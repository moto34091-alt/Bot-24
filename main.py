from flask import Flask, request
import requests
import os
import time
from threading import Thread

# =====================================================
# FLASK
# =====================================================
app = Flask(__name__)

# =====================================================
# CONFIG
# =====================================================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

INTERVAL = "15min"

# =====================================================
# MARKETS
# =====================================================
FOREX_PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD"
]

CRYPTO_PAIRS = [
    "BTC/USD",
    "ETH/USD",
    "SOL/USD",
    "XRP/USD"
]

GOLD_PAIRS = [
    "XAU/USD"
]

# =====================================================
# MEMORY
# =====================================================
last_signals = {}

user_languages = {}

selected_market = {}

auto_signal_users = {}

# =====================================================
# TRANSLATIONS
# =====================================================
def get_text(lang, key):

    texts = {

        "fr": {
            "welcome": "🤖 SNIPER BOT ACTIVÉ\n\n💬 Sélectionnez une option:",
            "language": "🌐 Choisissez votre langue:",
            "timeframe": "⏰ Choisissez timeframe:",
            "market": "📊 Choisissez le marché:"
        },

        "en": {
            "welcome": "🤖 SNIPER BOT ACTIVATED\n\n💬 Select option:",
            "language": "🌐 Select your language:",
            "timeframe": "⏰ Choose timeframe:",
            "market": "📊 Choose market:"
        },

        "pt": {
            "welcome": "🤖 SNIPER BOT ATIVADO\n\n💬 Selecione uma opção:",
            "language": "🌐 Escolha seu idioma:",
            "timeframe": "⏰ Escolha timeframe:",
            "market": "📊 Escolha mercado:"
        },

        "sw": {
            "welcome": "🤖 SNIPER BOT IMEWASHWA\n\n💬 Chagua option:",
            "language": "🌐 Chagua lugha:",
            "timeframe": "⏰ Chagua timeframe:",
            "market": "📊 Chagua market:"
        },

        "ln": {
            "welcome": "🤖 SNIPER BOT EZO SALA\n\n💬 Pona option:",
            "language": "🌐 Pona monoko:",
            "timeframe": "⏰ Pona timeframe:",
            "market": "📊 Pona marché:"
        }
    }

    return texts.get(lang, texts["en"]).get(key, "")

# =====================================================
# TELEGRAM
# =====================================================
def send_message(chat_id, text):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    requests.post(url, json=data)

# =====================================================
# SEND MENU
# =====================================================
def send_menu(chat_id, text, keyboard):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard
    }

    requests.post(url, json=data)

# =====================================================
# EDIT MENU
# =====================================================
def edit_menu(chat_id, message_id, text, keyboard):

    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "reply_markup": keyboard
    }

    requests.post(url, json=data)

# =====================================================
# MAIN MENU
# =====================================================
def main_menu():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "🚀 Exécuter",
                    "callback_data": "execute"
                }
            ],

            [
                {
                    "text": "🌐 Language settings",
                    "callback_data": "language"
                }
            ],

            [
                {
                    "text": "❓ Aide",
                    "callback_data": "help"
                }
            ],

            [
                {
                    "text": "👨‍💻 @Mr_dflam",
                    "url": "https://t.me/Mr_dflam"
                }
            ]
        ]
    }

# =====================================================
# LANGUAGE MENU
# =====================================================
def language_menu():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "🇫🇷 Français",
                    "callback_data": "fr"
                },

                {
                    "text": "🇬🇧 English",
                    "callback_data": "en"
                }
            ],

            [
                {
                    "text": "🇵🇹 Português",
                    "callback_data": "pt"
                },

                {
                    "text": "🇨🇩 Swahili",
                    "callback_data": "sw"
                }
            ],

            [
                {
                    "text": "🇨🇩 Lingala",
                    "callback_data": "ln"
                }
            ]
        ]
    }

# =====================================================
# TIMEFRAME MENU
# =====================================================
def timeframe_menu():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "⏰ 15MIN",
                    "callback_data": "tf15"
                },

                {
                    "text": "⏰ 30MIN",
                    "callback_data": "tf30"
                }
            ]
        ]
    }

# =====================================================
# MARKET MENU
# =====================================================
def market_menu():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "💱 Forex",
                    "callback_data": "forex"
                },

                {
                    "text": "🪙 Crypto",
                    "callback_data": "crypto"
                }
            ],

            [
                {
                    "text": "🥇 Gold",
                    "callback_data": "gold"
                }
            ]
        ]
    }

