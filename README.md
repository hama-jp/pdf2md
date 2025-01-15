# PDF to Markdown Converter

PDFファイルをMarkdown形式に変換するWebアプリケーションです。

## 機能

- PDFファイルのアップロード
- PDFからテキストを抽出してMarkdown形式に変換
- 変換結果のプレビュー表示
- Markdownファイルのダウンロード

## 必要条件

- Python 3.8以上
- 依存パッケージ（requirements.txtに記載）

## セットアップ

1. リポジトリをクローン
```bash
git clone [repository-url]
cd pdf2md
```

2. 仮想環境を作成して有効化
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate     # Windows
```

3. 依存パッケージのインストール
```bash
uv pip install -r requirements.txt
```

## 使用方法

1. アプリケーションの起動
```bash
python app.py
```

2. ブラウザで http://localhost:5000 にアクセス

3. 「ファイルを選択」ボタンからPDFファイルを選択

4. 「Markdownに変換」ボタンをクリック

5. 変換結果を確認し、必要に応じてダウンロード

## 使用技術

- Flask: Webアプリケーションフレームワーク
- PyMuPDF: PDFファイルの処理
- HTML/CSS: フロントエンド

## 注意事項

- 一度に処理できるファイルサイズには制限があります
- 複雑なレイアウトのPDFファイルは正確に変換できない場合があります
- アップロードされたファイルは一時ファイルとして保存され、処理後に自動的に削除されます

## ライセンス

MITライセンス
