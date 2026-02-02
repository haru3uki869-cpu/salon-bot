import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import datetime

# 設定ファイルのパス（Botと同じフォルダに置く想定）
JSON_KEYFILE = 'service_account.json'
SPREADSHEET_NAME = 'SalonReservations' # スプレッドシートの名前（共有時にこれと同じ名前にする）

def add_reservation_to_sheet(user_id, date_str, time_str, menu, name=None):
    """
    予約情報をGoogleスプレッドシートに追記する
    """
    if not os.path.exists(JSON_KEYFILE):
        print(f"ℹ️ Google Sheets連携スキップ: {JSON_KEYFILE} が見つかりません。")
        return False

    try:
        # 認証
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
        client = gspread.authorize(creds)

        # シートを開く
        try:
            sheet = client.open(SPREADSHEET_NAME).sheet1
        except gspread.SpreadsheetNotFound:
            print(f"⚠️ スプレッドシート '{SPREADSHEET_NAME}' が見つかりません。")
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
