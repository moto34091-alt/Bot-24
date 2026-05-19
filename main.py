from flask import Flask, request, jsonify, render_template
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

USER = {}
HISTORY = []

PAIRS = {
    "forex": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"],
    "crypto": ["BTC/USD", "ETH/USD", "SOL/USD"],
    "gold": ["XAU/USD"]
}

TIMEFRAMES = {
    "5min": "5min",
    "15min": "15min",
    "1h": "1h"
}

# =========================
# TELEGRAM
# =========================
def send(chat_id, text, keyboard=None):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {"chat_id": chat_id, "text": text}

    if keyboard:
        data["reply_markup"] = keyboard

    requests.post(url, json=data)

# =========================
# MARKET DATA
# =========================
def candles(symbol, tf):

    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={tf}&outputsize=60&apikey={API_KEY}"
    r = requests.get(url).json()

    if "values" not in r:
        return None

    return r["values"][::-1]

# =========================
# AI ENGINE (PRO)
# =========================
def analyze(data):

    closes = [float(c["close"]) for c in data]

    c1, c2, c3 = data[-1], data[-2], data[-3]

    close1 = float(c1["close"])
    close2 = float(c2["close"])
    close3 = float(c3["close"])
    open1 = float(c1["open"])

    ema5 = sum(closes[-5:]) / 5
    ema20 = sum(closes[-20:]) / 20
    ema50 = sum(closes[-50:]) / 50

    bullish = ema5 > ema20 > ema50
    bearish = ema5 < ema20 < ema50

    momentum_up = close1 > close2 > close3
    momentum_down = close1 < close2 < close3

    body = abs(close1 - open1)

    strong = body > (close1 * 0.002)

    return bullish, bearish, momentum_up, momentum_down, strong

# =========================
# SIGNAL ENGINE (IA + FILTER)
# =========================
def signal(symbol):

    tf = {}

    for k in TIMEFRAMES:

        data = candles(symbol, TIMEFRAMES[k])
        if not data:
            return None

        tf[k] = analyze(data)

    buy = 0
    sell = 0

    # WEIGHT SYSTEM
    if tf["5min"][0]: buy += 1
    if tf["5min"][1]: sell += 1

    if tf["15min"][0]: buy += 2
    if tf["15min"][1]: sell += 2

    if tf["1h"][0]: buy += 3
    if tf["1h"][1]: sell += 3

    if tf["5min"][2]: buy += 1
    if tf["5min"][3]: sell += 1

    if tf["5min"][4]:
        buy += 1
        sell += 1

    # ANTI FAKE SIGNAL
    if abs(buy - sell) < 2:
        return None

    total = buy + sell
    if total == 0:
        return None

    buy_p = int((buy / total) * 100)
    sell_p = int((sell / total) * 100)

    direction = None
    prob = 0

    if buy >= 7 and buy_p >= 70 and tf["1h"][0]:
        direction = "BUY"
        prob = buy_p

    elif sell >= 7 and sell_p >= 70 and tf["1h"][1]:
        direction = "SELL"
        prob = sell_p

    else:
        return None

    return direction, prob, tf, buy, sell

# =========================
# FORMAT SIGNAL
# =========================
def format(symbol, direction, prob, tf, buy, sell):

    emoji = "🟢" if direction == "BUY" else "🔴"

    bar = "█" * int(prob / 10) + "░" * (10 - int(prob / 10))

    text = ""

    for k, v in tf.items():
        state = "🟢 Bullish" if v[0] else "🔴 Bearish" if v[1] else "⚪ Neutral"
        text += f"{k.upper()} : {state}\n"

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 SNIPER AI PRO\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} {direction}\n\n"
        f"💱 {symbol}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "MULTI TIMEFRAME\n\n"
        f"{text}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"PROBABILITY: {prob}%\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"BUY {buy} / SELL {sell}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{bar} {prob}%\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "HIGH PROB CONFIRMED\n"
        "━━━━━━━━━━━━━━━━━━"
    )

# =========================
# DASHBOARD API
# =========================
@app.route("/api/signals")
def api_signals():

    market = request.args.get("market", "forex")

    res = []

    for p in PAIRS.get(market, []):

        s = signal(p)

        if s:

            d, pr, tf, b, se = s

            item = {
                "pair": p,
                "direction": d,
                "probability": pr,
                "buy": b,
                "sell": se
            }

            HISTORY.append(item)

            res.append(item)

    return jsonify(res)

# =========================
# HISTORY
# =========================
@app.route("/api/history")
def history():
    return jsonify(HISTORY[-100:])

# =========================
# DASHBOARD PAGE
# =========================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# =========================
# LOOP AUTO SIGNAL
# =========================
def loop():

    while True:

        for chat_id, u in USER.items():

            market = u.get("market", "forex")

            for p in PAIRS[market]:

                s = signal(p)

                if s:

                    d, pr, tf, b, se = s

                    send(chat_id, format(p, d, pr, tf, b, se))

                time.sleep(2)

        time.sleep(60)

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if "message" in data:

        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if chat_id not in USER:
            USER[chat_id] = {"market": "forex"}

        if text == "/start":

            send(chat_id,
                "🤖 SNIPER AI PRO SYSTEM\n\n"
                "📊 Forex / Crypto / Gold\n"
                "🧠 AI Prediction Engine\n"
                "📡 Live Signals Active"
            )

    return "ok"

# =========================
# RUN
# =========================
if __name__ == "__main__":

    Thread(target=loop, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
