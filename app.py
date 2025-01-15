import os
import tempfile
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    session,
    url_for,
    redirect,
)
import fitz

app = Flask(__name__)
app.secret_key = os.urandom(24)

def pdf_to_markdown(pdf_path):
    """PDFファイルをMarkdownテキストに変換する"""
    try:
        doc = fitz.open(pdf_path)
        markdown_content = []
        
        for page in doc:
            text = page.get_text()
            # 基本的なテキスト処理
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    # ヘッダーっぽい行の処理
                    if len(line) < 100 and line.isupper():
                        markdown_content.append(f"## {line}\n")
                    else:
                        markdown_content.append(f"{line}\n")
            
            markdown_content.append("\n---\n")  # ページ区切り
        
        doc.close()
        return ''.join(markdown_content)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return render_template('index.html', error='ファイルが選択されていません')
    
    file = request.files['pdf_file']
    if file.filename == '':
        return render_template('index.html', error='ファイルが選択されていません')
    
    if not file.filename.lower().endswith('.pdf'):
        return render_template('index.html', error='PDFファイルのみ対応しています')
    
    try:
        # 一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            markdown_content = pdf_to_markdown(temp_file.name)
            
            # 変換結果をセッションに保存
            session['markdown_content'] = markdown_content
            
        # 一時ファイルを削除
        os.unlink(temp_file.name)
        
        return render_template('index.html', markdown_content=markdown_content)
    except Exception as e:
        return render_template('index.html', error=f'変換中にエラーが発生しました: {str(e)}')

@app.route('/download')
def download_markdown():
    markdown_content = session.get('markdown_content')
    if not markdown_content:
        return redirect(url_for('index'))
    
    # 一時ファイルとしてMarkdownを保存
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as temp_file:
        temp_file.write(markdown_content)
    
    try:
        return_data = send_file(
            temp_file.name,
            mimetype='text/markdown',
            as_attachment=True,
            download_name='converted.md'
        )
        
        # ファイル送信後に一時ファイルを削除
        os.unlink(temp_file.name)
        return return_data
    except Exception as e:
        os.unlink(temp_file.name)
        return render_template('index.html', error=f'ダウンロード中にエラーが発生しました: {str(e)}')

if __name__ == '__main__':
    app.run(debug=True)
