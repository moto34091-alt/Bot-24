from flask import Flask
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

# =========================
# VARIABLES ENVIRONNEMENT
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_API_KEY")

# =========================
# CONFIGURATION
# =========================
PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

INTERVAL = "1min"

# =========================
# TELEGRAM
# =========================
def send_telegram(message):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=data)

# =========================
# EMA CALCULATION
# =========================
def calculate_ema(prices):

    return sum(prices) / len(prices)

# =========================
# RSI CALCULATION
# =========================
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

# =========================
# ANALYSE MARCHÉ
# =========================
def analyze_pair(symbol):

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
    volume1 = float(candles[0]["volume"])

    volume2 = float(candles[1]["volume"])

    closes = [float(c["close"]) for c in candles[:20]]

    ema20 = calculate_ema(closes[:20])
    ema10 = calculate_ema(closes[:10])

    rsi = calculate_rsi(closes[:15])

    # =========================
    # TENDANCE
    # =========================
    trend_up = ema10 > ema20
    trend_down = ema10 < ema20

    # =========================
    # BOUGIES
    # =========================
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

    # =========================
    # VOLUME
    # =========================
    high_volume = volume1 > volume2

    # =========================
    # VOLATILITÉ
    # =========================
    candle_size = high1 - low1

    volatility_ok = candle_size > (close1 * 0.0005)

    # =========================
    # FILTRE ANTI PETITES BOUGIES
    # =========================
    strong_body = body > candle_size * 0.3

    # =========================
    # SIGNAL CALL
    # =========================
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
            f"Timeframe: 1min"
        )

    # =========================
    # SIGNAL PUT
    # =========================
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
            f"Timeframe: 1min"
        )

    return None

# =========================
# BOT LOOP
# =========================
def bot_loop():

    while True:

        try:

            for pair in PAIRS:

                result = analyze_pair(pair)

                if result:
                    send_telegram(result)

                time.sleep(3)

        except Exception as e:

            send_telegram(f"❌ ERROR:\n{str(e)}")

        time.sleep(60)

# =========================
# ROUTES
# =========================
@app.route("/")
def home():

    return "BOT ONLINE"

@app.route("/test")
def test():

    send_telegram("✅ BOT TEST SUCCESS")

    return "TEST SENT"

@app.route("/signal")
def signal():

    messages = []

    for pair in PAIRS:

        result = analyze_pair(pair)

        if result:

            send_telegram(result)

            messages.append(result)

    if messages:
        return "\n\n".join(messages)

    return "NO SIGNAL"

# =========================
# START BACKGROUND LOOP
# =========================
thread = Thread(target=bot_loop)
thread.daemon = True
thread.start()

# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":

    PORT = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=PORT)
