import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to python path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Load env
env_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print("❌ .env not found")
    sys.exit(1)

import lark_calendar
import scheduler

def test_reservation_30min():
    print("--- 30分単位予約登録テスト開始 ---")
    
    # Check unit
    print(f"現在の予約枠単位: {scheduler.SLOT_UNIT_MINUTES}分")
    if scheduler.SLOT_UNIT_MINUTES != 30:
        print("❌ 予約枠が30分になっていません。")
        return

    # Test date: Tomorrow 10:00
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    # 1st slot: 10:00 - 10:30
    start_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0, 0)
    end_dt = start_dt + timedelta(minutes=30)
    
    summary = "【テスト予約】カット 30分枠"
    description = "自動テストによる30分単位の予約登録"
    
    print(f"予約作成日時: {start_dt} - {end_dt}")
    
    # Create
    success = lark_calendar.create_calendar_event(summary, start_dt, end_dt, description)
    
    if success:
        print("✅ 予約登録成功！(Create API)")
        
        # Verify
        print("予約確認中...(Get API)")
        # Fetch with buffer
        events = lark_calendar.get_calendar_events(start_dt, end_dt)
        found = False
        for event in events:
            if summary in event['summary']:
                print(f"✅ 登録された予約が見つかりました: {event['summary']} ({event['start']} - {event['end']})")
                found = True
                break
        
        if not found:
            print("⚠️ 登録したはずの予約が一覧に見つかりません（反映遅延の可能性あり）")
            # debug
            print("取得できたイベント:")
            for e in events:
                print(f" - {e['summary']}: {e['start']} - {e['end']}")
            
    else:
        print("❌ 予約登録失敗")

    print("--- テスト終了 ---")

if __name__ == "__main__":
    test_reservation_30min()
