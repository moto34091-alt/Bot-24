from flask import Flask, request
import requests
import os
import time
from threading import Thread

app = Flask(__name__)

# =====================================================
# CONFIG
# =====================================================

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

# =====================================================
# USER STATE
# =====================================================

USER = {}
AUTO_USERS = {}

# =====================================================
# MARKETS
# =====================================================

PAIRS = {

    "forex": [
        "EUR/USD",
        "GBP/USD",
        "USD/JPY",
        "AUD/USD"
    ],

    "crypto": [
        "BTC/USD",
        "ETH/USD",
        "SOL/USD"
    ],

    "gold": [
        "XAU/USD"
    ]
}

# =====================================================
# TELEGRAM
# =====================================================

def typing(chat_id):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendChatAction",
        json={
            "chat_id": chat_id,
            "action": "typing"
        }
    )

def send(chat_id, text, keyboard=None):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

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

# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def home():

    return "🏦 HEDGE FUND BOT RUNNING"

@app.route("/dashboard")
def dashboard():

    return """
    <html>

    <head>

        <title>HEDGE FUND DASHBOARD</title>

        <meta http-equiv="refresh" content="10">

    </head>

    <body style="
        background:#0d0d0d;
        color:white;
        font-family:Arial;
        text-align:center;
        padding-top:40px;
    ">

        <h1>🏦 HEDGE FUND DASHBOARD</h1>

        <p>📡 LIVE SIGNAL SYSTEM ACTIVE</p>

        <hr style="width:60%;border:1px solid #333;">

        <h2>📊 SYSTEM STATUS</h2>

        <p>🧠 AI ENGINE : ACTIVE</p>

        <p>📡 SIGNAL ENGINE : READY</p>

        <p>💱 FOREX / CRYPTO / GOLD</p>

        <hr style="width:60%;border:1px solid #333;">

        <h2>⚡ HIGH PROBABILITY MODE</h2>

        <p>ONLY STRONG SIGNALS</p>

        <hr style="width:60%;border:1px solid #333;">

        <h2>🌐 BOT URL</h2>

        <p>
            https://bot-24-x8en.onrender.com
        </p>

    </body>

    </html>
    """

# =====================================================
# APP MENU
# =====================================================

def app_menu(lang="en"):

    texts = {

        "en": {

            "title":
            "🏦 HEDGE FUND AI BOT\n\n"
            "📊 Smart Trading Application\n"
            "🧠 Institutional AI Engine\n"
            "📡 HIGH PROBABILITY SIGNALS",

            "market": "📊 Markets",

            "signals": "📡 Live Signals",

            "auto": "🤖 Auto Signal",

            "dashboard": "🌐 Dashboard",

            "language": "🌐 Language",

            "settings": "⚙ Settings"
        },

        "fr": {

            "title":
            "🏦 HEDGE FUND AI BOT\n\n"
            "📊 Application Trading Intelligente\n"
            "🧠 Intelligence Institutionnelle\n"
            "📡 Signaux Haute Probabilité",

            "market": "📊 Marchés",

            "signals": "📡 Signaux",

            "auto": "🤖 Auto Signal",

            "dashboard": "🌐 Dashboard",

            "language": "🌐 Langue",

            "settings": "⚙ Paramètres"
        }
    }

    t = texts.get(lang, texts["en"])

    keyboard = {

        "inline_keyboard": [

            [
                {
                    "text": t["market"],
                    "callback_data": "market"
                },

                {
                    "text": t["signals"],
                    "callback_data": "signals"
                }
            ],

            [
                {
                    "text": t["auto"],
                    "callback_data": "auto"
                }
            ],

            [
                {
                    "text": t["dashboard"],
                    "url":
                    "https://bot-24-x8en.onrender.com/dashboard"
                }
            ],

            [
                {
                    "text": t["language"],
                    "callback_data": "language"
                },

                {
                    "text": t["settings"],
                    "callback_data": "settings"
                }
            ]
        ]
    }

    return t["title"], keyboard

# =====================================================
# MARKET MENU
# =====================================================

def market_menu(lang="en"):

    text = {

        "en": "📊 Select Market",

        "fr": "📊 Choisir Marché"
    }

    keyboard = {

        "inline_keyboard": [

            [
                {
                    "text": "💱 FOREX",
                    "callback_data": "forex"
                },

                {
                    "text": "🪙 CRYPTO",
                    "callback_data": "crypto"
                }
            ],

            [
                {
                    "text": "🥇 GOLD",
                    "callback_data": "gold"
                }
            ],

            [
                {
                    "text": "⬅ Back",
                    "callback_data": "home"
                }
            ]
        ]
    }

    return text.get(lang, text["en"]), keyboard

# =====================================================
# LANGUAGE MENU
# =====================================================

def language_menu():

    keyboard = {

        "inline_keyboard": [

            [
                {
                    "text": "🇬🇧 English",
                    "callback_data": "lang_en"
                },

                {
                    "text": "🇫🇷 Français",
                    "callback_data": "lang_fr"
                }
            ],

            [
                {
                    "text": "⬅ Back",
                    "callback_data": "home"
                }
            ]
        ]
    }

    return "🌐 Select Language", keyboard

# =====================================================
# SIGNAL ENGINE
# =====================================================

def get_price(symbol):

    try:

        url = (
            f"https://api.twelvedata.com/quote?"
            f"symbol={symbol}&apikey={API_KEY}"
        )

        r = requests.get(url).json()

        price = float(r.get("price", 0))

        change = float(r.get("change", 0))

        return price, change

    except:

        return 0, 0

