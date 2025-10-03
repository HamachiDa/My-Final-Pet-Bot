import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime
import gspread # Google Sheets連携ライブラリをインポート

# Flaskアプリの初期化
app = Flask(__name__)

# 環境変数からLINE BOTのキーを取得
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))


# --- Google Sheets認証と接続処理 ---
WORKSHEET = None
try:
    # 1. Renderに登録したJSON文字列（認証キー）を取得
    json_auth = os.environ.get('GSPREAD_AUTH_JSON')
    if not json_auth:
        raise ValueError("GSPREAD_AUTH_JSON environment variable not found.")
        
    # 2. JSON文字列をPythonの辞書に変換
    credentials_dict = json.loads(json_auth)
    
    # 3. サービスアカウント認証
    gc = gspread.service_account_from_dict(credentials_dict)
    
    # 4. Renderに登録したシートURLを取得
    sheet_url = os.environ.get('GOOGLE_SHEETS_URL')
    if not sheet_url:
        raise ValueError("GOOGLE_SHEETS_URL environment variable not found.")
    
    # 5. スプレッドシートを開き、最初のシート（sheet1）を取得
    WORKSHEET = gc.open_by_url(sheet_url).sheet1
    print("Google Sheets接続成功。")

except Exception as e:
    # 認証や接続が失敗した場合、BOTは起動するが、Sheetsへの記録は行わない
    print(f"致命的エラー: Google Sheets認証または接続に失敗しました: {e}")
    WORKSHEET = None 

# データの記録関数
def save_to_sheet(user_id, action_type):
    if WORKSHEET is None:
        print("シート接続が確立されていないため、記録できません。")
        return False

    try:
        # タイムスタンプを日本時間（JST）に合わせて取得
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')
        # シートの末尾に新しい行を追加
        WORKSHEET.append_row([timestamp, user_id, action_type])
        return True
    except Exception as e:
        print(f"Google Sheetsへの書き込みエラーが発生しました: {e}")
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
        record_success = save_to_sheet(user_id, '給餌')
        if record_success:
            response_text = f"ごはんありがとう！({user_id} の行動として)メモしたにゃ"
        else:
            response_text = "ごめん！ごはんは認識できたけど、メモに失敗したにゃ。Renderのログを確認してね。"

    # 2.トイレキーワードのチェックと記録
    elif "トイレ" in user_text or "うんち" in user_text or "おしっこ" in user_text:
        record_success = save_to_sheet(user_id, '排泄')
        if record_success:
            response_text = f"トイレ掃除ありがとう！({user_id} の行動として)メモしたにゃ"
        else:
            response_text = "ごめん！トイレ掃除は認識できたけど、メモに失敗したにゃ。Renderのログを確認してね。"
    
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