import os
import json
import logging
from flask import Flask, request, abort
from datetime import datetime
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, PostbackEvent,
    TemplateSendMessage, ButtonsTemplate, PostbackAction
)
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *


# Custom Modules
import scheduler
import lark_calendar
import google_sheets  # Added

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_LINE_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_LINE_SECRET')
# LARK関連は一旦そのまま

# --- INITIALIZATION ---
# ... (省略)

# (中略)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    
    if text == "予約":
        show_menu_selection(event.reply_token)
    elif text in ["キャンセル", "予約キャンセル"]:
        # Googleスプレッドシートからキャンセル処理
        success = google_sheets.cancel_reservation(user_id)
        if success:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🗑️ 予約をキャンセルしました。\nまたのご利用をお待ちしております。"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ℹ️ キャンセル可能な予約が見つかりませんでした。\n（既にキャンセル済みか、未来の予約がない可能性があります）"))
            
    elif text.startswith("売上"):
        # Existing Sales Logic
        try:
            parts = text.split()
            amount = parts[1]
            menu = parts[2] if len(parts) > 2 else "その他"
            add_sales_record(event.source.user_id, amount, menu)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 売上登録完了\n金額: ¥{amount}\nメニュー: {menu}"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ フォーマットエラー"))
    elif text.startswith("使用"):
        # Existing Inventory Logic
        try:
            parts = text.split()
            item_name = parts[1]
            qty = int(parts[2]) if len(parts) > 2 else 1
            is_low, alert = update_inventory(item_name, qty)
            msgs = [TextSendMessage(text=f"✅ 在庫更新完了: {item_name} -{qty}")]
            if is_low: msgs.append(TextSendMessage(text=alert))
            line_bot_api.reply_message(event.reply_token, msgs)
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ フォーマットエラー"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="メニュー:\n・「予約」\n・「キャンセル」\n・「売上 [金額]」\n・「使用 [商品]」"))


@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    params = dict(x.split('=') for x in data.split('&'))
    action = params.get('action')
    
    if action == 'select_menu':
        menu = params.get('menu')
        slots = int(params.get('slots'))
        show_available_times(event.reply_token, menu, slots)
        
    elif action == 'confirm':
        menu = params.get('menu')
        start = params.get('start')
        end = params.get('end')
        confirm_reservation(event.reply_token, menu, start, end)

if __name__ == "__main__":
    app.run(port=8000)
