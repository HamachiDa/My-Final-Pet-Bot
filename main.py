import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime

# Flaskアプリの初期化
app = Flask(__name__)

# 環境変数からキーを取得し、LineBotApiとWebhookHandlerを設定
# Renderに設定されたCHANNEL_ACCESS_TOKENとCHANNEL_SECRETが使用されます。
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    # LINEからのリクエストの署名を確認
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        # Webhookハンドラに処理を渡す
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 署名が無効な場合は400エラーを返す
        print("Invalid signature. Please check your channel access token/secret.")
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 受け取ったメッセージを小文字でチェック
    user_text = event.message.text.lower()
    user_id = event.source.user_id # 誰が送ったか

    # デフォルトの応答メッセージを設定
    response_text = "よくわからないにゃ。「ごはん」「エサ」や「トイレ」「うんち」とかならわかるにゃ"
    
    # 1.ごはんキーワードのチェック
    if "ごはん" in user_text or "ご飯" in user_text or "エサ" in user_text or "餌" in user_text:
        # TODO: Google Sheetsにメモする処理を追加
        # save_to_database(user_id, '給餌', datetime.now()) # datetime.now()をdatetimeモジュールから取得に変更
        response_text = f"{user_id}、ごはんありがとう！メモしたにゃ"

    # 2.トイレキーワードのチェック
    elif "トイレ" in user_text or "うんち" in user_text or "おしっこ" in user_text:
        # TODO: Google Sheetsにメモする処理を追加
        # save_to_database(user_id, '排泄', datetime.now())
        response_text = f"{user_id}、トイレ掃除ありがとう！メモしたにゃ"
    
    # === 応答メッセージを送信する処理を、全ての条件分岐の「外」に移動 ===
    # 上記の処理で response_text に適切なメッセージが格納されます。
    
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text))
    except Exception as e:
        # 応答送信中にエラーが発生した場合、ログに出力
        print(f"Failed to send reply message: {e}")

if __name__ == "__main__":
    # 環境変数からポートを取得し、アプリケーションを起動
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
