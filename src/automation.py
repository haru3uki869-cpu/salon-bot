import os
import time
from dotenv import load_dotenv
import lark_oapi as lark

load_dotenv()

# --- CONFIGURATION ---
LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')
OWNER_LINE_ID = os.getenv('OWNER_LINE_ID') # In a real app, send via LINE Bot Push Message

client = lark.Client.builder().app_id(LARK_APP_ID).app_secret(LARK_APP_SECRET).build()

def run_daily_audit():
    """
    日次監査ジョブ
    1. 売上データの異常値チェック
    2. 在庫の再確認
    3. 日報の生成
    """
    print("--- Starting Daily Audit ---")
    
    # 1. Fetch Today's Sales (Mock)
    total_sales = 150000
    sales_count = 12
    
    # 2. Anomaly Detection (Simple Rule-based AI)
    # Average exceeding 30,000 JPY might be an error for this salon type
    avg_price = total_sales / sales_count if sales_count > 0 else 0
    alerts = []
    
    if avg_price > 30000:
        alerts.append("⚠️ 平均客単価が通常より異常に高いです(¥{:.0f})。入力ミスを確認してください。".format(avg_price))
        
    if sales_count == 0:
        alerts.append("⚠️ 本日の売上登録が0件です。")

    # 3. Generate Report
    report = f"""【日次経営レポート】
----------------
売上合計: ¥{total_sales:,}
来店客数: {sales_count}名
平均単価: ¥{avg_price:,.0f}
----------------
"""
    if alerts:
        report += "\n【AI監査アラート】\n" + "\n".join(alerts)
    else:
        report += "\n✅ 異常は検出されませんでした。"

    print(report)
    print("--- Audit Complete ---")
    
    # In production: send_line_push_message(OWNER_LINE_ID, report)

if __name__ == "__main__":
    run_daily_audit()
