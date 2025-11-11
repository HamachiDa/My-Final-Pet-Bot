# Pythonのベースイメージを指定 (軽量で安定したバージョン)
FROM python:3.11-slim

# 作業ディレクトリをコンテナ内に設定
WORKDIR /app

# 依存関係ファイル（requirements.txt）をコピー
COPY requirements.txt requirements.txt

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード（main.pyなど）をすべてコピー
COPY . .

#Shellスクリプトを廃止し、Gunicorn実行ファイルを直接指定
# Cloud Runの推奨する形式で、ポート8080を明示的にリッスンさせる
# gunicornの実行パスを明示することで、exit code 127エラーを回避します。
CMD ["/usr/local/bin/gunicorn", "main:app", "--bind", "0.0.0.0:8080", "--workers", "1"]