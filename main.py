from flask import Flask, request
import os
import requests

app = Flask(__name__)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"]

# =========================
# HOME ROUTE (IMPORTANT)
# =========================
@app.route("/")
def home():
    return "BOT ONLINE OK"

# =========================
# TELEGRAM SEND
# =========================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

# =========================
# SIMPLE MARKET ANALYSIS
# =========================
def analyze(symbol):

    try:
        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={symbol}"
            f"&interval=1min"
            f"&outputsize=20"
            f"&apikey={API_KEY}"
        )

        data = requests.get(url).json()

        if "values" not in data:
            return None

        candles = data["values"][::-1]

        close = float(candles[-1]["close"])
        open_ = float(candles[-1]["open"])
        prev_close = float(candles[-2]["close"])

        # =========================
        # TREND SIMPLE
        # =========================
        if close > prev_close:
            return f"📈 CALL SIGNAL\nPair: {symbol}"
        elif close < prev_close:
            return f"📉 PUT SIGNAL\nPair: {symbol}"

        return None

    except:
        return None

# =========================
# SCAN ALL PAIRS
# =========================
def scan_market():
    signals = []

    for p in PAIRS:
        sig = analyze(p)
        if sig:
            signals.append(sig)

    return signals

# =========================
# WEBHOOK TELEGRAM
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id,
                "🤖 BOT PRO ACTIF\n\n"
                "/signal → voir les signaux\n"
                "/status → statut bot"
            )

        elif text == "/signal":
            signals = scan_market()
            send_message(chat_id, "\n\n".join(signals) if signals else "NO SIGNAL")

        elif text == "/status":
            send_message(chat_id, "✅ BOT ONLINE")

    return "ok"

# =========================
# START SERVER (RAILWAY FIX)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
