from flask import Flask, request
import requests
import os
import time

app = Flask(__name__)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]

# =========================
# TELEGRAM SEND
# =========================
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(url, json=payload)

# =========================
# MENU
# =========================
def menu():
    return {
        "inline_keyboard": [
            [{"text": "📊 SIGNALS", "callback_data": "signals"}],
            [{"text": "📈 STATUS", "callback_data": "status"}],
            [{"text": "💱 PAIRS", "callback_data": "pairs"}]
        ]
    }

# =========================
# MARKET DATA
# =========================
def get_data(symbol):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=20&apikey={API_KEY}"
    return requests.get(url).json()

# =========================
# SIMPLE PRO SIGNAL ENGINE
# =========================
def analyze(symbol):

    try:
        data = get_data(symbol)

        if "values" not in data:
            return None

        candles = data["values"][::-1]

        close = float(candles[-1]["close"])
        open_ = float(candles[-1]["open"])
        high = float(candles[-1]["high"])
        low = float(candles[-1]["low"])

        prev_close = float(candles[-2]["close"])

        body = abs(close - open_)
        range_ = high - low

        trend_up = close > prev_close
        trend_down = close < prev_close

        volatility = range_ > close * 0.0003

        call_score = 0
        put_score = 0

        # trend
        if trend_up:
            call_score += 1
        if trend_down:
            put_score += 1

        # momentum
        if close > open_:
            call_score += 1
        else:
            put_score += 1

        # volatility filter
        if volatility:
            call_score += 1
            put_score += 1

        # signal rules
        if call_score >= 3:
            return f"📈 CALL SIGNAL\nPair: {symbol}\nScore: {call_score}/3"

        if put_score >= 3:
            return f"📉 PUT SIGNAL\nPair: {symbol}\nScore: {put_score}/3"

        return None

    except:
        return None

# =========================
# SIGNALS MULTI PAIRS
# =========================
def scan_market():
    results = []

    for p in PAIRS:
        sig = analyze(p)
        if sig:
            results.append(sig)

    return results

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    # MESSAGE
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "🤖 <b>BOT PRO ACTIF</b>\nChoisis une option :", menu())

        elif text == "/signal":
            signals = scan_market()
            send_message(chat_id, "\n\n".join(signals) if signals else "NO SIGNAL")

        elif text == "/status":
            send_message(chat_id, "✅ BOT ONLINE & RUNNING")

    # CALLBACK BUTTONS
    if "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        action = data["callback_query"]["data"]

        if action == "signals":
            signals = scan_market()
            send_message(chat_id, "\n\n".join(signals) if signals else "NO SIGNAL")

        elif action == "status":
            send_message(chat_id, "✅ STATUS: ACTIVE")

        elif action == "pairs":
            send_message(chat_id, "💱 PAIRS:\nEUR/USD\nGBP/USD\nUSD/JPY")

    return "ok"

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return "BOT PRO ONLINE"

# =========================
# START
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
