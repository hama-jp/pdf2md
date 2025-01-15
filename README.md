# PDF to Markdown Converter

PDFファイルをMarkdownテキストに変換するWebアプリケーションです。

## 機能

- PDFファイルのアップロード
- PDF内のテキストをMarkdown形式に変換
- 変換結果のプレビュー表示
- Markdownファイルのダウンロード

## 必要要件

- Python 3.8以上
- 必要なパッケージは`requirements.txt`に記載

## インストール方法

1. リポジトリをクローン
```bash
git clone [repository-url]
cd pdf2md
```

2. 仮想環境を作成し、アクティベート
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
```

3. 依存パッケージをインストール
```bash
uv pip install -r requirements.txt
```

## 使用方法

1. アプリケーションを起動
```bash
python app.py
```

2. ブラウザで http://localhost:5000 にアクセス

3. PDFファイルを選択してアップロード

4. 変換結果を確認し、必要に応じてMarkdownファイルをダウンロード

## 注意事項

- PDFファイルのみ対応しています
- テキスト抽出の精度はPDFファイルの品質に依存します
- 大きなPDFファイルの場合、変換に時間がかかる可能性があります

## ライセンス

[MIT License](https://opensource.org/licenses/MIT)
