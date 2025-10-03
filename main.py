import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime
import psycopg2 # PostgreSQLとの接続ライブラリ

# Flaskアプリの初期化
app = Flask(__name__)

# 環境変数からLINE BOTのキーを取得
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))

# --- データベース接続とテーブル作成 ---
CONN = None # データベース接続オブジェクト
DB_URL = os.environ.get('DATABASE_URL') # Renderが自動で生成したURL

def initialize_database():
    """データベース接続を試行し、テーブルが存在しなければ作成する"""
    global CONN
    if not DB_URL:
        print("致命的エラー: DATABASE_URLが環境変数に設定されていません。")
        return False

    try:
        # DBへの接続
        CONN = psycopg2.connect(DB_URL)
        cursor = CONN.cursor()
        
        # テーブルが存在しなければ作成するSQLコマンド
        # (BOTの将来的な展開を見据え、NULLを許可しない形で設計します)
        create_table_query = """
        CREATE TABLE IF NOT EXISTS pet_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            action_type VARCHAR(20) NOT NULL
        );
        """
        cursor.execute(create_table_query)
        CONN.commit()
        cursor.close()
        print("PostgreSQL接続成功 & テーブル作成完了。")
        return True
    except Exception as e:
        print(f"致命的エラー: データベース初期化に失敗しました: {e}")
        CONN = None
        return False

# BOT起動時にデータベース接続を試みる
initialize_database()


# データの記録関数
def save_to_db(user_id, action_type):
    """データをデータベースに書き込む"""
    if CONN is None:
        print("データベース接続が確立されていないため、記録できません。")
        return False

    try:
        cursor = CONN.cursor()
        timestamp = datetime.now() # データベースのタイムスタンプ形式に合わせる
        
        # データ挿入のSQLコマンド
        insert_query = """
        INSERT INTO pet_logs (timestamp, user_id, action_type)
        VALUES (%s, %s, %s);
        """
        cursor.execute(insert_query, (timestamp, user_id, action_type))
        CONN.commit()
        cursor.close()
        print(f"DB記録成功: {action_type} by {user_id}")
        return True
    except Exception as e:
        print(f"データベースへの書き込みエラーが発生しました: {e}")
        return False


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature.")
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.lower()
    user_id = event.source.user_id 
    response_text = "よくわからないにゃ。「ごはん」「エサ」や「トイレ」「うんち」とかならわかるにゃ"
    
    record_success = False

    # 1.ごはんキーワードのチェックと記録
    if "ごはん" in user_text or "ご飯" in user_text or "エサ" in user_text or "餌" in user_text:
        record_success = save_to_db(user_id, '給餌')
        if record_success:
            response_text = f"ごはんありがとう！({user_id} の行動として)メモしたにゃ"
        else:
            response_text = "ごめん！記録に失敗したにゃ。RenderのログとDB接続を確認してね。"

    # 2.トイレキーワードのチェックと記録
    elif "トイレ" in user_text or "うんち" in user_text or "おしっこ" in user_text:
        record_success = save_to_db(user_id, '排泄')
        if record_success:
            response_text = f"トイレ掃除ありがとう！({user_id} の行動として)メモしたにゃ"
        else:
            response_text = "ごめん！記録に失敗したにゃ。RenderのログとDB接続を確認してね。" 
    
    # 応答メッセージを送信
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text))
    except Exception as e:
        print(f"Failed to send reply message: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)