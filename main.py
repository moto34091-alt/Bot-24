from flask import Flask, request
import requests
import os
import time
from threading import Thread

# =====================================================
# FLASK APP
# =====================================================
app = Flask(__name__)

# =====================================================
# CONFIG
# =====================================================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")

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

ALL_PAIRS = FOREX_PAIRS + CRYPTO_PAIRS + GOLD_PAIRS

# =====================================================
# MEMORY
# =====================================================
last_signals = {}

auto_signal_enabled = True

# =====================================================
# TELEGRAM MESSAGE
# =====================================================
def send_message(text, chat_id):

    try:

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        data = {
            "chat_id": chat_id,
            "text": text
        }

        requests.post(url, json=data)

    except Exception as e:
        print(e)

# =====================================================
# TELEGRAM MENU
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
                    "text": "📡 Auto Signal ON",
                    "callback_data": "auto_on"
                },

                {
                    "text": "🛑 Auto Signal OFF",
                    "callback_data": "auto_off"
                }
            ],

            [
                {
                    "text": "👨‍💻 @Mr_dflam",
                    "url": "https://t.me/Mr_dflam"
                }
            ],

            [
                {
                    "text": "❓ Aide",
                    "callback_data": "help"
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
# FOREX MENU
# =====================================================
def forex_menu():

    keyboard = []

    for pair in FOREX_PAIRS:

        keyboard.append([
            {
                "text": pair,
                "callback_data": pair
            }
        ])

    return {
        "inline_keyboard": keyboard
    }

# =====================================================
# CRYPTO MENU
# =====================================================
def crypto_menu():

    keyboard = []

    for pair in CRYPTO_PAIRS:

        keyboard.append([
            {
                "text": pair,
                "callback_data": pair
            }
        ])

    return {
        "inline_keyboard": keyboard
    }

# =====================================================
# GOLD MENU
# =====================================================
def gold_menu():

    keyboard = []

    for pair in GOLD_PAIRS:

        keyboard.append([
            {
                "text": pair,
                "callback_data": pair
            }
        ])

    return {
        "inline_keyboard": keyboard
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
# ANALYSE PAIR
# =====================================================
def analyze_pair(symbol):

    try:

        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={symbol}"
            f"&interval={INTERVAL}"
            f"&outputsize=50"
            f"&apikey={API_KEY}"
        )

        response = requests.get(url).json()

        if "values" not in response:
            return None

        candles = response["values"][::-1]

        closes = [float(c["close"]) for c in candles]

        current = candles[-1]
        previous = candles[-2]

        close = float(current["close"])
        open_ = float(current["open"])

        prev_close = float(previous["close"])

        ema10 = ema(closes[-10:], 10)
        ema20 = ema(closes[-20:], 20)

        current_rsi = rsi(closes[-15:], 14)

        trend_up = ema10 > ema20
        trend_down = ema10 < ema20

        bullish = close > open_
        bearish = close < open_

        momentum_up = close > prev_close
        momentum_down = close < prev_close

        call_score = 0
        put_score = 0

        if trend_up:
            call_score += 1

        if trend_down:
            put_score += 1

        if current_rsi > 55:
            call_score += 1

        if current_rsi < 45:
            put_score += 1

        if bullish:
            call_score += 1

        if bearish:
            put_score += 1

        if momentum_up:
            call_score += 1

        if momentum_down:
            put_score += 1

        # =================================================
        # CALL SIGNAL
        # =================================================
        if call_score >= 3:

            return (
                f"🔥 SNIPER CALL\n\n"
                f"💱 Pair: {symbol}\n"
                f"📈 RSI: {round(current_rsi,2)}\n"
                f"🔥 Score: {call_score}/4\n"
                f"⏰ Timeframe: 15MIN"
            )

        # =================================================
        # PUT SIGNAL
        # =================================================
        if put_score >= 3:

            return (
                f"⚡ SNIPER PUT\n\n"
                f"💱 Pair: {symbol}\n"
                f"📉 RSI: {round(current_rsi,2)}\n"
                f"🔥 Score: {put_score}/4\n"
                f"⏰ Timeframe: 15MIN"
            )

        return None

    except Exception as e:

        return f"ERROR: {str(e)}"

# =====================================================
# AUTO SIGNALS
# =====================================================
def auto_signals():

    global auto_signal_enabled

    while True:

        try:

            if auto_signal_enabled:

                for pair in ALL_PAIRS:

                    signal = analyze_pair(pair)

                    if signal:

                        if signal not in last_signals:

                            send_message(signal, CHAT_ID)

                            last_signals[signal] = time.time()

            current_time = time.time()

            expired = []

            for sig, t in last_signals.items():

                if current_time - t > 3600:
                    expired.append(sig)

            for sig in expired:
                del last_signals[sig]

        except Exception as e:

            send_message(
                f"BOT ERROR:\n{str(e)}",
                CHAT_ID
            )

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

    global auto_signal_enabled

    data = request.get_json()

    # =================================================
    # MESSAGE
    # =================================================
    if "message" in data:

        message = data["message"]

        chat_id = message["chat"]["id"]

        text = message.get("text", "")

        # =============================================
        # START
        # =============================================
        if text == "/start":

            send_menu(
                chat_id,
                "🤖 SNIPER BOT ACTIVÉ\n\n💬 Select option:",
                main_menu()
            )

        # =============================================
        # STATUS
        # =============================================
        elif text == "/status":

            send_message(
                "✅ BOT ONLINE",
                chat_id
            )

        # =============================================
        # SIGNAL
        # =============================================
        elif text == "/signal":

            results = []

            for pair in ALL_PAIRS:

                result = analyze_pair(pair)

                if result:
                    results.append(result)

            if results:

                send_message(
                    "\n\n".join(results),
                    chat_id
                )

            else:

                send_message(
                    "NO SIGNAL",
                    chat_id
                )

    # =================================================
    # CALLBACK BUTTONS
    # =================================================
    if "callback_query" in data:

        callback = data["callback_query"]

        chat_id = callback["message"]["chat"]["id"]

        action = callback["data"]

        # =============================================
        # LANGUAGE
        # =============================================
        if action == "language":

            send_menu(
                chat_id,
                "🌐 Select your language:",
                language_menu()
            )

        # =============================================
        # LANGUAGES
        # =============================================
        elif action == "fr":

            send_message(
                "🇫🇷 Français activé",
                chat_id
            )

        elif action == "en":

            send_message(
                "🇬🇧 English activated",
                chat_id
            )

        elif action == "pt":

            send_message(
                "🇵🇹 Português ativado",
                chat_id
            )

        elif action == "sw":

            send_message(
                "🇨🇩 Swahili activated",
                chat_id
            )

        elif action == "ln":

            send_message(
                "🇨🇩 Lingala activé",
                chat_id
            )

        # =============================================
        # EXECUTE
        # =============================================
        elif action == "execute":

            send_menu(
                chat_id,
                "📊 Choisissez le marché :",
                market_menu()
            )

        # =============================================
        # FOREX
        # =============================================
        elif action == "forex":

            send_menu(
                chat_id,
                "💱 Forex Market",
                forex_menu()
            )

        # =============================================
        # CRYPTO
        # =============================================
        elif action == "crypto":

            send_menu(
                chat_id,
                "🪙 Crypto Market",
                crypto_menu()
            )

        # =============================================
        # GOLD
        # =============================================
        elif action == "gold":

            send_menu(
                chat_id,
                "🥇 Gold Market",
                gold_menu()
            )

        # =============================================
        # AUTO SIGNAL ON
        # =============================================
        elif action == "auto_on":

            auto_signal_enabled = True

            send_message(
                "✅ AUTO SIGNAL ACTIVÉ",
                chat_id
            )

        # =============================================
        # AUTO SIGNAL OFF
        # =============================================
        elif action == "auto_off":

            auto_signal_enabled = False

            send_message(
                "🛑 AUTO SIGNAL DÉSACTIVÉ",
                chat_id
            )

        # =============================================
        # HELP
        # =============================================
        elif action == "help":

            send_message(
                "❓ AIDE\n\n"
                "🚀 Exécuter → Scanner marché\n"
                "📡 Auto Signal → Signaux automatiques\n"
                "💱 Forex + Crypto + Gold\n"
                "🌐 Multi-langues",
                chat_id
            )

        # =============================================
        # SIGNAL PAR PAIRE
        # =============================================
        elif "/" in action:

            result = analyze_pair(action)

            if result:

                send_message(
                    result,
                    chat_id
                )

            else:

                send_message(
                    "NO SIGNAL",
                    chat_id
                )

    return "ok"

# =====================================================
# START BOT
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
