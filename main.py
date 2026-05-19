from flask import Flask
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

# =========================
# VARIABLES ENV
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_API_KEY")

# =========================
# CONFIG
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
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message
        }
        requests.post(url, data=data)
    except:
        pass

# =========================
# EMA (CORRECT)
# =========================
def calculate_ema(prices, period):
    k = 2 / (period + 1)
    ema = prices[0]

    for price in prices[1:]:
        ema = price * k + ema * (1 - k)

    return ema

# =========================
# RSI (FIXED)
# =========================
def calculate_rsi(closes, period=14):
    gains = []
    losses = []

    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]

        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period if gains else 0
    avg_loss = sum(losses[-period:]) / period if losses else 0

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =========================
# ANALYSE
# =========================
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

        candles = response["values"][::-1]  # IMPORTANT: ordre correct

        close1 = float(candles[-1]["close"])
        open1 = float(candles[-1]["open"])
        high1 = float(candles[-1]["high"])
        low1 = float(candles[-1]["low"])

        closes = [float(c["close"]) for c in candles]

        ema10 = calculate_ema(closes[-10:], 10)
        ema20 = calculate_ema(closes[-20:], 20)
        rsi = calculate_rsi(closes[-15:], 14)

        # =========================
        # TREND
        # =========================
        trend_up = ema10 > ema20
        trend_down = ema10 < ema20

        # =========================
        # CANDLE PATTERN
        # =========================
        body = abs(close1 - open1)
        upper_wick = high1 - max(close1, open1)
        lower_wick = min(close1, open1) - low1

        bullish = close1 > open1
        bearish = close1 < open1

        hammer = lower_wick > body * 2.5 and bullish
        shooting_star = upper_wick > body * 2.5 and bearish

        # =========================
        # VOLUME FIX (FOREX SAFE)
        # =========================
        volume1 = abs(high1 - low1)
        volume2 = abs(
            float(candles[-2]["high"]) - float(candles[-2]["low"])
        )

        high_volume = volume1 > volume2

        # =========================
        # VOLATILITY
        # =========================
        candle_size = high1 - low1
        volatility_ok = candle_size > (close1 * 0.0005)

        strong_body = body > candle_size * 0.25

        # =========================
        # CALL SIGNAL
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
                f"Pattern: HAMMER\n"
                f"Timeframe: 1min"
            )

        # =========================
        # PUT SIGNAL
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
                f"Pattern: SHOOTING STAR\n"
                f"Timeframe: 1min"
            )

        return None

    except Exception as e:
        return f"❌ ERROR: {str(e)}"

# =========================
# BOT LOOP
# =========================
def bot_loop():
    while True:
        try:
            for pair in PAIRS:
                result = analyze_pair(pair)
                if result and not result.startswith("❌"):
                    send_telegram(result)
                time.sleep(3)

        except Exception as e:
            send_telegram(f"❌ BOT ERROR: {str(e)}")

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
    return "TEST OK"

@app.route("/signal")
def signal():
    messages = []

    for pair in PAIRS:
        result = analyze_pair(pair)
        if result:
            send_telegram(result)
            messages.append(result)

    return "\n\n".join(messages) if messages else "NO SIGNAL"

# =========================
# START BOT
# =========================
if __name__ == "__main__":
    thread = Thread(target=bot_loop, daemon=True)
    thread.start()

    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
