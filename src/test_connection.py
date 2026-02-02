import os
import sys
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
import lark_oapi as lark
from lark_oapi.api.calendar.v4 import *

def test_connections():
    print("--- 接続テスト開始 ---")

    # 1. Load .env
    env_path = os.path.join(os.getcwd(), 'docs', '.env')
    if not os.path.exists(env_path):
        # Try root .env
        env_path = os.path.join(os.getcwd(), '.env')
    
    if os.path.exists(env_path):
        print(f"Loading env from: {env_path}")
        load_dotenv(env_path)
    else:
        print("❌ .envファイルが見つかりません。")
        return

    # 2. LINE Messaging API Test
    print("\n[LINE Messaging API テスト]")
    line_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    if not line_token:
        print("❌ LINE_CHANNEL_ACCESS_TOKEN が設定されていません。")
    else:
        try:
            line_bot_api = LineBotApi(line_token)
            bot_info = line_bot_api.get_bot_info()
            print(f"✅ 接続成功！ Bot名: {bot_info.display_name}")
            print(f"   UserID: {bot_info.user_id}")
            print(f"   BasicId: {bot_info.basic_id}")
        except LineBotApiError as e:
            print(f"❌ LINE接続エラー: {e.status_code} {e.error.message}")
        except Exception as e:
            print(f"❌ エラー: {e}")

    # 3. Lark API Test
    print("\n[Lark Open Platform テスト]")
    app_id = os.getenv('LARK_APP_ID')
    app_secret = os.getenv('LARK_APP_SECRET')
    
    if not app_id or not app_secret:
        print("❌ Lark App ID または App Secret が設定されていません。")
    else:
        try:
            # DOMAIN_LARK is needed for non-CN apps
            # Use explicit URL if constant is missing
            client = lark.Client.builder() \
                .app_id(app_id) \
                .app_secret(app_secret) \
                .domain("https://open.larksuite.com") \
                .build()
            
            # Try to fetch tenant access token indirectly by making a simple request
            # Or just check calendar resource to verify permissions
            print("   Lark Calendar APIへのアクセス確認中...")
            
            # List calendars to find a valid one
            print(f"   カレンダーリスト取得中...")
            req = ListCalendarRequest.builder().build()
            resp = client.calendar.v4.calendar.list(req)
            
            if resp.code == 0:
                print("✅ 接続成功！ カレンダーリスト取得成功。")
                if resp.data and resp.data.calendar_list:
                    print(f"   取得できたカレンダー数: {len(resp.data.calendar_list)}")
                    for cal in resp.data.calendar_list:
                        print(f"   - ID: {cal.calendar_id}, Name: {cal.summary}, Role: {cal.role}")
                else:
                    print("   (カレンダーが見つかりませんでした。Botにカレンダー権限がないか、カレンダーが作成されていません)")
            else:
                print(f"❌ Lark APIエラー: Code {resp.code}, Msg: {resp.msg}")
                if resp.code == 191001:
                    print("   ('primary'カレンダーはBot(Tenant Access Token)ではアクセスできません。特定のCalendar IDが必要です)")
                
        except Exception as e:
            print(f"❌ エラー: {e}")

    print("\n--- テスト終了 ---")

if __name__ == "__main__":
    test_connections()
