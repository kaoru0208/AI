#!/bin/bash
# 
# Step 1: 必要なPythonパッケージをインストール（OANDA APIラッパー、ニュースAPIクライアント、センチメント分析ツール）
pip3 install --upgrade oandapyV20 newsapi-python vaderSentiment || exit 1

# Step 2: APIキーや設定を保存する設定ファイルを作成/更新
# 既に設定ファイルや環境変数で設定している場合は、この部分を調整してください。
# ここではサンプルのconfig.pyを作成し、後でユーザーが値を入力できるようにしています。
cat > config.py << 'EOF'
# OANDA APIの認証情報と設定
ACCOUNT_ID = 101-009-35627361-001       # TODO: ご自身のOANDAアカウントIDに置き換えてください
ACCESS_TOKEN = ad06897d472c6ac1adc1ef3bc9e08e57-cccc549507e86d74e3c442add43d5a0b　      # TODO: ご自身のOANDA APIトークンに置き換えてください
API_ENV = "practice"                       # デモ口座を利用する場合は"practice"、本番口座は"live"

# トレード設定
INSTRUMENT = "USD_JPY"                     # トレードする通貨ペア（例：ドル円）
RISK_PER_TRADE = 0.01                      # 1トレードあたり口座残高の何％をリスク許容とするか（例：1%）
NEWS_API_KEY = "YOUR_NEWSAPI_KEY"          # TODO: ニュースAPIのキーをここに設定（ニュース分析に使用）
NEWS_QUERY = ""                            # 特定のニュース検索キーワード（例："USD JPY"）。空文字の場合、通貨ペア名を使用します。
NEWS_CHECK_INTERVAL = 3600                 # ニュースセンチメントをチェックする間隔（秒）。3600秒=1時間ごと。
EOF

echo "Created config.py. Please open this file and insert your real API credentials (ACCOUNT_ID, ACCESS_TOKEN, NEWS_API_KEY)."

# Step 3: 新機能（トレーリングストップ、ニュース分析、リスク管理強化）を組み込んだメインのトレードボットコードを生成
cat > trading_bot_v2.py << 'EOF'
import os
import time
import math
from datetime import datetime

# OANDA API関連のモジュールをインポート
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.accounts as accounts
from oandapyV20.contrib.requests import MarketOrderRequest, TrailingStopLossDetails, TakeProfitDetails

# ニュースAPIとセンチメント分析のインポート
from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# 設定の読み込み
try:
    import config
    ACCOUNT_ID = config.ACCOUNT_ID
    ACCESS_TOKEN = config.ACCESS_TOKEN
    API_ENV = config.API_ENV if hasattr(config, 'API_ENV') else "practice"
    INSTRUMENT = config.INSTRUMENT if hasattr(config, 'INSTRUMENT') else "USD_JPY"
    RISK_PER_TRADE = config.RISK_PER_TRADE if hasattr(config, 'RISK_PER_TRADE') else 0.01
    NEWS_API_KEY = config.NEWS_API_KEY if hasattr(config, 'NEWS_API_KEY') else ""
    NEWS_QUERY = config.NEWS_QUERY if hasattr(config, 'NEWS_QUERY') else ""
    NEWS_CHECK_INTERVAL = config.NEWS_CHECK_INTERVAL if hasattr(config, 'NEWS_CHECK_INTERVAL') else 3600
except ImportError:
    # config.pyが無い場合、環境変数から読み込む
    ACCOUNT_ID = os.environ.get("OANDA_ACCOUNT_ID")
    ACCESS_TOKEN = os.environ.get("OANDA_ACCESS_TOKEN")
    API_ENV = os.environ.get("OANDA_API_ENV", "practice")
    INSTRUMENT = os.environ.get("OANDA_INSTRUMENT", "USD_JPY")
    RISK_PER_TRADE = float(os.environ.get("RISK_PER_TRADE", 0.01))
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
    NEWS_QUERY = os.environ.get("NEWS_QUERY", "")
    NEWS_CHECK_INTERVAL = int(os.environ.get("NEWS_CHECK_INTERVAL", 3600))

# 必須の設定があるか確認
if not ACCOUNT_ID or not ACCESS_TOKEN:
    raise RuntimeError("Missing OANDA API credentials! Please set them in config.py or environment variables.")

# OANDA APIクライアントを初期化
api_client = API(access_token=ACCESS_TOKEN, environment=API_ENV)

# ニュースAPIクライアントとセンチメント分析器を初期化（APIキーがある場合）
news_client = None
if NEWS_API_KEY:
    news_client = NewsApiClient(api_key=NEWS_API_KEY)
