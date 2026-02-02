import os
import sys
import lark_oapi as lark
from lark_oapi.api.calendar.v4 import *
from dotenv import load_dotenv

# Load env
env_path = os.path.join(os.getcwd(), '.env')
load_dotenv(env_path)

LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')

def diagnose():
    print("--- Lark API 診断開始 ---")
    print(f"App ID: {LARK_APP_ID}")
    
    if not LARK_APP_ID or not LARK_APP_SECRET:
        print("❌ App ID または Secret が不足しています")
        return

    # Client作成 (Log LevelをDEBUGにして詳細を見る)
    client = lark.Client.builder() \
        .app_id(LARK_APP_ID) \
        .app_secret(LARK_APP_SECRET) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    print("\n[テスト1: カレンダーリスト取得]")
    # カレンダー一覧を取得してみる (EventsではなくCalendarそのもの)
    req = ListCalendarRequest.builder().build()
    
    try:
        resp = client.calendar.v4.calendar.list(req)
        
        if resp.success():
            print("✅ カレンダーリスト取得成功！")
            if resp.data and resp.data.calendar_list:
                for cal in resp.data.calendar_list:
                    print(f" - ID: {cal.calendar_id}, Summary: {cal.summary}, Role: {cal.role}")
            else:
                print("   (カレンダーが見つかりません)")
        else:
            print(f"❌ カレンダーリスト取得失敗: Code {resp.code}")
            print(f"   Msg: {resp.msg}")
            print(f"   Error: {resp.error}")
            
    except Exception as e:
        print(f"❌ 例外発生: {e}")

    print("\n--- 診断終了 ---")

if __name__ == "__main__":
    diagnose()
