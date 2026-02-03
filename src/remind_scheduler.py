
import os
import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from linebot import LineBotApi
from linebot.models import TextMessage
from linebot.exceptions import LineBotApiError
from google_sheets import get_all_reservations

# 環境変数からLINE BOTのトークンを取得
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

def send_reminders():
    """
    明日の予約者と当日の予約者にリマインドを送る
    """
    if not CHANNEL_ACCESS_TOKEN:
        print("❌ LINE_CHANNEL_ACCESS_TOKENが設定されていません。")
        return

    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    reservations = get_all_reservations()
    
    if not reservations:
        print("ℹ️ 予約データがありません（または取得失敗）。")
        return

    # 日付の計算
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    
    today_str = today.strftime('%Y-%m-%d')
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')

    print(f"📅 リマインド実行: 今日={today_str}, 明日={tomorrow_str}")

    count_tomorrow = 0
    count_today = 0

    for res in reservations:
        user_id = res['user_id']
        res_date = res['date']
        res_time = res['time']
        menu = res['menu']

        # 前日リマインド
        if res_date == tomorrow_str:
            try:
                message = (
                    f"【前日リマインド】\n"
                    f"明日 {res_time} からのご予約をお待ちしております✨\n"
                    f"メニュー: {menu}\n\n"
                    f"※変更やキャンセルがある場合は、メニューからその旨お知らせください。"
                )
                line_bot_api.push_message(user_id, TextMessage(text=message))
                print(f"✅ 前日リマインド送信: {user_id} ({res_date} {res_time})")
                count_tomorrow += 1
            except LineBotApiError as e:
                print(f"❌ 送信エラー({user_id}): {e}")

        # 当日リマインド
        elif res_date == today_str:
            try:
                message = (
                    f"【本日リマインド】\n"
                    f"本日はご予約ありがとうございます😊\n"
                    f"日時: {res_time}〜\n"
                    f"メニュー: {menu}\n\n"
                    f"ご来店を心よりお待ちしております！気をつけてお越しください。"
                )
                line_bot_api.push_message(user_id, TextMessage(text=message))
                print(f"✅ 当日リマインド送信: {user_id} ({res_date} {res_time})")
                count_today += 1
            except LineBotApiError as e:
                print(f"❌ 送信エラー({user_id}): {e}")

    print(f"🏁 完了: 前日リマインド={count_tomorrow}件, 当日リマインド={count_today}件")

if __name__ == "__main__":
    # 環境変数をロードするために python-dotenv を使う（ローカル実行時用）
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass # Render上などでは入っていない場合があるが、環境変数は設定済み想定

    send_reminders()