analyzer = SentimentIntensityAnalyzer()

# ヘルパー関数：現在のレート取得（ミッドプライスを返す）
def get_current_price(instrument):
    params = {"instruments": instrument}
    price_req = pricing.PricingInfo(accountID=ACCOUNT_ID, params=params)
    resp = api_client.request(price_req)
    # OANDAのAPIはbidとaskを返すので、その平均を取る
    price = None
    if 'prices' in resp and len(resp['prices']) > 0:
        bid = float(resp['prices'][0]['bids'][0]['price'])
        ask = float(resp['prices'][0]['asks'][0]['price'])
        price = (bid + ask) / 2.0
    return price

# ヘルパー関数：直近のローソク足からATR（平均的な変動幅）を計算
def get_ATR(instrument, period=14, granularity="H1"):
    # period+1本のローソク足データを取得（ATR計算に前日終値が必要なため）
    params = {"count": period+1, "granularity": granularity, "price": "M"}
    candles_req = instruments.InstrumentsCandles(instrument=instrument, params=params)
    data = api_client.request(candles_req)
    candles = data.get('candles', [])
    if len(candles) < period+1:
        return None
    # True Rangeを計算しATRを求める
    trs = []
    prev_close = None
    for candle in candles:
        if not candle['complete']:
            continue
        high = float(candle['mid']['h'])
        low = float(candle['mid']['l'])
        close = float(candle['mid']['c'])
        if prev_close is None:
            # 最初のTR計算時は前のクローズが無いのでスキップ
            prev_close = close
            continue
        # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
        prev_close = close
    if len(trs) == 0:
        return None
    # シンプルな平均を用いてATR算出（より厳密には指数移動平均などもあります）
    atr = sum(trs[-period:]) / float(len(trs[-period:]))
    return atr

# ヘルパー関数：ニュースを取得しセンチメントスコアを算出
def get_news_sentiment():
    if news_client is None:
        return None
    # ニュース検索クエリを決定（指定が無ければ通貨ペアをスペース区切りにしたものを使用）
    query = NEWS_QUERY if NEWS_QUERY else INSTRUMENT.replace('_', ' ')
    try:
        response = news_client.get_top_headlines(q=query, language='en')
    except Exception as e:
        print(f"[WARN] News API request failed: {e}")
        return None
    articles = response.get('articles', [])
    if not articles:
        return None
    # 記事タイトルのセンチメントを平均化
    total_score = 0.0
    count = 0
    for article in articles:
        title = article.get('title', '') or ''
        if not title:
            continue
        vs = analyzer.polarity_scores(title)
        total_score += vs['compound']
        count += 1
    if count == 0:
        return None
    avg_score = total_score / count
    # avg_scoreは-1（極めてネガティブ）～+1（極めてポジティブ）の範囲
    return avg_score

# ヘルパー関数：リスク管理に基づくポジションサイズを計算
def calculate_position_size(balance, risk_fraction, stop_distance, price):
    """
    概算で、指定したリスク割合に対し与えられたストップ距離分の損失となるポジション数量を計算します。
    （口座通貨と通貨ペアの決済通貨が同じ場合を想定。異なる場合はレート換算が必要です）
    """
    if stop_distance <= 0 or balance is None:
        return 0
    risk_amount = balance * risk_fraction
    # 簡略化: 1通貨単位あたり価格がstop_distance動いたときにその分損益が出ると仮定
    units = risk_amount / stop_distance
    # 単位数は整数に
    units = math.floor(units)
    return units

# 簡易な売買シグナルの例：移動平均クロスオーバー（デモ用）
def check_trade_signal():
    # MA計算用に直近50本のH1足終値を取得
    params = {"count": 50, "granularity": "H1", "price": "M"}
    candles_req = instruments.InstrumentsCandles(instrument=INSTRUMENT, params=params)
    data = api_client.request(candles_req)
    candles = [c for c in data.get('candles', []) if c['complete']]
    if len(candles) < 50:
        return None  # データ不足の場合はシグナルなし
    # 20期間と50期間の単純移動平均を算出
    closes = [float(c['mid']['c']) for c in candles]
    sma_short = sum(closes[-20:]) / 20.0
    sma_long = sum(closes[-50:]) / 50.0
    # シグナル判定：短期MAが長期MAを上抜きしたら買い、下抜きしたら売り
    if sma_short > sma_long * 1.001:  # 短期MAが長期MAよりわずかに上ならBUY
        return "BUY"
    elif sma_short < sma_long * 0.999:  # 短期MAが長期MAよりわずかに下ならSELL
        return "SELL"
    else:
        return None

