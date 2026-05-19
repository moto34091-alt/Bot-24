from flask import Flask, request
import os
import requests
import time
from threading import Thread

app = Flask(__name__)

# =====================================================
# CONFIG
# =====================================================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

INTERVAL = "15min"

# =====================================================
# ANTI DUPLICATE SIGNALS
# =====================================================
last_signals = {}

# =====================================================
# TELEGRAM MESSAGE
# =====================================================
def send_message(text):

    try:

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        data = {
            "chat_id": CHAT_ID,
            "text": text
        }

        requests.post(url, data=data)

    except Exception as e:
        print(e)

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
# MARKET ANALYSIS SNIPER
# =====================================================
def analyze_pair(symbol):

    try:

        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={symbol}"
            f"&interval={INTERVAL}"
            f"&outputsize=60"
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
        high = float(current["high"])
        low = float(current["low"])

        prev_close = float(previous["close"])

        # =====================================================
        # EMA
        # =====================================================
        ema10 = ema(closes[-10:], 10)
        ema20 = ema(closes[-20:], 20)
        ema50 = ema(closes[-50:], 50)

        # =====================================================
        # RSI
        # =====================================================
        current_rsi = rsi(closes[-15:], 14)

        # =====================================================
        # TREND
        # =====================================================
        trend_up = ema10 > ema20 > ema50
        trend_down = ema10 < ema20 < ema50

        # =====================================================
        # CANDLE STRENGTH
        # =====================================================
        body = abs(close - open_)
        candle_range = high - low

        bullish = close > open_
        bearish = close < open_

        strong_body = body > candle_range * 0.45

        # =====================================================
        # MOMENTUM
        # =====================================================
        momentum_up = close > prev_close
        momentum_down = close < prev_close

        # =====================================================
        # VOLATILITY
        # =====================================================
        volatility_ok = candle_range > close * 0.0006

        # =====================================================
        # SNIPER SCORE
        # =====================================================
        call_score = 0
        put_score = 0

        # TREND
        if trend_up:
            call_score += 2

        if trend_down:
            put_score += 2

        # RSI
        if current_rsi > 55:
            call_score += 1

        if current_rsi < 45:
            put_score += 1

        # MOMENTUM
        if momentum_up:
            call_score += 1

        if momentum_down:
            put_score += 1

        # STRONG CANDLE
        if bullish and strong_body:
            call_score += 1

        if bearish and strong_body:
            put_score += 1

        # VOLATILITY
        if volatility_ok:
            call_score += 1
            put_score += 1

        # =====================================================
        # FINAL SIGNALS
        # =====================================================
        if call_score >= 5:

            return (
                f"🔥 SNIPER CALL\n\n"
                f"💱 Pair: {symbol}\n"
                f"📈 Trend: STRONG UP\n"
                f"📊 RSI: {round(current_rsi, 2)}\n"
                f"🔥 Score: {call_score}/6\n"
                f"⏰ TF: 15MIN"
            )

        if put_score >= 5:

            return (
                f"⚡ SNIPER PUT\n\n"
                f"💱 Pair: {symbol}\n"
                f"📉 Trend: STRONG DOWN\n"
                f"📊 RSI: {round(current_rsi, 2)}\n"
                f"🔥 Score: {put_score}/6\n"
                f"⏰ TF: 15MIN"
            )

        return None

    except Exception as e:

        return f"ERROR: {str(e)}"

# =====================================================
# MARKET SCANNER
# =====================================================
def scan_market():

    signals = []

    for pair in PAIRS:

        result = analyze_pair(pair)

        if result and not result.startswith("ERROR"):

            signals.append(result)

    return signals

# =====================================================
# AUTO LIVE SIGNALS
# =====================================================
def auto_signals():

    while True:

        try:

            signals = scan_market()

            for signal in signals:

                if signal not in last_signals:

                    send_message(signal)

                    last_signals[signal] = time.time()

            # CLEAN OLD SIGNALS
            current_time = time.time()

            expired = []

            for sig, t in last_signals.items():

                if current_time - t > 3600:
                    expired.append(sig)

            for sig in expired:
                del last_signals[sig]

        except Exception as e:

            send_message(f"BOT ERROR:\n{str(e)}")

        # CHECK EVERY 5 MINUTES
        time.sleep(300)

# =====================================================
# HOME
# =====================================================
@app.route("/")
def home():

    return "SNIPER BOT 15MIN ONLINE"

# =====================================================
# STATUS
# =====================================================
@app.route("/status")
def status():

    return "SNIPER STATUS ACTIVE"

# =====================================================
# SIGNAL ROUTE
# =====================================================
@app.route("/signal")
def signal():

    signals = scan_market()

    if signals:
        return "\n\n".join(signals)

    return "NO SIGNAL"

# =====================================================
# TELEGRAM WEBHOOK
# =====================================================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    if "message" in data:

        text = data["message"].get("text", "")

        # START
        if text == "/start":

            send_message(
                "🤖 SNIPER BOT 15MIN ACTIVÉ\n\n"
                "Commandes:\n"
                "/signal - Voir signaux\n"
                "/status - Vérifier bot"
            )

        # STATUS
        elif text == "/status":

            send_message("✅ SNIPER BOT ONLINE")

        # SIGNAL
        elif text == "/signal":

            signals = scan_market()

            if signals:
                send_message("\n\n".join(signals))
            else:
                send_message("NO SIGNAL")

    return "ok"

# =====================================================
# START BOT
# =====================================================
if __name__ == "__main__":

    # AUTO SIGNAL THREAD
    thread = Thread(target=auto_signals)
    thread.daemon = True
    thread.start()

    # FLASK
    PORT = int(os.environ.get("PORT", 5000"))

    app.run(
        host="0.0.0.0",
        port=PORT
    )
