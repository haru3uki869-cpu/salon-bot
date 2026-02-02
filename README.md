# サロン経営DXパッケージ

サロン運営の効率化・自動化を実現するシステムパッケージです。
Lark Baseをバックエンドデータベースとし、LINE公式アカウントをフロントエンド（インターフェース）として使用します。

## 📂 ディレクトリ構成

```
salon package/
├── docs/
│   ├── PRODUCT_PROPOSAL.md  # オーナー向け提案資料
│   └── lark_base_schema.md  # データベース設計書
├── src/
│   ├── main.py              # LINE Bot × Lark 連携サーバー
│   └── automation.py        # 日次監査・集計スクリプト
├── .env.example             # 環境変数テンプレート
├── requirements.txt         # 依存ライブラリ
└── README.md                # 本ファイル
```

## 🚀 セットアップ手順

### 1. データベースの準備 (Lark Base)
`docs/lark_base_schema.md` を参照し、Lark Base上に以下のテーブルを作成してください。
*   Staff
*   Customers
*   Inventory
*   Sales

### 2. 環境変数の設定
`.env.example` をコピーして `.env` を作成し、各種トークンを設定します。

```bash
cp .env.example .env
```

必要なキー:
*   LINE Developers: Channel Secret, Access Token
*   Lark Open Platform: App ID, App Secret
*   Lark Base: Base Token, Table IDs

### 3. インストール

```bash
pip install -r requirements.txt
```

### 4. 起動

サーバーを起動し、LINE DevelopersコンソールでWebhook URLを設定してください (例: https://your-domain.com/callback)。

```bash
python src/main.py
```

## 🤖 機能

1.  **売上登録**: LINEで「売上 5000 カット」と送信
2.  **在庫利用**: LINEで「使用 カラー剤A 2」と送信
3.  **在庫アラート**: 在庫が閾値を下回ると自動通知
4.  **日次レポート**: `src/automation.py` をcron等で定期実行することでオーナーへレポート送信