# 自動売買ループ開始
print("Starting trading bot with instrument:", INSTRUMENT)
news_sentiment = None
last_news_check = 0
opened_trades = 0  # デモ用に実行したトレード数をカウント
try:
    while True:
        # ループの待機時間（必要に応じて調整）
        time.sleep(60)  # 60秒ごとにチェック
        # 一定間隔でニュースセンチメントを更新
        if news_client and (time.time() - last_news_check > NEWS_CHECK_INTERVAL):
            sentiment_score = get_news_sentiment()
            if sentiment_score is not None:
                news_sentiment = sentiment_score
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - News sentiment updated (score={news_sentiment:.3f})")
            last_news_check = time.time()
        # 売買シグナルの確認
        signal = check_trade_signal()
        if signal:
            current_price = get_current_price(INSTRUMENT)
            if current_price is None:
                print("[WARN] 現在価格の取得に失敗しました。次のループへ。")
                continue
            # ファンダメンタルイベントフィルター: 重大指標発表前などは取引スキップ（必要に応じて実装）
            # ニュースセンチメントフィルター: センチメントが極端に悪い中での買い信号などは回避
            if news_sentiment is not None:
                if signal == "BUY" and news_sentiment < -0.3:
                    print(f"シグナル=BUY しかしニュースセンチメントがネガティブ（score={news_sentiment:.2f}）、取引を見送り。")
                    signal = None
                elif signal == "SELL" and news_sentiment > 0.3:
                    print(f"シグナル=SELL しかしニュースセンチメントがポジティブ（score={news_sentiment:.2f}）、取引を見送り。")
                    signal = None
            if not signal:
                continue  # センチメントにより取引をスキップした場合、次のループへ
            # リスク管理に基づきポジションサイズを決定（ATRをストップ距離として使用）
            balance = None
            try:
                acc_req = accounts.AccountDetails(accountID=ACCOUNT_ID)
                acc_data = api_client.request(acc_req)
                balance = float(acc_data['account']['balance'])
            except Exception as e:
                print(f"[WARN] 口座残高の取得に失敗しました。デフォルト値を使用します: {e}")
            atr = get_ATR(INSTRUMENT, period=14, granularity="H1")
            if atr is None:
                atr = 0.0
            # ATRが極端に小さい（例: データ取得失敗や極端な低ボラティリティ）の場合、最小ストップ幅を設定
            stop_distance = atr if atr > 0 else (0.001 if INSTRUMENT.endswith("JPY") else 0.0001)
            units = calculate_position_size(balance if balance is not None else 10000, RISK_PER_TRADE, stop_distance, current_price)
            if units == 0:
                print("[INFO] 計算されたポジションサイズが0のため、取引をスキップします。")
                continue
            if signal == "SELL":
                units = -units  # 売りの場合はマイナス数量
            # 成行注文を発注（トレーリングストップを指定）
            try:
                trailing_distance = stop_distance  # トレーリングストップ幅としてATR相当を使用
                ordr = MarketOrderRequest(
                    instrument=INSTRUMENT,
                    units=units,
                    trailingStopLossOnFill=TrailingStopLossDetails(distance=trailing_distance).data
                    # 任意で利益確定注文を同時設定可能:
                    # takeProfitOnFill=TakeProfitDetails(price=<目標価格>).data
                )
                order_create = orders.OrderCreate(accountID=ACCOUNT_ID, data=ordr.data)
                resp = api_client.request(order_create)
                opened_trades += 1
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {INSTRUMENT} に対して {signal} の成行注文発注: 数量={units} (注文ID: {resp.get('orderFillTransaction', {}).get('id', 'N/A')})")
            except Exception as e:
                print(f"[ERROR] 注文発注に失敗しました: {e}")
                # エラー時には再試行や通知処理をここに追加できます
                continue
        # （オプション）既存ポジションの管理ロジック: トレーリングストップはOANDA側で自動調整されるため不要ですが、
        # 必要であればここでポジション状況を監視し追加のクローズ条件を入れることができます。
        
        # デモ目的: 一定回数トレードしたらループを抜ける
        if opened_trades >= 5:
            print("5件の注文を発注したため、デモ用リミットに達しました。ボットを停止します。")
            break
except KeyboardInterrupt:
    print("Trading bot stopped by user.")
EOF

echo "trading_bot_v2.py を作成しました。新機能が実装されています。"
echo "config.pyの値（特にAPI認証情報）を編集し、内容を確認してからボットを実行してください。"
echo "ボットを起動するには次のコマンドを実行します: python3 trading_bot_v2.py"

