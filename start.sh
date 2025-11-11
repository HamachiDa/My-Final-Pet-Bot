#!/bin/bash
# Cloud Runが指定する環境変数$PORTを使ってGunicornを確実に起動する
exec gunicorn main:app --bind 0.0.0.0:$PORT --workers 1