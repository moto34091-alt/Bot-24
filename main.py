from flask import Flask
import requests
import os

app = Flask(__name__)

# =====================================
# VARIABLES ENVIRONNEMENT
# =====================================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_API_KEY")

# =====================================
# CONFIGURATION
# =====================================
PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

INTERVAL = "1min"
LANGUAGE = "FR"

# =====================================
# TELEGRAM
# =====================================
def send_telegram(message):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data)
    except:
        pass

# =====================================
# EMA
# =====================================
def calculate_ema(prices):

    return sum(prices) / len(prices)

# =====================================
# RSI
# =====================================
def calculate_rsi(closes, period=14):

    gains = []
    losses = []

    for i in range(1, len(closes)):

        diff = closes[i - 1] - closes[i]

        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain = sum(gains) / period if gains else 0.1
    avg_loss = sum(losses) / period if losses else 0.1

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# =====================================
# ANALYSE
# =====================================
def analyze_pair(symbol):

    try:

        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={symbol}"
            f"&interval={INTERVAL}"
            f"&outputsize=30"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url).json()

        if "values" not in response:
            return None

        candles = response["values"]

        close1 = float(candles[0]["close"])
        open1 = float(candles[0]["open"])
        high1 = float(candles[0]["high"])
        low1 = float(candles[0]["low"])

        volume1 = float(candles[0].get("volume", 0))
        volume2 = float(candles[1].get("volume", 0))

        closes = [float(c["close"]) for c in candles[:20]]

        ema20 = calculate_ema(closes[:20])
        ema10 = calculate_ema(closes[:10])

        rsi = calculate_rsi(closes[:15])

        # =====================================
        # TREND
        # =====================================
        trend_up = ema10 > ema20
        trend_down = ema10 < ema20

        # =====================================
        # CANDLES
        # =====================================
        body = abs(close1 - open1)

        upper_wick = high1 - max(close1, open1)
        lower_wick = min(close1, open1) - low1

        bullish = close1 > open1
        bearish = close1 < open1

        hammer = (
            lower_wick > body * 2.5 and
            bullish
        )

        shooting_star = (
            upper_wick > body * 2.5 and
            bearish
        )

        # =====================================
        # VOLUME
        # =====================================
        high_volume = volume1 >= volume2

        # =====================================
        # VOLATILITY
        # =====================================
        candle_size = high1 - low1

        volatility_ok = candle_size > (close1 * 0.0005)

        # =====================================
        # STRONG BODY
        # =====================================
        strong_body = body > candle_size * 0.3

        # =====================================
        # CALL SIGNAL
        # =====================================
        if (
            trend_up and
            hammer and
            high_volume and
            volatility_ok and
            strong_body and
            rsi > 50
        ):

            return (
                f"📈 CALL SIGNAL\n\n"
                f"Pair: {symbol}\n"
                f"Trend: UP\n"
                f"RSI: {round(rsi,2)}\n"
                f"Volume: HIGH\n"
                f"Pattern: HAMMER\n"
                f"Timeframe: {INTERVAL}"
            )

        # =====================================
        # PUT SIGNAL
        # =====================================
        if (
            trend_down and
            shooting_star and
            high_volume and
            volatility_ok and
            strong_body and
            rsi < 50
        ):

            return (
                f"📉 PUT SIGNAL\n\n"
                f"Pair: {symbol}\n"
                f"Trend: DOWN\n"
                f"RSI: {round(rsi,2)}\n"
                f"Volume: HIGH\n"
                f"Pattern: SHOOTING STAR\n"
                f"Timeframe: {INTERVAL}"
            )

        return None

    except Exception as e:

        return f"ERROR: {str(e)}"

# =====================================
# HOME
# =====================================
@app.route("/")
def home():

    return (
        "🏦 HEDGE FUND BOT RUNNING\n\n"
        "OPTIONS:\n"
        "/forex\n"
        "/crypto\n"
        "/gold\n"
        "/m1\n"
        "/m5\n"
        "/fr\n"
        "/en\n"
        "/signal"
    )

# =====================================
# FOREX MODE
# =====================================
@app.route("/forex")
def forex():

    global PAIRS

    PAIRS = [
        "EUR/USD",
        "GBP/USD",
        "USD/JPY",
        "AUD/USD"
    ]

    return "✅ FOREX MODE ACTIVATED"

# =====================================
# CRYPTO MODE
# =====================================
@app.route("/crypto")
def crypto():

    global PAIRS

    PAIRS = [
        "BTC/USD",
        "ETH/USD",
        "SOL/USD"
    ]

    return "✅ CRYPTO MODE ACTIVATED"

# =====================================
# GOLD MODE
# =====================================
@app.route("/gold")
def gold():

    global PAIRS

    PAIRS = [
        "XAU/USD"
    ]

    return "✅ GOLD MODE ACTIVATED"

# =====================================
# TIMEFRAME 1MIN
# =====================================
@app.route("/m1")
def m1():

    global INTERVAL

    INTERVAL = "1min"

    return "✅ TIMEFRAME 1MIN"

# =====================================
# TIMEFRAME 5MIN
# =====================================
@app.route("/m5")
def m5():

    global INTERVAL

    INTERVAL = "5min"

    return "✅ TIMEFRAME 5MIN"

# =====================================
# LANGUE FR
# =====================================
@app.route("/fr")
def fr():

    global LANGUAGE

    LANGUAGE = "FR"

    return "✅ LANGUE FRANÇAISE"

# =====================================
# LANGUE EN
# =====================================
@app.route("/en")
def en():

    global LANGUAGE

    LANGUAGE = "EN"

    return "✅ ENGLISH LANGUAGE"

# =====================================
# TEST
# =====================================
@app.route("/test")
def test():

    send_telegram("✅ BOT TEST SUCCESS")

    return "TEST SENT"

# =====================================
# SIGNAL
# =====================================
@app.route("/signal")
def signal():

    messages = []

    for pair in PAIRS:

        result = analyze_pair(pair)

        if result and "ERROR" not in result:

            send_telegram(result)

            messages.append(result)

    if messages:
        return "\n\n".join(messages)

    return "NO SIGNAL"

# =====================================
# DEBUG
# =====================================
@app.route("/debug")
def debug():

    result = analyze_pair(PAIRS[0])

    return str(result)

# =====================================
# RUN SERVER
# =====================================
if __name__ == "__main__":

    PORT = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=PORT
    )
