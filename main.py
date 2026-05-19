from flask import Flask, request
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

CHAT_ID = None

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "BTC/USD",
    "ETH/USD"
]

TIMEFRAMES = {
    "5min": "5min",
    "15min": "15min",
    "1h": "1h"
}

# =========================
# TELEGRAM
# =========================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# =========================
# DATA
# =========================
def get_candles(symbol, tf):

    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={tf}&outputsize=50&apikey={API_KEY}"
    r = requests.get(url).json()

    if "values" not in r:
        return None

    return r["values"][::-1]

# =========================
# AI CORE (SCORE ENGINE)
# =========================
def analyze_tf(candles):

    closes = [float(c["close"]) for c in candles]

    c1 = candles[-1]
    c2 = candles[-2]
    c3 = candles[-3]

    close1 = float(c1["close"])
    close2 = float(c2["close"])
    close3 = float(c3["close"])

    open1 = float(c1["open"])

    ema_fast = sum(closes[-5:]) / 5
    ema_slow = sum(closes[-20:]) / 20

    bullish = ema_fast > ema_slow
    bearish = ema_fast < ema_slow

    momentum_up = close1 > close2 > close3
    momentum_down = close1 < close2 < close3

    score = 0

    if bullish:
        score += 2
    if bearish:
        score -= 2

    if momentum_up:
        score += 2
    if momentum_down:
        score -= 2

    if close1 > open1:
        score += 1
    else:
        score -= 1

    return {
        "bullish": bullish,
        "bearish": bearish,
        "score": score
    }

# =========================
# MULTI TF ENGINE
# =========================
def high_probability(symbol):

    tf_data = {}

    for tf_name, tf in TIMEFRAMES.items():

        candles = get_candles(symbol, tf)

        if not candles:
            return None

        tf_data[tf_name] = analyze_tf(candles)

    buy = 0
    sell = 0

    # =========================
    # CONFLUENCE WEIGHT
    # =========================
    if tf_data["5min"]["bullish"]:
        buy += 1
    if tf_data["5min"]["bearish"]:
        sell += 1

    if tf_data["15min"]["bullish"]:
        buy += 2
    if tf_data["15min"]["bearish"]:
        sell += 2

    if tf_data["1h"]["bullish"]:
        buy += 3
    if tf_data["1h"]["bearish"]:
        sell += 3

    total = buy + sell
    if total == 0:
        return None

    buy_prob = int((buy / total) * 100)
    sell_prob = int((sell / total) * 100)

    direction = None
    prob = 0

    if buy_prob >= 70 and tf_data["1h"]["bullish"]:
        direction = "BUY"
        prob = buy_prob

    elif sell_prob >= 70 and tf_data["1h"]["bearish"]:
        direction = "SELL"
        prob = sell_prob

    else:
        return None

    return direction, prob, tf_data

# =========================
# APP STYLE FORMAT
# =========================
def format_app(symbol, direction, prob, tf_data):

    emoji = "🟢" if direction == "BUY" else "🔴"

    bar = "█" * int(prob / 10) + "░" * (10 - int(prob / 10))

    tf_text = ""

    for tf, v in tf_data.items():

        if v["bullish"]:
            state = "🟢 Bullish"
        elif v["bearish"]:
            state = "🔴 Bearish"
        else:
            state = "⚪ Neutral"

        tf_text += f"{tf.upper():<6} {state}\n"

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "        📊 SNIPER AI PRO\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} SIGNAL: {direction}\n\n"
        f"💱 PAIR\n{symbol}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📈 MULTI TIMEFRAME\n\n"
        f"{tf_text}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🧠 PROBABILITY\n{prob}% HIGH QUALITY\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"⚡ STRENGTH\n{bar} {prob}%\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 CONCLUSION\n"
        "Multi-timeframe confluence confirmed\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⏱ 5m / 15m / 1h VALIDATED\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "      📡 SNIPER BOT\n"
        "━━━━━━━━━━━━━━━━━━"
    )

# =========================
# LOOP
# =========================
def bot_loop():

    global CHAT_ID

    while True:

        if CHAT_ID:

            for pair in PAIRS:

                result = high_probability(pair)

                if result:

                    direction, prob, tf_data = result

                    msg = format_app(pair, direction, prob, tf_data)

                    send_message(CHAT_ID, msg)

                time.sleep(2)

        time.sleep(60)

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():

    global CHAT_ID

    data = request.json

    if "message" in data:

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        CHAT_ID = chat_id

        if text == "/start":

            send_message(chat_id,
                "🤖 SNIPER AI PRO ACTIVÉ\n\n"
                "📊 Multi-Timeframe System\n"
                "🧠 High Probability Filter ON\n"
                "⏱ 5m / 15m / 1h CONFIRMATION"
            )

    return "ok"

# =========================
# RUN
# =========================
if __name__ == "__main__":

    Thread(target=bot_loop, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
