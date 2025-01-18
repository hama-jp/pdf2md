# PDF to Markdown Converter

PDF文書をMarkdownに変換するWebアプリケーションです。数式や表、画像を含むPDFファイルにも対応しています。

## 特徴

- OCRを使用した高品質な変換（Nougat）
- 軽量で高速な変換オプション（PyMuPDF）
- ドラッグ＆ドロップでのファイルアップロード
- リアルタイムの変換進捗表示
- ダークモード対応
- 数式の自動検出とTeX形式での出力

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/pdf2md.git
cd pdf2md

# 仮想環境を作成して有効化
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate  # Windows

# 依存パッケージをインストール
pip install -r requirements.txt
```

## 使用方法

1. サーバーを起動
```bash
python app.py
```

2. ブラウザで http://localhost:5002 にアクセス

3. 以下のいずれかの方法でPDFファイルを選択
   - 「ファイルを選択」ボタンをクリック
   - PDFファイルをドラッグ＆ドロップ

4. 変換方法を選択
   - Nougat OCR: 高品質な変換（数式対応）
   - PyMuPDF: 軽量・高速な変換

5. 「Markdownに変換」ボタンをクリック

6. 変換完了後、プレビューを確認してダウンロード

## 依存パッケージ

- Flask: Webフレームワーク
- Nougat OCR: 高品質PDF変換
- PyMuPDF: PDF解析とテキスト抽出
- Flask-SocketIO: リアルタイム進捗表示

## ライセンス

MIT License
