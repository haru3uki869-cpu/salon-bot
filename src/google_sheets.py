import gspread
import os
import datetime
import json

# スプレッドシートの名前（共有時にこれと同じ名前にする）
SPREADSHEET_NAME = 'SalonReservations'

def get_client():
    """
    gspreadクライアントを取得する（環境変数 or ファイル）
    """
    # 1. 環境変数から読み込み（Render用）
    json_creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if json_creds:
        try:
            creds_dict = json.loads(json_creds)
            return gspread.service_account_from_dict(creds_dict)
        except Exception as e:
            print(f"⚠️ 環境変数からの認証失敗: {e}")

    # 2. ファイルから読み込み（ローカル用: service_account.json または salon-bot-xxx.json を探す）
    # VSCodeに置いた salon-bot-*.json を自動で探すロジック
    for file in os.listdir('.'):
        if file.startswith("salon-bot-") and file.endswith(".json"):
            return gspread.service_account(filename=file)
            
    if os.path.exists('service_account.json'):
        return gspread.service_account(filename='service_account.json')

    return None

def add_reservation_to_sheet(user_id, date_str, time_str, menu, name=None):
    """
    予約情報をGoogleスプレッドシートに追記する
    """
    client = get_client()
    if not client:
        print("ℹ️ Google Sheets連携スキップ: 認証情報が見つかりません。")
        return False

    try:
        # シートを開く
        try:
            sheet = client.open(SPREADSHEET_NAME).sheet1
        except gspread.SpreadsheetNotFound:
            print(f"⚠️ スプレッドシート '{SPREADSHEET_NAME}' が見つかりません。Bot（サービスアカウント）に共有されていますか？")
            return False

        # 行を追加
        # 日時, 顧客ID, メニュー, 名前, 登録タイムスタンプ
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row = [date_str, time_str, user_id, menu, name or "LINE User", timestamp]
        
        sheet.append_row(row)
        print(f"✅ Google Sheetに追加しました: {row}")
        return True

    except Exception as e:
        print(f"❌ Google Sheet連携エラー: {e}")
        return False
