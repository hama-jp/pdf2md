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
    """PyMuPDFを使用してPDFファイルを簡易的にMarkdownに変換する"""
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

def pdf_to_markdown_nougat(pdf_path):
    """nougat-ocrを使用してPDFファイルを高品質にMarkdownに変換する"""
    output_dir = UPLOAD_FOLDER / "nougat_output"
    output_dir.mkdir(exist_ok=True)
    
    try:
        # nougat-ocrを実行
        subprocess.run([
            "nougat",
            "--markdown",
            str(pdf_path),
            "-o", str(output_dir)
        ], check=True)
        
        # 出力ファイルを読み込む
        md_file = next(output_dir.glob("*.mmd"))
        markdown_content = md_file.read_text(encoding='utf-8')
        
        return markdown_content
    
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Nougat変換エラー: {str(e)}")
    finally:
        # 一時ファイルを削除
        if output_dir.exists():
            for file in output_dir.glob("*"):
                file.unlink()
            output_dir.rmdir()

@app.route('/')
def index():
    """トップページを表示"""
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
        
        # 変換方法の選択（デフォルトはnougat）
        use_nougat = request.form.get('conversion_type', 'nougat') == 'nougat'
        
        # Markdownに変換
        if use_nougat:
            try:
                markdown_content = pdf_to_markdown_nougat(temp_pdf)
            except Exception as e:
                # nougatが失敗した場合、簡易変換にフォールバック
                markdown_content = pdf_to_markdown_simple(temp_pdf)
        else:
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
    app.run(debug=True)
