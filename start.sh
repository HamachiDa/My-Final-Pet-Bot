#!/bin/bash
# 起動ポートが完全に準備されるまで5秒間待機する
sleep 5
# Gunicornを起動し、全てのインターフェースとCloud Runが指定したポートを使用
exec gunicorn main:app --bind 0.0.0.0:"$PORT" --workers 1