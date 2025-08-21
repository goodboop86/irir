# IRIR (Investor Relations Information Retrieval)

EDINET APIを活用した投資家向け情報開示システム

## 概要

IRIRは、金融庁のEDINET（Electronic Disclosure for Investors' NETwork）APIを使用して、上場企業の開示書類を効率的に取得・表示するWebアプリケーションです。Streamlitを使用したユーザーフレンドリーなインターフェースを提供します。

## 機能

- EDINET APIからの企業開示書類一覧取得
- 開示書類の詳細表示
- Streamlitベースの直感的なWebインターフェース


## 環境構築

### 前提条件

- Python 3.10以上
- uv（Python パッケージマネージャー）

### セットアップ手順

1. **uvのインストール**
   ```bash
   brew install uv
   ```

2. **Pythonバージョンの設定**
   ```bash
   uv python install 3.13
   uv python pin 3.13
   ```

3. **依存関係のインストール**
   ```bash
   # 本体依存関係
   uv add streamlit
   uv add fastapi --extra standard
   uv add tenacity # retry処理
   uv add aiohttp
   uv add aiofiles

   # aws
   uv add boto3
   
   # 開発用依存関係
   uv add --dev ruff
   ```

4. **環境変数の設定**
   
   `.env`ファイルを作成し、EDINET APIキーを設定してください：
   ```bash
   EDINET_API_KEY=your_api_key_here
   ```

## 使用方法

### アプリケーションの起動

```bash
# フロントエンドアプリケーションの起動
uv run streamlit run app/frontend/main.py

# バックエンド
uv run uvicorn backend.main.main:app --reload
```

### EDINET API の直接利用

#### 開示書類一覧の取得

```bash
curl 'https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2023-08-28&type=2&Subscription-Key=[your-api-key]' | jq '.results[].docID' | head
```

#### 特定書類のダウンロード

```bash
curl -o document.zip 'https://api.edinet-fsa.go.jp/api/v2/documents/S100RR60?type=1&Subscription-Key=[your-api-key]'
```

```
PYTHONPATH=./ uv run app/path/to/[filename].py
```

## 開発

### コード品質チェック

```bash
# Ruffによるリンティング・フォーマット
uv run ruff check
uv run ruff format
```

### プロジェクト構造の説明

- **app/frontend/**: Streamlitベースのユーザーインターフェース
- **app/backend/**: EDINET API連携とビジネスロジック
- **app/backend/model/**: データモデル定義

## EDINET API について

EDINET（Electronic Disclosure for Investors' NETwork）は、金融庁が提供する企業情報開示システムです。

- **公式ドキュメント**: [EDINET API仕様書（Version 2）](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WZEK0110.html)
- **API エンドポイント**: `https://api.edinet-fsa.go.jp/api/v2/`

### 主要なAPIエンドポイント

- `GET /documents.json`: 開示書類一覧取得
- `GET /documents/{docId}`: 特定書類の取得

## ライセンス

このプロジェクトのライセンスについては、プロジェクト管理者にお問い合わせください。

## 貢献

プロジェクトへの貢献を歓迎します。プルリクエストやイシューの報告をお待ちしています。

## 注意事項

- EDINET APIの利用には、事前の利用登録とAPIキーの取得が必要です
- APIの利用制限や利用規約については、EDINET公式サイトをご確認ください
- 本アプリケーションは開発中のため、機能や仕様が変更される可能性があります

## サポート

質問や問題がある場合は、GitHubのIssuesページでお知らせください。
