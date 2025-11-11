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

# 最終的な起動コマンド: Cloud Runの仕様に完全に適合させる
# 環境変数 $PORT をホスト0.0.0.0と正確に結合させる
CMD gunicorn main:app --bind 0.0.0.0:$PORT --workers 1