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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# --- CONFIGURATION ---
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_LINE_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_LINE_SECRET')
LARK_APP_ID = os.getenv('LARK_APP_ID', 'YOUR_LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET', 'YOUR_LARK_APP_SECRET')
LARK_BASE_TOKEN = os.getenv('LARK_BASE_TOKEN', 'YOUR_BASE_TOKEN')
TABLE_SALES = os.getenv('TABLE_SALES', 'tblSales')
TABLE_INVENTORY = os.getenv('TABLE_INVENTORY', 'tblInventory')

# --- INITIALIZATION ---
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = lark.Client.builder().app_id(LARK_APP_ID).app_secret(LARK_APP_SECRET).build()

# --- LARK SERVICE HELPER (Existing) ---
def add_sales_record(staff_name, amount, menu_item):
    print(f"Mock: Added sales record to Lark: {staff_name}, {amount}, {menu_item}")
    return True

def update_inventory(item_name, quantity_used):
    print(f"Mock: Decremented inventory for {item_name} by {quantity_used}")
    current_stock_mock = 2
    threshold_mock = 5
    if current_stock_mock < threshold_mock:
        return True, f"⚠️ 【在庫アラート】\n{item_name}の在庫が残り{current_stock_mock}個になりました。\n発注してください。"
    return False, None

# --- RESERVATION FLOW ---

def show_menu_selection(reply_token):
    """予約メニューを表示する"""
    buttons_template = ButtonsTemplate(
        title='メニュー選択',
        text='予約するメニューを選んでください',
        actions=[
            PostbackAction(label='カット (39分)', data='action=select_menu&menu=cut&slots=1'),
            PostbackAction(label='カラー (78分)', data='action=select_menu&menu=color&slots=2'),
            PostbackAction(label='パーマ (117分)', data='action=select_menu&menu=perm&slots=3'),
        ]
    )
    line_bot_api.reply_message(reply_token, TemplateSendMessage(alt_text='メニュー選択', template=buttons_template))

def show_available_times(reply_token, menu, slots_count):
    """空き時間を計算して表示する"""
    # 1. Get existing events from Lark
    today = datetime.now()
    existing_events = lark_calendar.get_calendar_events(today, datetime(today.year, today.month, today.day, 23, 59))
    
    # 2. Calculate available slots using the engine
    available = scheduler.check_availability(slots_count, today.date(), existing_events)
    
    if not available:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="申し訳ありません。本日は空きがありません。"))
        return

    # 3. Create buttons for times (Show top 3 for demo)
    actions = []
    for slot in available[:3]: 
        time_label = slot['label']
        # data format example: action=confirm&menu=cut&start=10:00&end=10:39
        data = f"action=confirm&menu={menu}&start={slot['start_time'].strftime('%H:%M')}&end={slot['end_time'].strftime('%H:%M')}"
        actions.append(PostbackAction(label=time_label, data=data))
        
    buttons_template = ButtonsTemplate(
        title='日時選択',
        text=f'{menu}の空き時間が見つかりました',
        actions=actions
    )
    line_bot_api.reply_message(reply_token, TemplateSendMessage(alt_text='日時選択', template=buttons_template))

def confirm_reservation(reply_token, menu, start_str, end_str):
    """予約を確定し、カレンダーに登録する"""
    today = datetime.now().date()
    start_time = datetime.strptime(start_str, "%H:%M").time()
    end_time = datetime.strptime(end_str, "%H:%M").time()
    
    start_dt = datetime.combine(today, start_time)
    end_dt = datetime.combine(today, end_time)
    
    # Register to Lark Calendar
    summary = f"予約: {menu}"
    lark_calendar.create_calendar_event(summary, start_dt, end_dt, description="LINE予約自動連携")
    
    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"✅ 予約が確定しました！\n\nメニュー: {menu}\n時間: {start_str} 〜 {end_str}\n\nご来店をお待ちしております。"))


# --- LINE EVENT HANDLERS ---

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    
    if text == "予約":
        show_menu_selection(event.reply_token)
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
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="メニュー:\n・「予約」\n・「売上 [金額]」\n・「使用 [商品]」"))

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