# =====================================================
# SIGNAL MENU
# =====================================================
def signal_menu():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "🔍 Signal Maintenant",
                    "callback_data": "scan_now"
                }
            ],

            [
                {
                    "text": "📡 Auto Signal ON",
                    "callback_data": "auto_on_market"
                },

                {
                    "text": "🛑 Auto Signal OFF",
                    "callback_data": "auto_off_market"
                }
            ],

            [
                {
                    "text": "⬅️ Retour",
                    "callback_data": "back_main"
                }
            ]
        ]
    }

# =====================================================
# EMA
# =====================================================
def ema(prices, period):

    multiplier = 2 / (period + 1)

    value = prices[0]

    for price in prices[1:]:

        value = ((price - value) * multiplier) + value

    return value

# =====================================================
# RSI
# =====================================================
def rsi(closes, period=14):

    gains = []
    losses = []

    for i in range(1, len(closes)):

        diff = closes[i] - closes[i - 1]

        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period if gains else 0
    avg_loss = sum(losses[-period:]) / period if losses else 0

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

# =====================================================
# ANALYSE
# =====================================================
def analyze_pair(symbol):

    try:

        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={symbol}"
            f"&interval={INTERVAL}"
            f"&outputsize=100"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url).json()

        if "values" not in response:
            return None

        candles = response["values"][::-1]

        closes = [float(c["close"]) for c in candles]

        c1 = candles[-1]
        c2 = candles[-2]
        c3 = candles[-3]

        close1 = float(c1["close"])
        open1 = float(c1["open"])
        high1 = float(c1["high"])
        low1 = float(c1["low"])

        close2 = float(c2["close"])
        close3 = float(c3["close"])

        volume1 = float(c1.get("volume", 0))
        volume2 = float(c2.get("volume", 0))

        ema10 = ema(closes[-10:], 10)
        ema20 = ema(closes[-20:], 20)
        ema50 = ema(closes[-50:], 50)

        current_rsi = rsi(closes[-15:], 14)

        body = abs(close1 - open1)

        candle_range = high1 - low1

        strong_body = body > candle_range * 0.5

        momentum_up = close1 > close2 > close3
        momentum_down = close1 < close2 < close3

        high_volume = volume1 > volume2

        bullish = close1 > open1
        bearish = close1 < open1

        buy_score = 0
        sell_score = 0

        if ema10 > ema20 > ema50:
            buy_score += 2

        if ema10 < ema20 < ema50:
            sell_score += 2

        if current_rsi > 60:
            buy_score += 1

        if current_rsi < 40:
            sell_score += 1

        if bullish and strong_body:
            buy_score += 1

        if bearish and strong_body:
            sell_score += 1

        if momentum_up:
            buy_score += 2

        if momentum_down:
            sell_score += 2

        if high_volume:
            buy_score += 1
            sell_score += 1

        buy_power = int((buy_score / 7) * 100)
        sell_power = int((sell_score / 7) * 100)

        if buy_score >= 6:

            return (
                f"🟢 BUY SIGNAL\n\n"
                f"💱 Pair: {symbol}\n"
                f"📈 RSI: {round(current_rsi,2)}\n"
                f"⚡ Momentum: UP\n"
                f"📦 Volume: HIGH\n"
                f"🔥 Power: {buy_power}%\n"
                f"⏰ Timeframe: {INTERVAL}"
            )

        if sell_score >= 6:

            return (
                f"🔴 SELL SIGNAL\n\n"
                f"💱 Pair: {symbol}\n"
                f"📉 RSI: {round(current_rsi,2)}\n"
                f"⚡ Momentum: DOWN\n"
                f"📦 Volume: HIGH\n"
                f"🔥 Power: {sell_power}%\n"
                f"⏰ Timeframe: {INTERVAL}"
            )

        return None

    except Exception as e:

        return f"ERROR: {str(e)}"

# =====================================================
# AUTO SIGNAL LOOP
# =====================================================
def auto_signals():

    while True:

        try:

            for chat_id, market in auto_signal_users.items():

                pairs = []

                if market == "forex":
                    pairs = FOREX_PAIRS

                elif market == "crypto":
                    pairs = CRYPTO_PAIRS

                elif market == "gold":
                    pairs = GOLD_PAIRS

                strong_signals = []

                for pair in pairs:

                    signal = analyze_pair(pair)

                    if signal:

                        power = 0

                        try:

                            power = int(
                                signal.split("Power: ")[1].split("%")[0]
                            )

                        except:
                            power = 0

                        strong_signals.append((power, signal))

                strong_signals.sort(reverse=True)

                top_signals = strong_signals[:2]

                for power, signal in top_signals:

                    if signal not in last_signals:

                        send_message(chat_id, signal)

                        last_signals[signal] = time.time()

                        time.sleep(1)

            current = time.time()

            expired = []

            for sig, t in last_signals.items():

                if current - t > 3600:
                    expired.append(sig)

            for sig in expired:
                del last_signals[sig]

        except Exception as e:

            print(e)

        time.sleep(300)

