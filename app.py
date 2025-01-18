
import os
import asyncio
from flask import Flask, render_template, request, send_file, session, jsonify
from flask_socketio import SocketIO, emit
import fitz
import tempfile
from pathlib import Path
from nougat import NougatModel
from nougat.utils.checkpoint import get_checkpoint
from nougat.postprocessing import markdown_compatible
import torch

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app)
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "pdf2md"
UPLOAD_FOLDER.mkdir(exist_ok=True)
MARKDOWN_FILE = UPLOAD_FOLDER / "converted.md"

# Nougatモデルをグローバルに初期化
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
nougat_model = None

def get_nougat_model():
    """Nougatモデルを取得（初回呼び出し時に初期化）"""
    global nougat_model
    if nougat_model is None:
        checkpoint = get_checkpoint()
        nougat_model = NougatModel.from_pretrained(checkpoint).to(device)
        nougat_model.eval()
    return nougat_model

async def pdf_to_markdown_with_nougat(pdf_path, sid=None):
    """Nougat-OCRを使用してPDFファイルを高品質にMarkdownに変換する"""
    model = get_nougat_model()
    predictions = []
    
    try:
        # PDFページ数を取得
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        doc.close()

        # 進捗状況の初期化
        if sid:
            socketio.emit('progress', {'progress': 0, 'status': '変換を開始しています...'}, room=sid)

        predictions = []
        async for page_idx, prediction in aenumerate(model.convert(pdf_path)):
            predictions.append(prediction)
            if sid:
                progress = int((page_idx + 1) / total_pages * 100)
                socketio.emit('progress', {
                    'progress': progress,
                    'status': f'ページを処理中... ({page_idx + 1}/{total_pages})'
                }, room=sid)
        markdown = []
        for page, pred in enumerate(predictions):
            # マークダウン互換の後処理を適用
            processed = markdown_compatible(pred)
            markdown.append(processed)
            markdown.append("\n---\n")  # ページ区切り
        
        return '\n'.join(markdown)
    except Exception as e:
        raise RuntimeError(f"Nougat変換エラー: {str(e)}")

import re

def is_likely_math(text):
    """テキストが数式である可能性を判定"""
    math_indicators = [
        r'\+', r'-', r'\*', r'/', r'=', r'\^',  # 基本的な演算子
        r'\\sum', r'\\int', r'\\frac', r'\\sqrt',    # 一般的な数学記号
        r'[a-z]\([x-z]\)',                       # 関数表記
        r'[α-ωΑ-Ω]',                            # ギリシャ文字
        r'\d+[²³]',                              # 上付き数字
        r'[xy]\d+',                              # 変数と数字の組み合わせ
    ]
    pattern = '|'.join([re.escape(p) if '\\' in p else p for p in math_indicators])
    return (
        bool(re.search(pattern, text)) or
        (text.count('(') > 0 and text.count(')') > 0) or  # 括弧の存在
        (len(text) < 30 and sum(c.isdigit() for c in text) > len(text) * 0.3)  # 短い文で数字が多い
    )

