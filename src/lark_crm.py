import os
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from dotenv import load_dotenv

# Load env used by this module
load_dotenv()

# Configuration
LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')
# 顧客管理データベースのID（URLの /base/ の後ろの部分）
LARK_BASE_APP_TOKEN = os.getenv('LARK_BASE_APP_TOKEN')
# テーブルID（URLの table= の後ろの部分。通常は自動取得も可能だが指定推奨）
LARK_BASE_TABLE_ID = os.getenv('LARK_BASE_TABLE_ID')

# Client setup
client = lark.Client.builder() \
    .app_id(LARK_APP_ID) \
    .app_secret(LARK_APP_SECRET) \
    .domain("https://open.larksuite.com") \
    .build()

def get_table_id():
    """
    環境変数にTable IDがあればそれを返す。なければBase情報を取得して最初のテーブルIDを返す。
    """
    global LARK_BASE_TABLE_ID
    if LARK_BASE_TABLE_ID and len(LARK_BASE_TABLE_ID) > 10 and "..." not in LARK_BASE_TABLE_ID:
        return LARK_BASE_TABLE_ID
    
    # Fetch table list
    print("ℹ️ Table ID not set. Fetching table list...")
    req = ListAppTableRequest.builder() \
        .app_token(LARK_BASE_APP_TOKEN) \
        .build()
        
    resp = client.bitable.v1.app_table.list(req)
    
    if resp.success() and resp.data.items:
        first_table = resp.data.items[0]
        LARK_BASE_TABLE_ID = first_table.table_id
        print(f"✅ Automatically selected Table ID: {LARK_BASE_TABLE_ID} ({first_table.name})")
        return LARK_BASE_TABLE_ID
    else:
        print(f"❌ Failed to fetch tables: {resp.code}, {resp.msg}")
        return None

def add_reservation_record(line_user_id, reservation_date, reservation_time, menu="カット"):
    """
    予約が入った際に、顧客管理テーブル（または来店履歴テーブル）にレコードを追加する
    """
    table_id = get_table_id()
    
    if not LARK_BASE_APP_TOKEN or not table_id:
        print("⚠️ Lark Baseの設定（APP_TOKEN, TABLE_ID）が足りていません。CRM保存をスキップします。")
        return False

    # 登録するデータ
    fields = {
        "LINE UserID": line_user_id,
        "予約日": reservation_date,      # YYYY-MM-DD
        "予約時間": reservation_time,    # HH:MM
        "メニュー": menu,
        "ステータス": "予約中"
    }

    # Bitable APIを使ってレコード作成
    # https://open.larksuite.com/document/server-docs/docs/bitable-v1/app-table-record/create
    req = CreateAppTableRecordRequest.builder() \
        .app_token(LARK_BASE_APP_TOKEN) \
        .table_id(table_id) \
        .request_body(AppTableRecord.builder() \
            .fields(fields) \
            .build()) \
        .build()

    resp = client.bitable.v1.app_table_record.create(req)

    if resp.success():
        print(f"✅ CRM保存成功: {line_user_id} - {reservation_date} {reservation_time}")
        return True
    else:
        print(f"❌ CRM保存失敗: {resp.code}, {resp.msg}, {resp.error}")
        # フィールド名が間違っている可能性が高いのでヒントを表示
        if resp.code == 1254002: # Field not found
            print("   (Baseの列名が一致していない可能性があります。「LINE UserID」「予約日」「予約時間」「メニュー」「ステータス」の列があるか確認してください)")
        return False
