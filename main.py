import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime
import psycopg2 
from psycopg2.extras import DictCursor 

# Flaskアプリの初期化
app = Flask(__name__)

# 環境変数からLINE BOTのキーを取得
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))

# --- データベース接続とテーブル作成 ---
CONN = None 
DB_URL = os.environ.get('DATABASE_URL') 

def initialize_database():
    """データベース接続を試行し、テーブルが存在しなければ作成する"""
    global CONN
    if not DB_URL:
        print("致命的エラー: DATABASE_URLが環境変数に設定されていません。")
        return False

    try:
        CONN = psycopg2.connect(DB_URL)
        cursor = CONN.cursor()
        
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

initialize_database()

# データの記録関数 (変更なし)
def save_to_db(user_id, action_type):
    """データをデータベースに書き込む"""
    if CONN is None:
        print("データベース接続が確立されていないため、記録できません。")
        return False

    try:
        cursor = CONN.cursor()
        timestamp = datetime.now()
        
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

# データの削除関数 (変更なし)
def delete_latest_log(user_id):
    """特定のユーザーが記録した最新のログを削除する"""
    if CONN is None:
        print("データベース接続が確立されていないため、削除できません。")
        return False

    try:
        cursor = CONN.cursor()
        
        select_id_query = """
        SELECT id FROM pet_logs 
        WHERE user_id = %s 
        ORDER BY timestamp DESC 
        LIMIT 1;
        """
        cursor.execute(select_id_query, (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            cursor.close()
            return 0 

        log_id_to_delete = result[0]
        
        delete_query = """
        DELETE FROM pet_logs 
        WHERE id = %s;
        """
        cursor.execute(delete_query, (log_id_to_delete,))
        CONN.commit()
        cursor.close()
        print(f"DB記録削除成功: ID {log_id_to_delete} by {user_id}")
        return 1 
        
    except Exception as e:
        print(f"データベース削除エラーが発生しました: {e}")
        return -1 

# データの照会関数 (変更なし)
def get_latest_log():
    """最新のペットの世話記録をデータベースから取得する"""
    if CONN is None:
        return None

    try:
        cursor = CONN.cursor(cursor_factory=DictCursor)
        select_query = """
        SELECT timestamp, user_id, action_type 
        FROM pet_logs 
        ORDER BY timestamp DESC 
        LIMIT 1;
        """
        cursor.execute(select_query)
        latest_log = cursor.fetchone()
        cursor.close()
        
        if latest_log:
            return {
                'timestamp': latest_log['timestamp'].strftime('%Y/%m/%d %H時%M分'),
                'user_id': latest_log['user_id'],
                'action_type': latest_log['action_type']
            }
        return None
    except Exception as e:
        print(f"データベース照会エラーが発生しました: {e}")
        return None

# 【新規追加】アクションタイプを会話文に変換する辞書
ACTION_MAP = {
    '給餌': 'ごはん',
    '排泄': 'トイレ掃除'
}


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
    
    # ユーザー名取得ロジック
    user_name = "あなた"
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
    except Exception as e:
        print(f"ユーザー名の取得に失敗しました: {e}") 
        
    response_text = "よくわからないにゃ。\n「ごはん」「エサ」や「トイレ」「うんち」とかならわかるにゃ\n最新の記録を知りたいときは「最新」って聞いてにゃん！"
    record_success = False
    
    # --- 4. 記録削除キーワードのチェック (最優先) ---
    if "削除" in user_text or "消して" in user_text or "やり直し" in user_text or "間違えた" in user_text:
        delete_result = delete_latest_log(user_id)
        
        if delete_result == 1:
            response_text = f"{user_name}の最新の記録を削除したにゃん！"
        elif delete_result == 0:
            response_text = f"{user_name}の記録は見つからなかったにゃ。"
        else:
            response_text = "ごめん！削除に失敗したにゃ。Renderのログを確認してね。"
            
    # --- 3. ログ照会キーワードのチェック ---
    elif "誰が" in user_text or "だれが" in user_text or "お世話" in user_text or "最新" in user_text:
        latest_log = get_latest_log()
        
        if latest_log:
            try:
                profile = line_bot_api.get_profile(latest_log['user_id'])
                last_user_name = profile.display_name
            except Exception:
                last_user_name = latest_log['user_id'] 

            # 【修正点】アクションタイプを変換して表示
            action_display_name = ACTION_MAP.get(latest_log['action_type'], '不明なお世話')

            response_text = (
                f"最新のお世話は、{last_user_name} が\n"
                f"{action_display_name} を {latest_log['timestamp']} に\n"
                f"やってくれたにゃん！"
            )
        else:
            response_text = "まだ誰も記録してくれてないにゃ... 最初に「ごはん」か「トイレ」って送ってほしいにゃん。"

    elif "もらった？" in user_text or "もらえた？" in user_text or "食べた？" in user_text:
        latest_log = get_latest_log()
        
        if latest_log and latest_log['action_type'] == '給餌':
            try:
                profile = line_bot_api.get_profile(latest_log['user_id'])
                last_user_name = profile.display_name
            except Exception:
                last_user_name = latest_log['user_id'] 

            response_text = (
                f"最新のごはんは、{last_user_name} が\n"
                f"{latest_log['timestamp']} に\n"
                f"くれたにゃん！"
            )
        else:
            response_text = "まだ誰もごはんをくれてないにゃ... ご飯くれたら「ごはん」って送ってほしいにゃん。"

    elif "トイレした？" in user_text or "うんちした？" in user_text or "おしっこした？" in user_text:
        latest_log = get_latest_log()
        
        if latest_log and latest_log['action_type'] == '排泄':
            try:
                profile = line_bot_api.get_profile(latest_log['user_id'])
                last_user_name = profile.display_name
            except Exception:
                last_user_name = latest_log['user_id'] 

            response_text = (
                f"最新のトイレ掃除は、\n{last_user_name} が\n"
                f"{latest_log['timestamp']} に\n"
                f"やってくれたにゃん！" # トイレ掃除に固定
            )
        else:
            response_text = "まだ誰もトイレ掃除をしてくれてないにゃ... トイレ掃除してくれたら「トイレ」って送ってほしいにゃん。"
            
    # --- 1 & 2. ごはん/トイレキーワードのチェックと記録 ---
    elif "ごはん" in user_text or "ご飯" in user_text or "エサ" in user_text or "餌" in user_text:
        record_success = save_to_db(user_id, '給餌')
        if record_success:
            response_text = f"ごはんありがとう！{user_name} !\nメモしたにゃ～"
        else:
            response_text = "ごめん！記録に失敗したにゃ。RenderのログとDB接続を確認してね。"

    elif "トイレ" in user_text or "うんち" in user_text or "おしっこ" in user_text:
        record_success = save_to_db(user_id, '排泄')
        if record_success:
            response_text = f"トイレ掃除ありがとう！{user_name}\n メモしたにゃ。\n臭くてごめんにゃ～"
        else:
            response_text = "ごめん！記録に失敗したにゃ。RenderのログとDB接続を確認してね。" 
    
    #日常ワード
    elif "ママ" in user_text or "まま" in user_text or "お母さん" in user_text or "知子" in user_text:
        response_text = "ママ！\nいつもありがとうにゃん！\nでも抱っこは苦手にゃん～"
    elif "パパ" in user_text or "ぱぱ" in user_text or "お父さん" in user_text or "恭士" in user_text:
        response_text = "パパ！\nいつもありがとうにゃん！\nでも汗臭いのは嫌だニャン"
    elif "ゆり" in user_text or "ゆっちゃん" in user_text or "優里" in user_text or "お姉ちゃん" in user_text:
        response_text = "ゆり！\nいつもありがとうにゃん！\nでもあんまり嗅がないでほしいにゃん～"
    elif "みさき" in user_text or "みーちゃん" in user_text or "美咲" in user_text:
        response_text = "みさき！\nいつもありがとうにゃん！\nいっぱい毛を落としてごめんにゃ～"
    elif "まさと" in user_text or "まーくん" in user_text or "大翔" in user_text:
        response_text = "まさと！\nいつもありがとうにゃん！\nでも大声は怖いにゃん～"

    elif "にゃ" in user_text or "にゃー" in user_text:
        response_text = "にゃーん！"
    
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