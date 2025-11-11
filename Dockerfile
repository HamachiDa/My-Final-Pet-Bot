FROM python:3.11-slim

# 作業ディレクトリをコンテナ内に設定
WORKDIR /app

# 依存関係ファイル（requirements.txt）をコピー
COPY requirements.txt requirements.txt

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード（main.py, start.shなど）をすべてコピー
COPY . .

# 🚨 最終修正: start.shに実行権限を付与
RUN chmod +x ./start.sh

# 起動コマンドとしてシェルスクリプトを指定
CMD ["./start.sh"]