# Pythonのベースイメージを指定 (軽量で安定したバージョン)
FROM python:3.11-slim

# 作業ディレクトリをコンテナ内に設定
WORKDIR /app

# 依存関係ファイル（requirements.txt）をコピー
# 🚨 注意: requirements.txtからpsycopg2とpsycopg2-extrasを削除していることを確認
COPY requirements.txt requirements.txt

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード（main.pyなど）をすべてコピー
COPY . .

# Shellスクリプトを廃止し、Gunicorn実行ファイルを直接指定
CMD ["/usr/local/bin/gunicorn", "main:app", "--bind", "0.0.0.0:8080", "--workers", "1"]