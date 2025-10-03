import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from datetime import datetime
import gspread 

# ... (中略) ...

# --- Google Sheets認証と接続処理 ---
WORKSHEET = None
try:
    # 1. Renderに登録したJSON文字列（認証キー）を取得
    json_auth = os.environ.get('GSPREAD_AUTH_JSON') # <-- GSPREAD_AUTH_JSONに変更
    if not json_auth:
        raise ValueError("GSPREAD_AUTH_JSON environment variable not found.")
        
    # 2. JSON文字列をPythonの辞書に変換し、サービスアカウント認証
    # Base64デコード処理を削除しました。
    credentials_dict = json.loads(json_auth) 
    gc = gspread.service_account_from_dict(credentials_dict)
    
    # 3. Renderに登録したシートIDを取得
    sheet_id = os.environ.get('GOOGLE_SHEETS_ID')
    if not sheet_id:
        raise ValueError("GOOGLE_SHEETS_ID environment variable not found.")
    
    # 4. IDを使ってスプレッドシートを開き、最初のシート（インデックス0）を取得
    spreadsheet = gc.open_by_key(sheet_id) 
    WORKSHEET = spreadsheet.get_worksheet(0) 
    
    print("Google Sheets接続成功。")

except Exception as e:
    # 接続失敗時もBOTは起動し、失敗メッセージを返す
    print(f"致命的エラー: Google Sheets認証または接続に失敗しました: {e}")
    WORKSHEET = None 
    