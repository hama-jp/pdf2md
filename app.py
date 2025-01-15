
import os
import subprocess
from flask import Flask, render_template, request, send_file, session
import fitz
import tempfile
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "pdf2md"
UPLOAD_FOLDER.mkdir(exist_ok=True)
MARKDOWN_FILE = UPLOAD_FOLDER / "converted.md"

def pdf_to_markdown_simple(pdf_path):
    """PyMuPDFを使用してPDFファイルをMarkdownに変換する"""
    doc = fitz.open(pdf_path)
    markdown_content = []
    current_font_size = 0
    
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                        
                    size = span["size"]
                    flags = span["flags"]
                    
                    # ヘッダーの検出
                    if size > current_font_size:
                        level = min(3, max(1, int(6 - (size / 4))))
                        text = f"{'#' * level} {text}"
                        current_font_size = size
                    
                    # 太字の検出
                    if flags & 2**4:  # bold text
                        text = f"**{text}**"
                    
                    # イタリックの検出
                    if flags & 2**1:  # italic text
                        text = f"*{text}*"
                    
                    markdown_content.append(text)
            
            # ブロック間に空行を追加
            markdown_content.append("")
        
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

@app.route('/upload', methods=['POST'])
def upload_file():
    """PDFファイルをアップロードして変換"""
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
        
        # Markdownに変換
        markdown_content = pdf_to_markdown_simple(temp_pdf)
        
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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
