from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
import os
import sys
from datetime import datetime, timedelta, time
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ローカルモジュールのインポート設定
# このファイルが src/bot.py にあると仮定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import scheduler
import lark_calendar
import lark_crm
import google_sheets # 追加

import messages

# 簡易的なセッション管理（メモリ上）
# { user_id: { "menu": "カット", "slots": 2 } }
user_sessions = {}

app = Flask(__name__)

# 環境変数の取得
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print("Error: LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_SECRET is not set.")
    sys.exit(1)

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text
    user_id = event.source.user_id
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # 1. 「予約」とだけ打たれた場合 → メニュー選択へ
        if text == "予約":
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[messages.get_menu_flex_message()]
                )
            )

        # 2. メニューが選択された場合
        elif text.startswith("メニュー:"):
            # メニュー名を取得
            menu_name = text.split(":")[1].strip()
            
            # 所要時間（スロット数）の判定
            # 1スロット = 30分
            required_slots = 2 # デフォルト: カット (60分)
            if "カラー" in menu_name:
                required_slots = 3 # 90分
            elif "ヘッドスパ" in menu_name:
                required_slots = 1 # 30分
            
            # セッションに保存
            user_sessions[user_id] = {
                "menu": menu_name,
                "slots": required_slots
            }
            
            # 空き状況を検索
            target_date = datetime.now().date() + timedelta(days=1)
            start_search = datetime.combine(target_date, scheduler.OPEN_TIME)
            end_search = datetime.combine(target_date, scheduler.CLOSE_TIME)
            
            reply_msg = ""
            try:
                existing_events = lark_calendar.get_calendar_events(start_search, end_search)
                available = scheduler.check_availability(required_slots, target_date, existing_events)
                
                if not available:
                    reply_msg = f"{target_date.strftime('%Y/%m/%d')} は満席です😭\n別の日程またはメニューをお試しください。"
                else:
                    slots_str = "\n".join([f"・{s['label'].split('(')[0]}" for s in available[:8]])
                    reply_msg = f"【選択: {menu_name}】\n📅 {target_date.strftime('%m/%d')} の空き状況:\n{slots_str}\n\n※予約したい時間を「10:00」のように入力して送信してください。"
            except Exception as e:
                reply_msg = f"エラーが発生しました: {str(e)}"

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_msg)]
                )
            )

        # 3. 時間が入力された場合（予約実行）
        elif ":" in text and len(text) <= 5:
            try:
                target_time_str = text.strip()
                target_hour, target_minute = map(int, target_time_str.split(":"))
                
                # セッションから情報を取得（なければデフォルト）
                session = user_sessions.get(user_id, {"menu": "カット", "slots": 2})
                menu_name = session["menu"]
                required_slots = session["slots"]
                
                # 時間計算
                target_date = datetime.now().date() + timedelta(days=1)
                start_dt = datetime.combine(target_date, time(target_hour, target_minute))
                # スロット数から終了時間を計算
                duration_minutes = required_slots * scheduler.SLOT_UNIT_MINUTES
                end_dt = start_dt + timedelta(minutes=duration_minutes)
                
                summary = f"【LINE予約】{menu_name} - {user_id[:5]}...様"
                description = f"LINEからの自動予約\nメニュー: {menu_name}\n希望時間: {target_time_str}"
                
                # Larkに登録
                if lark_calendar.create_calendar_event(summary, start_dt, end_dt, description):
                    
                    # 1. お客様（予約者）への返信
                    reply_msg = f"✅ 予約を確定しました！\n\n📝 メニュー: {menu_name}\n🕘 日時: {start_dt.strftime('%m/%d %H:%M')} - {end_dt.strftime('%H:%M')}\nご来店をお待ちしております。"
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=reply_msg)]
                        )
                    )

                    # 2. オーナー（管理者）への通知
                    # 今回はデモとして「予約した本人」に管理者通知も送ります。
                    # 本番ではオーナーのUser ID (os.getenv('OWNER_LINE_ID')) を指定します。
                    admin_msg = (
                        f"🔔 【管理者通知】新しい予約が入りました！\n\n"
                        f"👤 顧客ID: {user_id[:8]}...\n"
                        f"📝 メニュー: {menu_name}\n"
                        f"📅 日時: {start_dt.strftime('%Y/%m/%d %H:%M')}"
                    )
                    try:
                        line_bot_api.push_message(
                            PushMessageRequest(
                                to=user_id, # ここをオーナーIDに変えればOK
                                messages=[TextMessage(text=admin_msg)]
                            )
                        )
                    except Exception as e:
                        print(f"Failed to send admin notification: {e}")

                    # 3. Lark Base CRM保存 (失敗しても止まらないようにtryで囲むのが安全)
                    try:
                        res_date_str = start_dt.strftime('%Y-%m-%d')
                        res_time_str = start_dt.strftime('%H:%M')
                        # Lark CRM
                        # lark_crm.add_reservation_record(user_id, res_date_str, res_time_str, menu=menu_name)

                        # Google Sheets (Optional)
                        google_sheets.add_reservation_to_sheet(user_id, res_date_str, res_time_str, menu_name)
                    except Exception as e:
                        print(f"CRM/Sheets save failed: {e}")

                else:
                    reply_msg = "申し訳ありません。予約の登録に失敗しました。もう一度お試しいただくか、店舗へ直接ご連絡ください。"
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=reply_msg)]
                        )
                    )
                    
            except ValueError:
                 reply_msg = "時間の形式が正しくありません。「10:00」のように入力してください。"
                 line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_msg)]
                    )
                )
            except Exception as e:
                reply_msg = f"エラーが発生しました: {str(e)}"
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_msg)]
                    )
                )


        elif text in ["キャンセル", "予約キャンセル"]:
            # Google Sheetsからキャンセル
            canceled_info = google_sheets.cancel_reservation(user_id)
            
            if canceled_info:
                # ユーザー要望: キャンセル内容をわかりやすく返す
                reply_msg = (
                    f"✅ 以下の予約をキャンセルしました。\n\n"
                    f"📅 {canceled_info['date']} {canceled_info['time']}\n"
                    f"📝 メニュー: {canceled_info['menu']}\n\n"
                    f"またのご予約をお待ちしております。"
                )

                # --- 管理者（オーナー）への通知 ---
                # 本番ではオーナーのUser IDを指定しますが、今はデモとして「操作した人」に通知します
                try:
                    admin_msg = (
                        f"🗑️ 【管理者通知】予約がキャンセルされました。\n\n"
                        f"👤 顧客ID: {user_id[:8]}...\n"
                        f"📅 日時: {canceled_info['date']} {canceled_info['time']}\n"
                        f"📝 メニュー: {canceled_info['menu']}"
                    )
                    line_bot_api.push_message(
                        PushMessageRequest(
                            to=user_id, # ここをオーナーID (os.getenv('OWNER_LINE_ID')) に変更すれば本番OK
                            messages=[TextMessage(text=admin_msg)]
                        )
                    )
                except Exception as e:
                    print(f"Failed to send admin notification: {e}")
                # ----------------------------------
            else:
                reply_msg = (
                    "ℹ️ キャンセル可能な予約が見つかりませんでした。\n"
                    "（既にキャンセル済みか、もし過去の予約の場合は店舗へ直接ご連絡ください）"
                )
            
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_msg)]
                )
            )

        elif text == "店舗情報":
            video_url = "https://example.com/salon_intro.mp4" # ダミーURL、必要であれば実際の動画URLへ
            info_msg = (
                "【 Salon Antigravity 】\n\n"
                "📍 住所\n東京都渋谷区神宮前1-2-3\n\n"
                "🕘 営業時間\n09:00 - 20:00 (最終受付 19:00)\n\n"
                "定休日: 火曜日\n\n"
                "皆様のご来店を心よりお待ちしております✨"
            )
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=info_msg)]
                )
            )
            
        else:
            # エコーバック + 案内
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"「{text}」ですね！\n予約をご希望の場合は「予約」と入力してください。")]
                )
            )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