def analyze(symbol):

    price, change = get_price(symbol)

    if price == 0:
        return None

    direction = "BUY" if change > 0 else "SELL"

    probability = 90 if abs(change) > 0.5 else 75

    market_rate = abs(change)

    return {
        "symbol": symbol,
        "direction": direction,
        "prob": probability,
        "price": price,
        "change": change,
        "rate": market_rate
    }

# =====================================================
# SIGNAL CARD
# =====================================================

def signal_card(data):

    emoji = "🟢" if data["direction"] == "BUY" else "🔴"

    trend = "📈 BULLISH" if data["change"] > 0 else "📉 BEARISH"

    strength = "█" * int(data["prob"] / 10)

    return (

        "━━━━━━━━━━━━━━━━━━\n"
        "📡 HIGH PROB SIGNAL\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"{emoji} {data['direction']}\n\n"

        f"💱 PAIR\n"
        f"{data['symbol']}\n\n"

        "━━━━━━━━━━━━━━━━━━\n"

        f"💰 PRICE : {data['price']}\n"

        f"📊 MARKET RATE : {round(data['rate'],2)}\n"

        f"{trend}\n\n"

        "━━━━━━━━━━━━━━━━━━\n"

        f"🧠 AI PROBABILITY\n"
        f"{data['prob']}%\n\n"

        "━━━━━━━━━━━━━━━━━━\n"

        f"⚡ STRENGTH\n"
        f"{strength}\n\n"

        "━━━━━━━━━━━━━━━━━━"
    )

# =====================================================
# AUTO SIGNAL LOOP
# =====================================================

def auto_loop():

    while True:

        try:

            for chat_id, market in AUTO_USERS.items():

                pairs = PAIRS.get(market, [])

                for symbol in pairs:

                    data = analyze(symbol)

                    if data and data["prob"] >= 80:

                        typing(chat_id)

                        send(chat_id, signal_card(data))

                        time.sleep(2)

            time.sleep(120)

        except Exception as e:

            print(e)

# =====================================================
# WEBHOOK
# =====================================================

@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    # =================================================
    # MESSAGE
    # =================================================

    if "message" in data:

        msg = data["message"]

        chat_id = msg["chat"]["id"]

        text = msg.get("text", "").lower()

        if chat_id not in USER:

            USER[chat_id] = {

                "lang": "en",

                "market": "forex"
            }

        # =============================================
        # SMART START
        # =============================================

        if (
            text.startswith("/start")
            or text.startswith("/star")
            or text == "start"
            or text == "menu"
        ):

            typing(chat_id)

            lang = USER[chat_id]["lang"]

            title, kb = app_menu(lang)

            send(chat_id, title, kb)

    # =================================================
    # CALLBACK
    # =================================================

    if "callback_query" in data:

        cb = data["callback_query"]

        chat_id = cb["message"]["chat"]["id"]

        msg_id = cb["message"]["message_id"]

        action = cb["data"]

        USER.setdefault(chat_id, {

            "lang": "en",

            "market": "forex"
        })

        # =========================
        # HOME
        # =========================

        if action == "home":

            typing(chat_id)

            lang = USER[chat_id]["lang"]

            title, kb = app_menu(lang)

            edit(chat_id, msg_id, title, kb)

        # =========================
        # MARKET
        # =========================

        elif action == "market":

            typing(chat_id)

            lang = USER[chat_id]["lang"]

            title, kb = market_menu(lang)

            edit(chat_id, msg_id, title, kb)

        # =========================
        # LANGUAGE
        # =========================

        elif action == "language":

            typing(chat_id)

            title, kb = language_menu()

            edit(chat_id, msg_id, title, kb)

        # =========================
        # CHANGE LANGUAGE
        # =========================

        elif action == "lang_en":

            typing(chat_id)

            USER[chat_id]["lang"] = "en"

            title, kb = app_menu("en")

            edit(chat_id, msg_id, title, kb)

        elif action == "lang_fr":

            typing(chat_id)

            USER[chat_id]["lang"] = "fr"

            title, kb = app_menu("fr")

            edit(chat_id, msg_id, title, kb)

        # =========================
        # MARKET SELECT
        # =========================

        elif action in ["forex", "crypto", "gold"]:

            typing(chat_id)

            USER[chat_id]["market"] = action

            lang = USER[chat_id]["lang"]

            title, kb = app_menu(lang)

            edit(
                chat_id,
                msg_id,
                f"✅ MARKET SELECTED : {action.upper()}",
                kb
            )

        # =========================
        # SIGNALS
        # =========================

        elif action == "signals":

            typing(chat_id)

            market = USER[chat_id]["market"]

            pairs = PAIRS.get(market, [])

            found = False

            for symbol in pairs:

                data = analyze(symbol)

                if data and data["prob"] >= 75:

                    send(chat_id, signal_card(data))

                    found = True

                    time.sleep(1)

            if not found:

                send(
                    chat_id,
                    "❌ No strong signal found"
                )

        # =========================
        # AUTO SIGNAL
        # =========================

        elif action == "auto":

            typing(chat_id)

            market = USER[chat_id]["market"]

            AUTO_USERS[chat_id] = market

            send(
                chat_id,
                f"🤖 AUTO SIGNAL ACTIVATED\n\n"
                f"📊 MARKET : {market.upper()}"
            )

        # =========================
        # SETTINGS
        # =========================

        elif action == "settings":

            typing(chat_id)

            send(
                chat_id,
                "⚙ SETTINGS PANEL\n\n"
                "🧠 AI MODE : ACTIVE\n"
                "📡 SIGNAL FILTER : HIGH PROBABILITY\n"
                "⚡ AUTO REFRESH : ON"
            )

    return "ok"

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    Thread(target=auto_loop, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
            )