# =====================================================
# HOME
# =====================================================
@app.route("/")
def home():

    return "SNIPER BOT ONLINE"

# =====================================================
# WEBHOOK
# =====================================================
@app.route("/webhook", methods=["POST"])
def webhook():

    global INTERVAL

    data = request.get_json()

    # =================================================
    # MESSAGE
    # =================================================
    if "message" in data:

        message = data["message"]

        chat_id = message["chat"]["id"]

        text = message.get("text", "")

        if text == "/start":

            lang = user_languages.get(chat_id, "en")

            send_menu(
                chat_id,
                get_text(lang, "welcome"),
                main_menu()
            )

    # =================================================
    # CALLBACK
    # =================================================
    if "callback_query" in data:

        callback = data["callback_query"]

        chat_id = callback["message"]["chat"]["id"]

        message_id = callback["message"]["message_id"]

        action = callback["data"]

        lang = user_languages.get(chat_id, "en")

        # LANGUAGE MENU
        if action == "language":

            edit_menu(
                chat_id,
                message_id,
                get_text(lang, "language"),
                language_menu()
            )

        # CHANGE LANGUAGE
        elif action in ["fr", "en", "pt", "sw", "ln"]:

            user_languages[chat_id] = action

            edit_menu(
                chat_id,
                message_id,
                get_text(action, "welcome"),
                main_menu()
            )

        # EXECUTE
        elif action == "execute":

            edit_menu(
                chat_id,
                message_id,
                get_text(lang, "timeframe"),
                timeframe_menu()
            )

        # TIMEFRAME
        elif action == "tf15":

            INTERVAL = "15min"

            edit_menu(
                chat_id,
                message_id,
                get_text(lang, "market"),
                market_menu()
            )

        elif action == "tf30":

            INTERVAL = "30min"

            edit_menu(
                chat_id,
                message_id,
                get_text(lang, "market"),
                market_menu()
            )

        # FOREX
        elif action == "forex":

            selected_market[chat_id] = "forex"

            edit_menu(
                chat_id,
                message_id,
                "💱 FOREX SÉLECTIONNÉ",
                signal_menu()
            )

        # CRYPTO
        elif action == "crypto":

            selected_market[chat_id] = "crypto"

            edit_menu(
                chat_id,
                message_id,
                "🪙 CRYPTO SÉLECTIONNÉ",
                signal_menu()
            )

        # GOLD
        elif action == "gold":

            selected_market[chat_id] = "gold"

            edit_menu(
                chat_id,
                message_id,
                "🥇 GOLD SÉLECTIONNÉ",
                signal_menu()
            )

        # SCAN NOW
        elif action == "scan_now":

            market = selected_market.get(chat_id)

            pairs = []

            if market == "forex":
                pairs = FOREX_PAIRS

            elif market == "crypto":
                pairs = CRYPTO_PAIRS

            elif market == "gold":
                pairs = GOLD_PAIRS

            strong_signals = []

            for pair in pairs:

                signal = analyze_pair(pair)

                if signal:

                    power = 0

                    try:

                        power = int(
                            signal.split("Power: ")[1].split("%")[0]
                        )

                    except:
                        power = 0

                    strong_signals.append((power, signal))

            strong_signals.sort(reverse=True)

            top_signals = strong_signals[:3]

            if len(top_signals) == 0:

                send_message(
                    chat_id,
                    "❌ Aucun signal fort"
                )

            else:

                for power, signal in top_signals:

                    send_message(chat_id, signal)

                    time.sleep(1)

        # AUTO ON
        elif action == "auto_on_market":

            market = selected_market.get(chat_id)

            auto_signal_users[chat_id] = market

            send_message(
                chat_id,
                f"✅ AUTO SIGNAL ACTIVÉ : {market.upper()}"
            )

        # AUTO OFF
        elif action == "auto_off_market":

            if chat_id in auto_signal_users:
                del auto_signal_users[chat_id]

            send_message(
                chat_id,
                "🛑 AUTO SIGNAL ARRÊTÉ"
            )

        # BACK
        elif action == "back_main":

            edit_menu(
                chat_id,
                message_id,
                get_text(lang, "welcome"),
                main_menu()
            )

        # HELP
        elif action == "help":

            send_message(
                chat_id,
                "❓ AIDE\n\n"
                "🚀 Exécuter → Scanner marché\n"
                "📡 Auto Signal intelligent\n"
                "💱 Forex + Crypto + Gold\n"
                "⏰ 15MIN et 30MIN\n"
                "📊 RSI + Momentum + Volume"
            )

    return "ok"

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":

    thread = Thread(target=auto_signals)

    thread.daemon = True

    thread.start()

    PORT = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=PORT
        )
