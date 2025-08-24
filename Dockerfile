# ベースイメージ
FROM public.ecr.aws/lambda/python:3.13

# uv インストール
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/
ENV PATH="/root/.local/bin/:$PATH"

# ビルド時引数でサービス名を切り替え（必須）
ARG SERVICE

# SERVICE が未指定ならビルドを止める
RUN if [ -z "$SERVICE" ]; then echo "ERROR: SERVICE build-arg is required"; exit 1; fi

# 依存ファイルだけコピーして uv sync
WORKDIR /app
COPY app/${SERVICE}/pyproject.toml app/${SERVICE}/uv.lock ./
RUN uv sync --locked

# 共通コードコピー（common）
COPY app/common/ /app/common

# サービス本体コピー
COPY app/${SERVICE}/ /app/${SERVICE}/

# Python パス設定
ENV PYTHONPATH=./

# コンテナ起動時
CMD ["uv", "run", "${SERVICE}/main/main.py"]
