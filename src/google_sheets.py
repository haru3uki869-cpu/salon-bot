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

def get_all_reservations():
    """
    全ての予約データを取得する
    戻り値: 予約のリスト（辞書形式）
    """
    client = get_client()
    if not client: return []

    try:
        sheet = client.open(SPREADSHEET_NAME).sheet1
        # 全データを取得（1行目はヘッダーと仮定してスキップしたいが、データのみの場合もあるためそのまま取得して処理側で判断）
        rows = sheet.get_all_values()
        
        reservations = []
        for i, row in enumerate(rows):
            # ヘッダー行っぽい場合（日付などの文字が入っている場合）はスキップする簡易ロジック
            if len(row) > 0 and row[0] == "日付": continue
            
            # データが足りない行はスキップ
            if len(row) < 3: continue

            # [date, time, user_id, menu, name, timestamp]
            reservations.append({
                "row_index": i + 1, # スプレッドシートは1始まり
                "date": row[0],
                "time": row[1],
                "user_id": row[2],
                "menu": row[3] if len(row) > 3 else "Unknown",
                "name": row[4] if len(row) > 4 else "Guest"
            })
        return reservations

    except Exception as e:
        print(f"❌ 予約データ取得エラー: {e}")
        return []

def cancel_reservation(user_id):
    """
    指定ユーザーの未来の予約を探して削除する
    """
    client = get_client()
    if not client: return False

    try:
        sheet = client.open(SPREADSHEET_NAME).sheet1
        rows = sheet.get_all_values()
        
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        
        target_row_index = -1
        target_date = ""

        # 下から順に探して、一番新しい（未来の）予約を消すのが自然
        target_reservation = None

        for i in range(len(rows) - 1, -1, -1):
            row = rows[i]
            if len(row) < 3: continue
            
            r_date = row[0]
            r_user_id = row[2]

            # ユーザーIDが一致し、かつ日付が今日以降のもの
            if r_user_id == user_id and r_date >= today_str:
                target_row_index = i + 1 # 1-based index
                target_reservation = {
                    "date": r_date,
                    "time": row[1],
                    "menu": row[3] if len(row) > 3 else "Unknown"
                }
                break
        
        if target_row_index != -1 and target_reservation:
            sheet.delete_rows(target_row_index)
            print(f"🗑️ 予約削除成功: 行{target_row_index} ({target_reservation['date']})")
            return target_reservation
        else:
            print("ℹ️ キャンセル対象の予約が見つかりませんでした。")
            return None

    except Exception as e:
        print(f"❌ キャンセル処理エラー: {e}")
        return None

