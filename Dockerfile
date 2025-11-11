# Pythonのベースイメージを指定 (軽量で安定したバージョン)
FROM python:3.11-slim

# 作業ディレクトリをコンテナ内に設定
WORKDIR /app

# 依存関係ファイル（requirements.txt）をコピー
# NOTE: requirements.txtファイルがmain.pyと同じディレクトリにあることを確認してください。
COPY requirements.txt requirements.txt

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード（main.pyなど）をすべてコピー
COPY . .

# アプリケーションの実行コマンドを設定
# Cloud Runは環境変数 $PORT を使用するため、それに対応する
# Webサーバー（gunicorn）でmain.pyを実行します。
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 main:app