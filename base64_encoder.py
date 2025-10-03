import base64
import os

JSON_FILE_NAME = 'line-pet-logger-6c9753831d9d.json' 

def encode_key(filename):
    try:
        with open(filename, 'rb') as f:
            # ファイル全体をBase64文字列にエンコード
            encoded_bytes = base64.b64encode(f.read())
            encoded_str = encoded_bytes.decode('utf-8')
            
            print("--- 以下の文字列をコピーしてRenderに登録してください ---")
            print(encoded_str)
            print("\n--- これがGSPREAD_AUTH_BASE64の値です ---")

    except FileNotFoundError:
        print(f"\nエラー: ファイルが見つかりません。ファイル名: '{filename}' を確認してください。")

if __name__ == '__main__':
    encode_key(JSON_FILE_NAME)