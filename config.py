# OANDA APIの認証情報と設定
ACCOUNT_ID = "101-009-35627361-001"
ACCESS_TOKEN = "ad06897d472c6ac1adc1ef3bc9e08e57-cccc549507e86d74e3c442add43d5a0b"
API_ENV = "practice"  # デモなら practice, 本番は live

# トレード設定
INSTRUMENT = "USD_JPY"
RISK_PER_TRADE = 0.01
NEWS_API_KEY = "9bd2d2e546454039884e976aa7cd2121"
NEWS_QUERY = ""  # 空なら自動で USD JPY
NEWS_CHECK_INTERVAL = 3600


# --- 追加パラメータ（自動追記） ---
PROM_PUSH_URL = "http://localhost:9091"  # Prometheus Pushgateway
DISCORD_WEBHOOK = ""  # Discord Webhook URL（任意）
TARGET_PAIRS = ["USD_JPY", "EUR_USD", "GBP_JPY"]  # 監視通貨ペア
MAX_VAR = 0.02  # 1‑day VaR 上限 (2 %)
