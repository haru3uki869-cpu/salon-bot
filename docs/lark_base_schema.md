# Lark Base データベース設計書

サロンDXパッケージの中核となるデータベース設計です。

## テーブル一覧

### 1. スタッフ管理テーブル (Staff)
スタッフの基本情報と歩合率を管理します。
*   **スタッフID** (Text, Primary Key)
*   **氏名** (Text)
*   **LINE User ID** (Text) - LINE連携用
*   **役職** (Single Select: スタイリスト, アシスタント, 店長)
*   **基本給** (Currency)
*   **指名歩合率** (Number, %) - 例: 10%なら0.1
*   **フリー歩合率** (Number, %)
*   **店販歩合率** (Number, %)

### 2. 顧客管理テーブル (Customers)
顧客情報と来店履歴を管理します。
*   **顧客ID** (Text, Primary Key)
*   **氏名** (Text)
*   **LINE連携ID** (Text)
*   **最終来店日** (Date)
*   **総来店回数** (Number)
*   **備考/カルテリンク** (Url)

### 3. 在庫管理テーブル (Inventory)
薬剤や店販商品の在庫を管理します。
*   **商品ID** (Text, Primary Key)
*   **商品名** (Text)
*   **カテゴリ** (Single Select: カラー剤, パーマ液, 店販シャンプー, etc)
*   **現在在庫数** (Number)
*   **発注点** (Number) - この数値を下回ったらアラート
*   **単価** (Currency)

### 4. 売上管理テーブル (Sales)
日々の売上を記録します。
*   **売上ID** (Text, Primary Key) - 自動生成
*   **日時** (Date Time)
*   **担当スタッフ** (Link to Staff)
*   **顧客** (Link to Customers)
*   **メニュー区分** (Single Select: カット, カラー, パーマ, 店販)
*   **売上金額** (Currency)
*   **歩合対象額** (Formula) - メニュー区分と担当スタッフの歩合率から自動計算

### 5. 在庫変動ログ (InventoryLogs)
いつ、誰が、何を使ったかを記録します。
*   **ログID** (Text)
*   **日時** (Date Time)
*   **商品** (Link to Inventory)
*   **変動数** (Number) - 使用ならマイナス、納品ならプラス
*   **担当スタッフ** (Link to Staff)

### 6. 予約管理テーブル (Reservations)
LINE予約システムからのデータを格納します。
*   **予約ID** (Text, Primary Key)
*   **顧客** (Link to Customers)
*   **予約日時** (Date Time)
*   **終了日時** (Date Time)
*   **メニュー** (Single Select: カット(39分), カラー(78分), etc)
*   **所要スロット数** (Number) - 39分を1単位とした必要枠数
*   **ステータス** (Single Select: 確定, キャンセル, 来店済み)
