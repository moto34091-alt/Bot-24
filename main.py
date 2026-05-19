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

# =====================================================
# AUTO SIGNAL
# =====================================================
auto_signal_enabled = True

last_signals = {}

# =====================================================
# TELEGRAM SEND MESSAGE
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

        # =================================================
        # LAST 3 CANDLES
        # =================================================
        c1 = candles[-1]
        c2 = candles[-2]
        c3 = candles[-3]

        close1 = float(c1["close"])
        open1 = float(c1["open"])
        high1 = float(c1["high"])
        low1 = float(c1["low"])

        close2 = float(c2["close"])
        open2 = float(c2["open"])

        close3 = float(c3["close"])
        open3 = float(c3["open"])

        # =================================================
        # VOLUME
        # =================================================
        volume1 = float(c1.get("volume", 0))
        volume2 = float(c2.get("volume", 0))

        high_volume = volume1 > volume2

        # =================================================
        # EMA
        # =================================================
        ema10 = ema(closes[-10:], 10)
        ema20 = ema(closes[-20:], 20)
        ema50 = ema(closes[-50:], 50)

        # =================================================
        # RSI
        # =================================================
        current_rsi = rsi(closes[-15:], 14)

        # =================================================
        # TREND
        # =================================================
        strong_uptrend = ema10 > ema20 > ema50
        strong_downtrend = ema10 < ema20 < ema50

        # =================================================
        # BODY
        # =================================================
        body = abs(close1 - open1)

        candle_range = high1 - low1

        upper_wick = high1 - max(close1, open1)

        lower_wick = min(close1, open1) - low1

        bullish = close1 > open1

        bearish = close1 < open1

        strong_body = body > candle_range * 0.5

        wick_buy = lower_wick > body * 1.5

        wick_sell = upper_wick > body * 1.5

        # =================================================
        # MOMENTUM
        # =================================================
        momentum_up = close1 > close2 > close3

        momentum_down = close1 < close2 < close3

        # =================================================
        # 3 CANDLES
        # =================================================
        bullish_3 = (
            close1 > open1 and
            close2 > open2 and
            close3 > open3
        )

        bearish_3 = (
            close1 < open1 and
            close2 < open2 and
            close3 < open3
        )

        # =================================================
        # VOLATILITY
        # =================================================
        volatility_ok = candle_range > close1 * 0.0007

        # =================================================
        # SCORE
        # =================================================
        buy_score = 0
        sell_score = 0

        if strong_uptrend:
            buy_score += 2

        if strong_downtrend:
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
            buy_score += 1

        if momentum_down:
            sell_score += 1

        if bullish_3:
            buy_score += 1

        if bearish_3:
            sell_score += 1

        if wick_buy:
            buy_score += 1

        if wick_sell:
            sell_score += 1

        if high_volume:
            buy_score += 1
            sell_score += 1

        if volatility_ok:
            buy_score += 1
            sell_score += 1

        # =================================================
        # POWER
        # =================================================
        buy_percent = int((buy_score / 9) * 100)

        sell_percent = int((sell_score / 9) * 100)

        # =================================================
        # BUY
        # =================================================
        if buy_score >= 7:

            return (
                f"🟢 BUY SIGNAL\n\n"
                f"💱 Pair: {symbol}\n"
                f"📈 Trend: BULLISH\n"
                f"📊 RSI: {round(current_rsi,2)}\n"
                f"⚡ Momentum: UP\n"
                f"📦 Volume: HIGH\n"
                f"🕯 Wick: BUY PRESSURE\n"
                f"🔥 Power: {buy_percent}%\n"
                f"⏰ Timeframe: {INTERVAL}"
            )

        # =================================================
        # SELL
        # =================================================
        if sell_score >= 7:

            return (
                f"🔴 SELL SIGNAL\n\n"
                f"💱 Pair: {symbol}\n"
                f"📉 Trend: BEARISH\n"
                f"📊 RSI: {round(current_rsi,2)}\n"
                f"⚡ Momentum: DOWN\n"
                f"📦 Volume: HIGH\n"
                f"🕯 Wick: SELL PRESSURE\n"
                f"🔥 Power: {sell_percent}%\n"
                f"⏰ Timeframe: {INTERVAL}"
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

                for pair in FOREX_PAIRS + CRYPTO_PAIRS + GOLD_PAIRS:

                    signal = analyze_pair(pair)

                    if signal:

                        if signal not in last_signals:

                            send_message(CHAT_ID, signal)

                            last_signals[signal] = time.time()

            current_time = time.time()

            expired = []

            for sig, t in last_signals.items():

                if current_time - t > 3600:
                    expired.append(sig)

            for sig in expired:
                del last_signals[sig]

        except Exception as e:

            send_message(CHAT_ID, f"BOT ERROR:\n{str(e)}")

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
    global auto_signal_enabled

    data = request.get_json()

    # =================================================
    # MESSAGE
    # =================================================
    if "message" in data:

        message = data["message"]

        chat_id = message["chat"]["id"]

        text = message.get("text", "")

        # START
        if text == "/start":

            send_menu(
                chat_id,
                "🤖 SNIPER BOT ACTIVÉ\n\n💬 Select option:",
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

        # =================================================
        # LANGUAGE
        # =================================================
        if action == "language":

            edit_menu(
                chat_id,
                message_id,
                "🌐 Select language:",
                language_menu()
            )

        elif action == "fr":

            send_message(chat_id, "🇫🇷 Français activé")

        elif action == "en":

            send_message(chat_id, "🇬🇧 English activated")

        elif action == "pt":

            send_message(chat_id, "🇵🇹 Português ativado")

        elif action == "sw":

            send_message(chat_id, "🇨🇩 Swahili activated")

        elif action == "ln":

            send_message(chat_id, "🇨🇩 Lingala activé")

        # =================================================
        # EXECUTE
        # =================================================
        elif action == "execute":

            edit_menu(
                chat_id,
                message_id,
                "⏰ Choose timeframe:",
                timeframe_menu()
            )

        # =================================================
        # TIMEFRAME
        # =================================================
        elif action == "tf15":

            INTERVAL = "15min"

            edit_menu(
                chat_id,
                message_id,
                "📊 Choose market:",
                market_menu()
            )

        elif action == "tf30":

            INTERVAL = "30min"

            edit_menu(
                chat_id,
                message_id,
                "📊 Choose market:",
                market_menu()
            )

        # =================================================
        # FOREX
        # =================================================
        elif action == "forex":

            edit_menu(
                chat_id,
                message_id,
                "💱 Forex Market",
                forex_menu()
            )

        # =================================================
        # CRYPTO
        # =================================================
        elif action == "crypto":

            edit_menu(
                chat_id,
                message_id,
                "🪙 Crypto Market",
                crypto_menu()
            )

        # =================================================
        # GOLD
        # =================================================
        elif action == "gold":

            edit_menu(
                chat_id,
                message_id,
                "🥇 Gold Market",
                gold_menu()
            )

        # =================================================
        # AUTO ON
        # =================================================
        elif action == "auto_on":

            auto_signal_enabled = True

            send_message(chat_id, "✅ AUTO SIGNAL ACTIVÉ")

        # =================================================
        # AUTO OFF
        # =================================================
        elif action == "auto_off":

            auto_signal_enabled = False

            send_message(chat_id, "🛑 AUTO SIGNAL DÉSACTIVÉ")

        # =================================================
        # HELP
        # =================================================
        elif action == "help":

            send_message(
                chat_id,
                "❓ AIDE\n\n"
                "🚀 Exécuter → Scanner marché\n"
                "💱 Forex + Crypto + Gold\n"
                "📡 Auto Signal disponible\n"
                "⏰ 15MIN et 30MIN\n"
                "📊 Momentum + RSI + Volume"
            )

        # =================================================
        # PAIR SIGNAL
        # =================================================
        elif "/" in action:

            result = analyze_pair(action)

            if result:
                send_message(chat_id, result)
            else:
                send_message(chat_id, "NO SIGNAL")

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
