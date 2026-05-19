from flask import Flask
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("TWELVE_API_KEY")

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]
INTERVAL = "1min"

# =========================
# ANTI SPAM (PRO FEATURE)
# =========================
last_signal_time = {}

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# =========================
# EMA
# =========================
def ema(prices, period):
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]:
        e = p * k + e * (1 - k)
    return e

# =========================
# RSI PRO
# =========================
def rsi(closes):
    gains, losses = [], []

    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain = sum(gains[-14:]) / 14 if gains else 0
    avg_loss = sum(losses[-14:]) / 14 if losses else 0

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =========================
# COOLDOWN CHECK
# =========================
def can_send(symbol):
    now = time.time()
    if symbol in last_signal_time and now - last_signal_time[symbol] < 90:
        return False
    last_signal_time[symbol] = now
    return True

# =========================
# ANALYSE PRO
# =========================
def analyze(symbol):

    try:
        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={symbol}"
            f"&interval={INTERVAL}"
            f"&outputsize=40"
            f"&apikey={API_KEY}"
        )

        data = requests.get(url).json()
        if "values" not in data:
            return None

        candles = data["values"][::-1]

        close = float(candles[-1]["close"])
        open_ = float(candles[-1]["open"])
        high = float(candles[-1]["high"])
        low = float(candles[-1]["low"])

        closes = [float(c["close"]) for c in candles]

        ema10 = ema(closes[-10:], 10)
        ema20 = ema(closes[-20:], 20)
        r = rsi(closes[-15:])

        # =========================
        # TREND
        # =========================
        trend_up = close > ema20
        trend_down = close < ema20

        # =========================
        # PRICE ACTION PRO
        # =========================
        body = abs(close - open_)
        range_ = high - low

        bullish = close > open_
        bearish = close < open_

        rejection_buy = (low - min(close, open_)) > body * 1.2 and bullish
        rejection_sell = (high - max(close, open_)) > body * 1.2 and bearish

        # =========================
        # VOLATILITY FILTER
        # =========================
        volatility_ok = range_ > close * 0.00025

        # =========================
        # SCORE SYSTEM PRO
        # =========================
        call_score = 0
        put_score = 0

        # trend
        if trend_up:
            call_score += 1
        if trend_down:
            put_score += 1

        # RSI zone (PRO logic)
        if r > 50:
            call_score += 1
        if r < 50:
            put_score += 1

        # price action
        if rejection_buy:
            call_score += 2
        if rejection_sell:
            put_score += 2

        # volatility
        if volatility_ok:
            call_score += 1
            put_score += 1

        # =========================
        # FINAL SIGNAL FILTER
        # =========================
        if call_score >= 4 and can_send(symbol):
            return (
                f"📈 PRO CALL SIGNAL\n\n"
                f"Pair: {symbol}\n"
                f"RSI: {round(r,2)}\n"
                f"Score: {call_score}/5\n"
                f"TF: 1min"
            )

        if put_score >= 4 and can_send(symbol):
            return (
                f"📉 PRO PUT SIGNAL\n\n"
                f"Pair: {symbol}\n"
                f"RSI: {round(r,2)}\n"
                f"Score: {put_score}/5\n"
                f"TF: 1min"
            )

        return None

    except Exception as e:
        return f"❌ ERROR: {str(e)}"

# =========================
# LOOP PRO
# =========================
def loop():
    while True:
        for p in PAIRS:
            res = analyze(p)

            if res and not res.startswith("❌"):
                send_telegram(res)

            time.sleep(2)

        time.sleep(40)

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return "BOT PRO TRADING ONLINE"

@app.route("/test")
def test():
    send_telegram("✅ PRO BOT TEST OK")
    return "OK"

@app.route("/signal")
def signal():
    out = []

    for p in PAIRS:
        r = analyze(p)
        if r:
            send_telegram(r)
            out.append(r)

    return "\n\n".join(out) if out else "NO SIGNAL"

# =========================
# START
# =========================
if __name__ == "__main__":
    Thread(target=loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
