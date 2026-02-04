
from google_sheets import add_reservation_to_sheet

# テストデータを書き込む
print("🚀 スプレッドシートへの書き込みテストを開始します...")

# 2026年2月3日 16:00 に「カット」の予約が入った想定
success = add_reservation_to_sheet(
    user_id="U1234567890abcdef", 
    date_str="2026-02-03", 
    time_str="16:00", 
    menu="カット(テスト)", 
    name="テスト太郎"
)

if success:
    print("✨ 書き込み成功！Googleスプレッドシート『SalonReservations』を確認してください。")
else:
    print("❌ 書き込み失敗...")
