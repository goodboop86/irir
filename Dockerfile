# ベースイメージはLambdaランタイムのPython 3.13
FROM public.ecr.aws/lambda/python:3.13

# uvのインストール
# ghcrからuvバイナリをコピーし、標準的な実行パスに配置
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /usr/local/bin/

# ビルド時引数でサービス名を切り替え
ARG SERVICE

# ARGの値をENVとして最終イメージに書き込む
ENV SERVICE=${SERVICE}

# SERVICEが未指定ならビルドを停止
RUN if [ -z "$SERVICE" ]; then echo "ERROR: SERVICE build-arg is required"; exit 1; fi

# 依存関係のインストールをキャッシュするために、依存ファイルのみを先にコピー
WORKDIR /app
COPY app/${SERVICE}/pyproject.toml app/${SERVICE}/uv.lock ./
RUN uv sync --locked

# 共通コードとサービス固有のコードをコピー
COPY app/common/ /app/common/
COPY app/${SERVICE}/ /app/${SERVICE}/

# Pythonパスの設定
# これにより、/appにあるモジュールを正しくインポートできる
ENV PYTHONPATH=./

# コンテナ起動時にLambdaハンドラ関数を直接指定
# これがLambdaランタイムが期待する形式
CMD ["${SERVICE}.main.main.lambda_handler"]