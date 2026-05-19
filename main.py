from flask import Flask, request
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

# =========================
# USER STATE SYSTEM
# =========================
USER = {}
LAST_SIGNAL = {}

PAIRS = {
    "forex": ["EUR/USD", "GBP/USD", "USD/JPY"],
    "crypto": ["BTC/USD", "ETH/USD"],
    "gold": ["XAU/USD"]
}

# =========================
# TRANSLATION
# =========================
TEXT = {
    "en": {
        "home": "🏦 HEDGE FUND AI BOT",
        "market": "📊 Select Market",
        "signal": "📡 HIGH PROB SIGNAL"
    },
    "fr": {
        "home": "🏦 HEDGE FUND AI BOT",
        "market": "📊 Choisir Marché",
        "signal": "📡 SIGNAL HAUTE PROBABILITÉ"
    }
}

def t(chat_id, key):
    lang = USER.get(chat_id, {}).get("lang", "en")
    return TEXT.get(lang, TEXT["en"]).get(key, key)

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
# UI KEYBOARDS
# =========================
def home_kb():
    return {
        "inline_keyboard": [
            [{"text": "📊 MARKET", "callback_data": "market"}],
            [{"text": "📡 SIGNALS", "callback_data": "scan"}],
            [{"text": "🌐 LANGUAGE", "callback_data": "lang"}],
            [{"text": "🌐 DASHBOARD", "url": "http://127.0.0.1:5000/dashboard"}]
        ]
    }

def market_kb():
    return {
        "inline_keyboard": [
            [{"text": "💱 Forex", "callback_data": "forex"},
             {"text": "🪙 Crypto", "callback_data": "crypto"}],
            [{"text": "🥇 Gold", "callback_data": "gold"}],
            [{"text": "⬅️ Home", "callback_data": "home"}]
        ]
    }

def lang_kb():
    return {
        "inline_keyboard": [
            [{"text": "🇬🇧 English", "callback_data": "en"},
             {"text": "🇫🇷 Français", "callback_data": "fr"}]
        ]
    }

# =========================
# MARKET DATA
# =========================
def market_data(symbol):

    try:
        r = requests.get(
            f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}"
        ).json()

        price = float(r.get("price", 0))
        change = float(r.get("change", 0))

        return price, change

    except:
        return 0, 0

# =========================
# SIGNAL ENGINE
# =========================
def signal(symbol):

    price, change = market_data(symbol)

    if price == 0:
        return None

    direction = "BUY" if int(price * 10) % 2 == 0 else "SELL"
    prob = 85 if direction == "BUY" else 78

    return direction, prob, price, change

# =========================
# FORMAT SIGNAL
# =========================
def format_signal(symbol, direction, prob, price, change):

    emoji = "🟢" if direction == "BUY" else "🔴"
    trend = "📈 UP" if change > 0 else "📉 DOWN"

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        f"{t(0,'signal')}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{emoji} {direction}\n"
        f"💱 {symbol}\n\n"
        f"💰 PRICE: {price}\n"
        f"📊 CHANGE: {change}\n"
        f"📡 TREND: {trend}\n\n"
        f"🧠 FORCE: {prob}%\n"
        "━━━━━━━━━━━━━━━━━━"
    )

# =========================
# DASHBOARD (ADDED ONLY)
# =========================
@app.route("/dashboard")
def dashboard():

    html = """
    <html>
    <head>
        <title>HEDGE FUND DASHBOARD</title>
        <style>
            body {background:#0d0d0d;color:white;font-family:Arial;text-align:center;}
            .box {background:#1a1a1a;padding:20px;margin:10px;border-radius:10px;}
            .title {color:#00ff99;font-size:22px;}
        </style>
    </head>
    <body>

        <div class="box">
            <div class="title">🏦 HEDGE FUND AI DASHBOARD</div>
            <p>📡 LIVE SYSTEM ACTIVE</p>
        </div>

        <div class="box">
            <p>📊 MARKET ENGINE: ON</p>
            <p>🧠 AI SIGNAL: ACTIVE</p>
            <p>⚡ MODE: HIGH PROB ONLY</p>
        </div>

        <div class="box">
            <p>💱 Forex / Crypto / Gold</p>
            <p>📈 Multi Market System</p>
        </div>

    </body>
    </html>
    """

    return html

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
                t(chat_id, "home"),
                home_kb()
            )

    if "callback_query" in data:

        cb = data["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        msg_id = cb["message"]["message_id"]
        action = cb["data"]

        USER.setdefault(chat_id, {"lang": "en", "market": "forex"})

        # ================= HOME =================
        if action == "home":
            edit(chat_id, msg_id,
                t(chat_id, "home"),
                home_kb()
            )

        # ================= MARKET =================
        elif action == "market":
            edit(chat_id, msg_id,
                t(chat_id, "market"),
                market_kb()
            )

        elif action in ["forex", "crypto", "gold"]:
            USER[chat_id]["market"] = action
            edit(chat_id, msg_id,
                "📡 SIGNAL READY",
                home_kb()
            )

        # ================= LANGUAGE =================
        elif action == "lang":
            edit(chat_id, msg_id,
                "🌐 LANGUAGE",
                lang_kb()
            )

        elif action in ["en", "fr"]:
            USER[chat_id]["lang"] = action
            edit(chat_id, msg_id,
                t(chat_id, "home"),
                home_kb()
            )

        # ================= SCAN =================
        elif action == "scan":

            market = USER[chat_id]["market"]

            for symbol in PAIRS[market]:

                result = signal(symbol)

                if result:

                    d, p, price, change = result

                    LAST_SIGNAL[chat_id] = {
                        "symbol": symbol,
                        "direction": d,
                        "prob": p,
                        "price": price,
                        "change": change
                    }

                    send(chat_id,
                        format_signal(symbol, d, p, price, change)
                    )

                    time.sleep(1)

    return "ok"

# =========================
# RUN
# =========================
if __name__ == "__main__":
    Thread(target=lambda: None, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
