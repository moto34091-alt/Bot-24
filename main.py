from flask import Flask, request
import os
import requests

app = Flask(__name__)

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():
    return "BOT ONLINE OK"

# =========================
# START ROUTE (WEB)
# =========================
@app.route("/start")
def start_page():
    return "BOT START OK"

# =========================
# STATUS ROUTE
# =========================
@app.route("/status")
def status():
    return "BOT STATUS ONLINE"

# =========================
# TELEGRAM SEND MESSAGE
# =========================
def send_message(chat_id, text):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    requests.post(url, data=data)

# =========================
# ANALYSE SIMPLE
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

        response = requests.get(url).json()

        if "values" not in response:
            return None

        candles = response["values"][::-1]

        close = float(candles[-1]["close"])
        open_ = float(candles[-1]["open"])

        previous_close = float(candles[-2]["close"])

        # =========================
        # TREND
        # =========================
        bullish = close > previous_close and close > open_
        bearish = close < previous_close and close < open_

        # =========================
        # SIGNALS
        # =========================
        if bullish:
            return (
                f"📈 CALL SIGNAL\n\n"
                f"Pair: {symbol}\n"
                f"Trend: UP\n"
                f"Timeframe: 1min"
            )

        if bearish:
            return (
                f"📉 PUT SIGNAL\n\n"
                f"Pair: {symbol}\n"
                f"Trend: DOWN\n"
                f"Timeframe: 1min"
            )

        return None

    except Exception as e:
        return f"ERROR: {str(e)}"

# =========================
# SCAN MARKET
# =========================
def scan_market():

    signals = []

    for pair in PAIRS:

        result = analyze(pair)

        if result and not result.startswith("ERROR"):
            signals.append(result)

    return signals

# =========================
# SIGNAL ROUTE
# =========================
@app.route("/signal")
def signal_route():

    signals = scan_market()

    if signals:
        return "\n\n".join(signals)

    return "NO SIGNAL"

# =========================
# TELEGRAM WEBHOOK
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    if "message" in data:

        chat_id = data["message"]["chat"]["id"]

        text = data["message"].get("text", "")

        # =========================
        # /START
        # =========================
        if text == "/start":

            send_message(
                chat_id,
                "🤖 BOT PRO ACTIF\n\n"
                "Commandes disponibles:\n"
                "/signal - Voir les signaux\n"
                "/status - Vérifier le bot"
            )

        # =========================
        # /STATUS
        # =========================
        elif text == "/status":

            send_message(
                chat_id,
                "✅ BOT ONLINE"
            )

        # =========================
        # /SIGNAL
        # =========================
        elif text == "/signal":

            signals = scan_market()

            if signals:
                send_message(
                    chat_id,
                    "\n\n".join(signals)
                )
            else:
                send_message(
                    chat_id,
                    "NO SIGNAL"
                )

    return "ok"

# =========================
# START SERVER
# =========================
if __name__ == "__main__":

    PORT = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=PORT
    )
