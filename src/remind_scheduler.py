import os
import sys
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ローカルモジュールのインポート設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import google_sheets

# LINE BOT SDK v3
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import ApiException

# Load env variables (for local run)
load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

def send_reminders(target_type=None):
    """
    リマインダーを送信する関数
    
    Args:
        target_type (str): 
            'tomorrow' -> 明日の予約者へのみ送信 (前日リマインド)
            'today'    -> 今日の予約者へのみ送信 (当日リマインド)
            None       -> 両方送信 (デフォルト)
    """
    if not CHANNEL_ACCESS_TOKEN:
        print("❌ Error: LINE_CHANNEL_ACCESS_TOKEN is not set.")
        return

    # Google Sheetsから予約全件取得
    reservations = google_sheets.get_all_reservations()
    if not reservations:
        print("📭 予約データがありません。")
        return

    # 日付計算
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    today_str = today.strftime('%Y-%m-%d')
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    
    print(f"🔄 リマインド確認開始 (Type: {target_type})")
    print(f"   Today: {today_str}, Tomorrow: {tomorrow_str}")

    # LINE API設定
    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
    
    count = 0
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        for res in reservations:
            user_id = res['user_id']
            res_date = res['date']   # YYYY-MM-DD
            res_time = res['time']
            menu = res['menu']
            
            message_text = ""

            # --- 明日の予約（前日リマインド） ---
            # 「tomorrow」指定 または 指定なしの場合に実行
            if res_date == tomorrow_str and (target_type == 'tomorrow' or target_type is None):
                message_text = (
                    f"こんばんは！明日 {tomorrow_str} のご予約確認です。\n\n"
                    f"⏰ 時間: {res_time}〜\n"
                    f"📝 メニュー: {menu}\n\n"
                    f"ご来店をお待ちしております✨\n"
                    f"変更やキャンセルがある場合は、お早めにご連絡ください。"
                )
            
            # --- 今日の予約（当日リマインド） ---
            # 「today」指定 または 指定なしの場合に実行
            elif res_date == today_str and (target_type == 'today' or target_type is None):
                message_text = (
                    f"おはようございます☀️\n本日 {today_str} のご予約当日です。\n\n"
                    f"⏰ 時間: {res_time}〜\n"
                    f"📝 メニュー: {menu}\n\n"
                    f"お気をつけてお越しくださいませ💇‍♀️"
                )

            # メッセージがあれば送信
            if message_text:
                try:
                    line_bot_api.push_message(
                        PushMessageRequest(
                            to=user_id,
                            messages=[TextMessage(text=message_text)]
                        )
                    )
                    print(f"✅ リマインド送信成功: {user_id} ({res_date} {res_time})")
                    count += 1
                except ApiException as e:
                    print(f"❌ LINE API送信エラー ({user_id}): {e}")
                except Exception as e:
                    print(f"❌ 予期せぬエラー ({user_id}): {e}")

    print(f"🏁 リマインド処理完了: {count}件送信")

if __name__ == "__main__":
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='Send LINE reminders for salon reservations.')
    parser.add_argument('--type', choices=['today', 'tomorrow'], help='Specify reminder type: "today" (morning) or "tomorrow" (evening)', default=None)
    
    args = parser.parse_args()
    
    send_reminders(target_type=args.type)
