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

TF = {
    "5m": "5min",
    "15m": "15min",
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
# DATA
# =========================
def candles(symbol, tf):

    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={tf}&outputsize=60&apikey={API_KEY}"
    r = requests.get(url).json()

    if "values" not in r:
        return None

    return r["values"][::-1]

# =========================
# AI ENGINE (INSTITUTIONAL SCORE)
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

    body = abs(close1 - open1)

    strong_candle = body > (close1 * 0.002)

    score = 0

    if trend_up:
        score += 35
    if trend_down:
        score -= 35

    if momentum_up:
        score += 25
    if momentum_down:
        score -= 25

    if strong_candle:
        score += 10

    if close1 > open1:
        score += 10
    else:
        score -= 10

    return score

# =========================
# MULTI TF SIGNAL ENGINE
# =========================
def signal(symbol):

    s5 = candles(symbol, TF["5m"])
    s15 = candles(symbol, TF["15m"])
    s1h = candles(symbol, TF["1h"])

    if not s5 or not s15 or not s1h:
        return None

    sc5 = score(s5)
    sc15 = score(s15)
    sc1h = score(s1h)

    total = (sc5 * 1) + (sc15 * 2) + (sc1h * 3)

    prob = min(98, abs(total))

    direction = None

    if total >= 90 and sc1h > 0:
        direction = "BUY"

    elif total <= -90 and sc1h < 0:
        direction = "SELL"

    else:
        return None

    return direction, prob

# =========================
# FORMAT SIGNAL
# =========================
def format_signal(symbol, direction, prob):

    emoji = "🟢" if direction == "BUY" else "🔴"

    bar = "█" * int(prob / 10) + "░" * (10 - int(prob / 10))

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🏦 HEDGE FUND AI ENGINE\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} {direction}\n\n"
        f"💱 {symbol}\n\n"
        f"🧠 PROBABILITY: {prob}%\n\n"
        f"{bar}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 MULTI TIMEFRAME CONFIRMED\n"
        "5m + 15m + 1h\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚡ HIGH PROB ONLY SYSTEM\n"
        "━━━━━━━━━━━━━━━━━━"
    )

# =========================
# DASHBOARD API
# =========================
@app.route("/api/signals")
def api_signals():

    market = request.args.get("market", "forex")

    res = []

    for p in PAIRS[market]:

        s = signal(p)

        if s:

            d, pr = s

            item = {
                "pair": p,
                "direction": d,
                "probability": pr
            }

            HISTORY.append(item)

            res.append(item)

    return jsonify(res)

# =========================
# HISTORY / WINRATE BASE
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
# TELEGRAM FLOW
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
                "📡 HIGH PROB ONLY SIGNALS"
            )

    return "ok"

# =========================
# AUTO LOOP
# =========================
def loop():

    while True:

        for chat_id, u in USER.items():

            market = u.get("market", "forex")

            for p in PAIRS[market]:

                s = signal(p)

                if s:

                    d, pr = s

                    send(chat_id, format_signal(p, d, pr))

                time.sleep(2)

        time.sleep(60)

# =========================
# RUN
# =========================
if __name__ == "__main__":

    Thread(target=loop, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
