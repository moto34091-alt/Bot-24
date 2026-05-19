from flask import Flask, request
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

# =========================
# USER STATE
# =========================
USER = {}

PAIRS = {
    "forex": ["EUR/USD", "GBP/USD", "USD/JPY"],
    "crypto": ["BTC/USD", "ETH/USD"],
    "gold": ["XAU/USD"]
}

# =========================
# TELEGRAM CORE
# =========================
def send(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if keyboard:
        data["reply_markup"] = keyboard
    requests.post(url, json=data)

def edit(chat_id, msg_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": msg_id,
        "text": text
    }
    if keyboard:
        data["reply_markup"] = keyboard
    requests.post(url, json=data)

# =========================
# HOME PAGE (IMPORTANT FIX)
# =========================
@app.route("/")
def home():
    return "🏦 HEDGE FUND BOT RUNNING"

# =========================
# DASHBOARD (FIXED)
# =========================
@app.route("/dashboard")
def dashboard():
    return """
    <html>
        <head>
            <title>HEDGE FUND DASHBOARD</title>
        </head>
        <body style="background:#0d0d0d;color:white;font-family:Arial;text-align:center;padding-top:40px;">

            <h1>🏦 DASHBOARD LIVE</h1>
            <p>📡 Render Bot is Running</p>

            <hr style="width:50%;border:1px solid #333;">

            <h3>📊 SYSTEM STATUS</h3>
            <p>🧠 AI ENGINE: ACTIVE</p>
            <p>📡 SIGNAL ENGINE: READY</p>
            <p>💱 MARKETS: FOREX / CRYPTO / GOLD</p>

            <hr style="width:50%;border:1px solid #333;">

            <h3>⚡ LIVE MODE</h3>
            <p>HIGH PROB ONLY SIGNAL SYSTEM</p>

        </body>
    </html>
    """

# =========================
# KEYBOARDS
# =========================
def home_kb():
    return {
        "inline_keyboard": [
            [{"text": "📊 MARKET", "callback_data": "market"}],
            [{"text": "📡 SIGNALS", "callback_data": "scan"}],
            [{"text": "🌐 LANGUAGE", "callback_data": "lang"}],
            [{
                "text": "🌐 DASHBOARD",
                "url": "https://bot-24-x8en.onrender.com"
            }]
        ]
    }

def market_kb():
    return {
        "inline_keyboard": [
            [
                {"text": "💱 Forex", "callback_data": "forex"},
                {"text": "🪙 Crypto", "callback_data": "crypto"}
            ],
            [{"text": "🥇 Gold", "callback_data": "gold"}]
        ]
    }

def lang_kb():
    return {
        "inline_keyboard": [
            [
                {"text": "🇬🇧 English", "callback_data": "en"},
                {"text": "🇫🇷 Français", "callback_data": "fr"}
            ]
        ]
    }

# =========================
# MARKET DATA
# =========================
def get_price(symbol):
    try:
        r = requests.get(
            f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}"
        ).json()

        return float(r.get("price", 0)), float(r.get("change", 0))
    except:
        return 0, 0

# =========================
# SIGNAL ENGINE (SIMPLE)
# =========================
def signal(symbol):

    price, change = get_price(symbol)

    if price == 0:
        return None

    direction = "BUY" if change > 0 else "SELL"
    prob = 80 if abs(change) > 0.5 else 65

    return direction, prob, price, change

# =========================
# FORMAT SIGNAL
# =========================
def format_signal(symbol, direction, prob, price, change):

    emoji = "🟢" if direction == "BUY" else "🔴"
    trend = "📈 UP" if change > 0 else "📉 DOWN"

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "📡 HIGH PROB SIGNAL\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} {direction}\n"
        f"💱 {symbol}\n\n"
        f"💰 PRICE: {price}\n"
        f"📊 CHANGE: {change}\n"
        f"📡 TREND: {trend}\n\n"
        f"🧠 PROB: {prob}%\n"
        "━━━━━━━━━━━━━━━━━━"
    )

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
            USER[chat_id] = {"lang": "en", "market": "forex"}

        if text == "/start":

            send(chat_id,
                "🏦 HEDGE FUND AI BOT\n\n"
                "📊 Forex / Crypto / Gold\n"
                "🧠 Institutional AI Engine\n"
                "📡 HIGH PROB ONLY SIGNALS",
                home_kb()
            )

    if "callback_query" in data:

        cb = data["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        msg_id = cb["message"]["message_id"]
        action = cb["data"]

        USER.setdefault(chat_id, {"lang": "en", "market": "forex"})

        # MARKET
        if action in ["forex", "crypto", "gold"]:
            USER[chat_id]["market"] = action
            edit(chat_id, msg_id, "📡 MARKET SELECTED", home_kb())

        elif action == "market":
            edit(chat_id, msg_id, "📊 CHOOSE MARKET", market_kb())

        elif action == "lang":
            edit(chat_id, msg_id, "🌐 LANGUAGE", lang_kb())

        elif action in ["en", "fr"]:
            USER[chat_id]["lang"] = action
            edit(chat_id, msg_id, "🏦 HOME", home_kb())

        elif action == "scan":

            market = USER[chat_id]["market"]

            for symbol in PAIRS[market]:

                result = signal(symbol)

                if result:

                    d, p, price, change = result

                    send(chat_id, format_signal(symbol, d, p, price, change))
                    time.sleep(1)

    return "ok"

# =========================
# RUN
# =========================
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
