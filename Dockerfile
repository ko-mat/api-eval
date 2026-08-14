FROM python:3.11-slim

WORKDIR /app

# パッケージインストールのためのシステム依存関係
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt のコピーと依存ライブラリのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードと静的ファイルのコピー
COPY . .

# コンテナが使用するポートを公開
EXPOSE 80

# アプリケーションの起動コマンド (Uvicorn)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