def pdf_to_markdown_with_mupdf(pdf_path, sid=None):
    """PyMuPDFを使用してPDFファイルをMarkdownに変換する（数式対応）"""
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count
    markdown_content = []
    current_font_size = 0
    in_math_block = False
    math_content = []
    
    if sid:
        socketio.emit('progress', {'progress': 0, 'status': '変換を開始しています...'}, room=sid)

    for page_idx, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        if sid:
            progress = int((page_idx + 1) / total_pages * 100)
            socketio.emit('progress', {
                'progress': progress,
                'status': f'ページを処理中... ({page_idx + 1}/{total_pages})'
            }, room=sid)
        for block in blocks:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                line_text = ""
                math_detected = False
                
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    
                    size = span["size"]
                    flags = span["flags"]
                    font = span["font"].lower()
                    
                    # 数式の検出
                    if (is_likely_math(text) or 
                        "math" in font or 
                        "symbol" in font or 
                        any(c in text for c in "∑∫∏√∆∇")):
                        
                        if not in_math_block:
                            if line_text:
                                markdown_content.append(line_text)
                                line_text = ""
                            markdown_content.append("\n$$")
                            in_math_block = True
                        math_content.append(text)
                        math_detected = True
                        continue
                    
                    if in_math_block and not math_detected:
                        markdown_content.append(' '.join(math_content))
                        markdown_content.append("$$\n")
                        in_math_block = False
                        math_content = []
                    
                    # 通常のテキスト処理
                    if size > current_font_size:
                        level = min(3, max(1, int(6 - (size / 4))))
                        if line_text:
                            markdown_content.append(line_text)
                            line_text = ""
                        line_text = f"{'#' * level} {text}"
                        current_font_size = size
                    else:
                        if flags & 2**4:  # bold text
                            text = f"**{text}**"
                        if flags & 2**1:  # italic text
                            text = f"*{text}*"
                        line_text += " " + text if line_text else text
                
                if line_text:
                    markdown_content.append(line_text)
            
            # ブロック間に空行を追加
            if not in_math_block:
                markdown_content.append("")
        
        # 数式ブロックを閉じる
        if in_math_block:
            markdown_content.append(' '.join(math_content))
            markdown_content.append("$$\n")
            in_math_block = False
            math_content = []
        
        # ページ区切り
        markdown_content.extend(["---", ""])
    
    doc.close()
    return '\n'.join(markdown_content)


@app.route('/')
def index():
    """トップページを表示"""
    if MARKDOWN_FILE.exists():
        MARKDOWN_FILE.unlink()
    return render_template('index.html', error=None, markdown_content=None)

@socketio.on('connect')
def handle_connect():
    """WebSocket接続時のハンドラ"""
    pass

@app.route('/upload', methods=['POST'])
def upload_file():
    """PDFファイルをアップロードして変換"""
    sid = request.cookies.get('socketio_sid')
    if 'pdf_file' not in request.files:
        return render_template('index.html', error='ファイルが選択されていません')
    
    file = request.files['pdf_file']
    if file.filename == '':
        return render_template('index.html', error='ファイルが選択されていません')
    
    if not file.filename.lower().endswith('.pdf'):
        return render_template('index.html', error='PDFファイルのみアップロード可能です')
    
    try:
        # 一時ファイルとして保存
        temp_pdf = UPLOAD_FOLDER / "temp.pdf"
        file.save(temp_pdf)
        
        # 変換方法の選択
        use_nougat = request.form.get('conversion_type', 'nougat') == 'nougat'
        
        # Markdownに変換
        if use_nougat:
            try:
                # 非同期関数を同期的に実行
                markdown_content = asyncio.run(pdf_to_markdown_with_nougat(temp_pdf, sid))
            except Exception as e:
                if sid:
                    socketio.emit('progress', {
                        'progress': 0,
                        'status': 'Nougatでの変換に失敗しました。PyMuPDFで再試行中...'
                    }, room=sid)
                # Nougatが失敗した場合、PyMuPDFにフォールバック
                markdown_content = pdf_to_markdown_with_mupdf(temp_pdf, sid)
        else:
            markdown_content = pdf_to_markdown_with_mupdf(temp_pdf, sid)

        if sid:
            socketio.emit('progress', {
                'progress': 100,
                'status': '変換が完了しました'
            }, room=sid)
        
        # 一時ファイルとしてMarkdownを保存
        MARKDOWN_FILE.write_text(markdown_content, encoding='utf-8')
        
        # 結果を表示
        return render_template('index.html', markdown_content=markdown_content)
    
    except Exception as e:
        return render_template('index.html', error=f'変換エラー: {str(e)}')
    
    finally:
        # 一時ファイルを削除
        if temp_pdf.exists():
            temp_pdf.unlink()

@app.route('/download')
def download_markdown():
    """変換したMarkdownファイルをダウンロード"""
    if not MARKDOWN_FILE.exists():
        return render_template('index.html', error='変換結果が見つかりません')
    
    try:
        return send_file(
            MARKDOWN_FILE,
            as_attachment=True,
            download_name='converted.md',
            mimetype='text/markdown'
        )
    
    except Exception as e:
        return render_template('index.html', error=f'ダウンロードエラー: {str(e)}')

async def aenumerate(ait):
    """非同期イテレータにenumerateを適用するヘルパー関数"""
    i = 0
    async for x in ait:
        yield i, x
        i += 1

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5002)
