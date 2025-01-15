import os
from flask import Flask, render_template, request, send_file, session
import fitz
import tempfile
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "pdf2md"
UPLOAD_FOLDER.mkdir(exist_ok=True)
MARKDOWN_FILE = UPLOAD_FOLDER / "converted.md"

def pdf_to_markdown(pdf_path):
    """PDFファイルをMarkdownに変換する"""
    doc = fitz.open(pdf_path)
    markdown_content = []
    
    for page in doc:
        text = page.get_text()
        # 改行を保持しながらテキストを抽出
        lines = text.split('\n')
        # 空行を除去し、Markdownフォーマットに変換
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line:
                formatted_lines.append(line)
        markdown_content.extend(formatted_lines)
        markdown_content.append('\n')  # ページ区切り
    
    doc.close()
    return '\n'.join(markdown_content)

@app.route('/')
def index():
    """トップページを表示"""
    return render_template('index.html')

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
        markdown_content = pdf_to_markdown(temp_pdf)
        
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
    app.run(debug=True)
