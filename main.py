from flask import Flask, request
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

USER = {}
STATE = {}

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
# UI SCREENS
# =========================
def screen_home():
    return {
        "inline_keyboard": [
            [{"text": "📊 Exécuter", "callback_data": "market"}],
            [{"text": "📡 Auto Signal", "callback_data": "auto"}],
            [{"text": "🌐 Langue", "callback_data": "lang"}]
        ]
    }

def screen_market():
    return {
        "inline_keyboard": [
            [{"text": "💱 Forex", "callback_data": "m_forex"},
             {"text": "🪙 Crypto", "callback_data": "m_crypto"}],
            [{"text": "🥇 Gold", "callback_data": "m_gold"}],
            [{"text": "⬅️ Back", "callback_data": "home"}]
        ]
    }

def screen_signal():
    return {
        "inline_keyboard": [
            [{"text": "🔄 Scan Signal", "callback_data": "scan"}],
            [{"text": "⬅️ Market", "callback_data": "market"}],
            [{"text": "🏠 Home", "callback_data": "home"}]
        ]
    }

def dashboard_button():

    return {
        "inline_keyboard": [
            [{
                "text": "📊 OPEN DASHBOARD",
                "url": "https://YOUR-DOMAIN.com/dashboard"
            }]
        ]
    }

# =========================
# AI SIGNAL SIMPLE (SAFE VERSION)
# =========================
def fake_signal(symbol):

    try:
        r = requests.get(
            f"https://api.twelvedata.com/price?symbol={symbol}&apikey={API_KEY}"
        ).json()

        price = float(r.get("price", 0))

        if price == 0:
            return None

        if int(price) % 2 == 0:
            return "BUY", 85
        else:
            return "SELL", 78

    except:
        return None

# =========================
# FORMAT SIGNAL
# =========================
def format_signal(symbol, direction, prob):

    bar = "█" * int(prob / 10) + "░" * (10 - int(prob / 10))
    emoji = "🟢" if direction == "BUY" else "🔴"

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "📡 HIGH PROB SIGNAL\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} {direction}\n"
        f"💱 {symbol}\n\n"
        f"🧠 Force: {prob}%\n"
        f"{bar}\n\n"
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
            USER[chat_id] = {"market": "forex"}

        # ================= START =================
        if text == "/start":

            send(
                chat_id,
                "🏦 HEDGE FUND AI BOT\n\n"
                "📊 Forex / Crypto / Gold\n"
                "🧠 Institutional AI Engine\n"
                "📡 HIGH PROB ONLY SIGNALS\n\n"
                "🌐 DASHBOARD READY",
                dashboard_button()
            )

            STATE[chat_id] = "home"

    # ================= CALLBACK =================
    if "callback_query" in data:

        cb = data["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        msg_id = cb["message"]["message_id"]
        action = cb["data"]

        STATE.setdefault(chat_id, "home")

        # HOME
        if action == "home":
            edit(chat_id, msg_id,
                "🏠 TRADING APP",
                screen_home()
            )

        # MARKET SCREEN
        elif action == "market":
            edit(chat_id, msg_id,
                "💱 SELECT MARKET",
                screen_market()
            )

        # MARKET SELECT
        elif action == "m_forex":
            USER[chat_id]["market"] = "forex"
            edit(chat_id, msg_id,
                "💱 FOREX READY\n📡 HIGH PROB ONLY",
                screen_signal()
            )

        elif action == "m_crypto":
            USER[chat_id]["market"] = "crypto"
            edit(chat_id, msg_id,
                "🪙 CRYPTO READY\n📡 HIGH PROB ONLY",
                screen_signal()
            )

        elif action == "m_gold":
            USER[chat_id]["market"] = "gold"
            edit(chat_id, msg_id,
                "🥇 GOLD READY\n📡 HIGH PROB ONLY",
                screen_signal()
            )

        # SCAN SIGNAL
        elif action == "scan":

            market = USER[chat_id]["market"]

            for symbol in PAIRS[market]:

                result = fake_signal(symbol)

                if result:

                    d, p = result

                    send(chat_id, format_signal(symbol, d, p))

                    time.sleep(1)

    return "ok"

# =========================
# LOOP (OPTIONAL)
# =========================
def loop():
    while True:
        time.sleep(10)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    Thread(target=loop, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
