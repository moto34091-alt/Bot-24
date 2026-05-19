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

PAIRS = {
    "forex": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"],
    "crypto": ["BTC/USD", "ETH/USD", "SOL/USD"],
    "gold": ["XAU/USD"]
}

TF = {
    "5m": "5min",
    "15m": "15min",
    "1h": "1h"
}

# =========================
# TELEGRAM SEND
# =========================
def send(chat_id, text, keyboard=None):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    requests.post(url, json=data)

# =========================
# DATA FETCH
# =========================
def candles(symbol, tf):

    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={tf}&outputsize=50&apikey={API_KEY}"
    r = requests.get(url).json()

    if "values" not in r:
        return None

    return r["values"][::-1]

# =========================
# AI SCORE ENGINE
# =========================
def score(data):

    closes = [float(c["close"]) for c in data]

    c1, c2, c3 = data[-1], data[-2], data[-3]

    close1 = float(c1["close"])
    close2 = float(c2["close"])
    close3 = float(c3["close"])
    open1 = float(c1["open"])

    ema5 = sum(closes[-5:]) / 5
    ema20 = sum(closes[-20:]) / 20
    ema50 = sum(closes[-50:]) / 50

    trend_up = ema5 > ema20 > ema50
    trend_down = ema5 < ema20 < ema50

    momentum_up = close1 > close2 > close3
    momentum_down = close1 < close2 < close3

    s = 0

    if trend_up:
        s += 35
    if trend_down:
        s -= 35

    if momentum_up:
        s += 25
    if momentum_down:
        s -= 25

    if close1 > open1:
        s += 10
    else:
        s -= 10

    return s

# =========================
# SIGNAL ENGINE
# =========================
def signal(symbol):

    d5 = candles(symbol, TF["5m"])
    d15 = candles(symbol, TF["15m"])
    d1h = candles(symbol, TF["1h"])

    if not d5 or not d15 or not d1h:
        return None

    s5 = score(d5)
    s15 = score(d15)
    s1h = score(d1h)

    total = (s5 * 1) + (s15 * 2) + (s1h * 3)

    prob = min(98, abs(total))

    if total >= 90 and s1h > 0:
        return "BUY", prob

    if total <= -90 and s1h < 0:
        return "SELL", prob

    return None

# =========================
# FORMAT SIGNAL
# =========================
def format_signal(symbol, direction, prob):

    emoji = "🟢" if direction == "BUY" else "🔴"

    bar = "█" * int(prob / 10) + "░" * (10 - int(prob / 10))

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🏦 HEDGE FUND AI BOT\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} {direction}\n\n"
        f"💱 {symbol}\n\n"
        f"🧠 PROBABILITY: {prob}%\n\n"
        f"{bar}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 MULTI TIMEFRAME (5m / 15m / 1h)\n"
        "━━━━━━━━━━━━━━━━━━"
    )

# =========================
# API SIGNALS (DASHBOARD)
# =========================
@app.route("/api/signals")
def api_signals():

    market = request.args.get("market", "forex")

    res = []

    for p in PAIRS.get(market, []):

        s = signal(p)

        if s:

            d, pr = s

            res.append({
                "pair": p,
                "direction": d,
                "probability": pr
            })

    return jsonify(res)

# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

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
                "🏦 HEDGE FUND AI BOT\n\n"
                "📊 Forex / Crypto / Gold\n"
                "🧠 Institutional AI Engine\n"
                "📡 HIGH PROB ONLY SIGNALS\n\n"
                "🌐 DASHBOARD:\n"
                "👉 /dashboard (web browser)"
            )

    return "ok"

# =========================
# AUTO LOOP
# =========================
def loop():

    while True:

        for chat_id in USER.keys():

            market = USER[chat_id]["market"]

            for p in PAIRS[market]:

                s = signal(p)

                if s:

                    d, pr = s

                    send(chat_id, format_signal(p, d, pr))

                time.sleep(1)

        time.sleep(60)

# =========================
# RUN
# =========================
if __name__ == "__main__":

    Thread(target=loop, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
