import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境変数からキーを取得
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 受け取ったメッセージをそのまま返す(削除)
   # line_bot_api.reply_message(
    #    event.reply_token,
    #    TextSendMessage(text=event.message.text))

    # 受け取ったメッセージを小文字でチェック
    user_text = event.message.text.lower()
    user_id = event.source.user_id # 誰が送ったか

    # 1.ごはん
    if "ごはん" in user_text or "ご飯" in user_text or "エサ" in user_text or "餌" in user_text:
        # TODO: Google Sheetsにメモする処理を追加
        # save_to_database(user_id, '給餌', datatime.now())

        response_text = f"{user_id}、ごはんありがとう！メモしたにゃ"

    elif "トイレ" in user_text or "うんち" in user_text or "おしっこ" in user_text:
        # TODO: Google Sheetsにメモする処理を追加
        # save_to_database(user_id, '排泄', datatime.now())
        response_text = f"{user_id}、トイレ掃除ありがとう！メモしたにゃ"
    
    else:
        reply_message = "よくわからないにゃ。「ごはん」「エサ」や「トイレ」「うんち」とかならわかるにゃ"

        # 返信メッセージを送信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)