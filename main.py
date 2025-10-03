import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime
import gspread 

# Flaskアプリの初期化
app = Flask(__name__)

# 環境変数からLINE BOTのキーを取得
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))


# --- Google Sheets認証と接続処理 ---
WORKSHEET = None
try:
    # 1. JSON文字列（認証キー）を取得し、認証
    json_auth = os.environ.get('GSPREAD_AUTH_JSON')
    if not json_auth:
        raise ValueError("GSPREAD_AUTH_JSON environment variable not found.")
        
    credentials_dict = json.loads(json_auth)
    gc = gspread.service_account_from_dict(credentials_dict)
    
    # 2. Renderに登録したシートIDを取得
    sheet_id = os.environ.get('GOOGLE_SHEETS_ID') 
    if not sheet_id:
        raise ValueError("GOOGLE_SHEETS_ID environment variable not found.")
    
    # 3. IDを使ってスプレッドシートを開き、最初のシート（インデックス0）を取得
    spreadsheet = gc.open_by_key(sheet_id) 
    WORKSHEET = spreadsheet.get_worksheet(0) 
    
    print("Google Sheets接続成功。")

except Exception as e:
    # 接続失敗時もBOTは起動し、失敗メッセージを返す
    print(f"致命的エラー: Google Sheets認証または接続に失敗しました: {e}")
    WORKSHEET = None 

# データの記録関数 (最終修正)
def save_to_sheet(user_id, action_type):
    global WORKSHEET
    if WORKSHEET is None:
        print("シート接続が確立されていないため、記録できません。")
        return False

    try:
        # WORKSHEETが古くなっている可能性があるため、シートを再取得し直す
        # これにより、権限が「編集者」であっても書き込みエラーを防ぐ
        sheet_id = os.environ.get('GOOGLE_SHEETS_ID')
        gc = gspread.service_account_from_dict(json.loads(os.environ.get('GSPREAD_AUTH_JSON')))
        WORKSHEET = gc.open_by_key(sheet_id).get_worksheet(0)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')
        WORKSHEET.append_row([timestamp, user_id, action_type])
        return True
    except Exception as e:
        print(f"Google Sheetsへの書き込みエラーが発生しました: {e}")
        return False


# ... @app.route("/callback", methods=['POST']) と @handler.add(MessageEvent, message=TextMessage) の関数は省略 ...

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
        record_success = save_to_sheet(user_id, '給餌')
        if record_success:
            response_text = f"ごはんありがとう！({user_id} の行動として)メモしたにゃ"
        else:
            response_text = "ごめん！記録に失敗したにゃ。😭 シートの権限やIDを最終確認してね。" 

    # 2.トイレキーワードのチェックと記録
    elif "トイレ" in user_text or "うんち" in user_text or "おしっこ" in user_text:
        record_success = save_to_sheet(user_id, '排泄')
        if record_success:
            response_text = f"トイレ掃除ありがとう！({user_id} の行動として)メモしたにゃ"
        else:
            response_text = "ごめん！記録に失敗したにゃ。😭 シートの権限やIDを最終確認してね。" 
    
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