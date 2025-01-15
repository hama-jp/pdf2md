
import os
from flask import Flask, render_template, request, send_file, session
import fitz
import pypdfium2 as pdfium
import tempfile
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "pdf2md"
UPLOAD_FOLDER.mkdir(exist_ok=True)
MARKDOWN_FILE = UPLOAD_FOLDER / "converted.md"

def pdf_to_markdown_with_pdfium(pdf_path):
    """pypdfium2を使用してPDFファイルをMarkdownに変換する"""
    pdf = pdfium.PdfDocument(pdf_path)
    markdown_content = []

    for page_number in range(len(pdf)):
        page = pdf.get_page(page_number)
        text_page = page.get_textpage()
        text = text_page.get_text_range()
        
        # テキストを行に分割して処理
        lines = text.split('\n')
        formatted_lines = []
        
        # 前の行の文字サイズを記録
        prev_size = None
        
        for line in lines:
            if not line.strip():
                continue
            
            # 行の文字サイズを取得（簡易的な実装）
            if len(line) > 50:  # 長い行は本文として扱う
                if prev_size and prev_size > 12:
                    formatted_lines.append(f"## {line}")
                else:
                    formatted_lines.append(line)
                prev_size = 10
            else:
                if prev_size and prev_size <= 12:
                    formatted_lines.append(line)
                else:
                    formatted_lines.append(f"### {line}")
                prev_size = 14
        
        markdown_content.extend(formatted_lines)
        markdown_content.extend(["", "---", ""])  # ページ区切り
    
    return '\n'.join(markdown_content)

def pdf_to_markdown_with_mupdf(pdf_path):
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
        
        # 変換方法の選択
        use_pdfium = request.form.get('conversion_type', 'mupdf') == 'pdfium'
        
        # Markdownに変換
        if use_pdfium:
            markdown_content = pdf_to_markdown_with_pdfium(temp_pdf)
        else:
            markdown_content = pdf_to_markdown_with_mupdf(temp_pdf)
        
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
