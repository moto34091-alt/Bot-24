from flask import Flask, request
import os
import requests
import time
from threading import Thread

app = Flask(__name__)

# ==================================================
# CONFIGURATION
# ==================================================
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("TWELVE_API_KEY")

# TON CHAT ID TELEGRAM
CHAT_ID = os.getenv("CHAT_ID")

# PAIRS FOREX
PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

# TIMEFRAME
INTERVAL = "15min"

# ANTI SPAM
last_signals = {}

# ==================================================
# TELEGRAM MESSAGE
# ==================================================
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

# ==================================================
# EMA
# ==================================================
def calculate_ema(prices, period):

    multiplier = 2 / (period + 1)

    ema = prices[0]

    for price in prices[1:]:
        ema = ((price - ema) * multiplier) + ema

    return ema

# ==================================================
# RSI
# ==================================================
def calculate_rsi(closes, period=14):

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

# ==================================================
# MARKET ANALYSIS
# ==================================================
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

        # CURRENT CANDLE
        current = candles[-1]
        previous = candles[-2]

        close = float(current["close"])
        open_ = float(current["open"])
        high = float(current["high"])
        low = float(current["low"])

        prev_close = float(previous["close"])

        # ==================================================
        # INDICATORS
        # ==================================================
        ema10 = calculate_ema(closes[-10:], 10)
        ema20 = calculate_ema(closes[-20:], 20)

        rsi = calculate_rsi(closes[-15:], 14)

        # ==================================================
        # TREND
        # ==================================================
        trend_up = ema10 > ema20
        trend_down = ema10 < ema20

        # ==================================================
        # CANDLE POWER
        # ==================================================
        body = abs(close - open_)
        candle_range = high - low

        bullish = close > open_
        bearish = close < open_

        strong_body = body > candle_range * 0.4

        # ==================================================
        # VOLATILITY
        # ==================================================
        volatility_ok = candle_range > close * 0.0005

        # ==================================================
        # MOMENTUM
        # ==================================================
        momentum_up = close > prev_close
        momentum_down = close < prev_close

        # ==================================================
        # SIGNAL SCORE
        # ==================================================
        call_score = 0
        put_score = 0

        # TREND
        if trend_up:
            call_score += 1

        if trend_down:
            put_score += 1

        # RSI
        if rsi > 52:
            call_score += 1

        if rsi < 48:
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

        # ==================================================
        # FINAL SIGNALS
        # ==================================================
        if call_score >= 4:

            return (
                f"📈 CALL SIGNAL\n\n"
                f"💱 Pair: {symbol}\n"
                f"📊 Trend: UP\n"
                f"📈 RSI: {round(rsi, 2)}\n"
                f"🔥 Score: {call_score}/5\n"
                f"⏰ Timeframe: 15min"
            )

        if put_score >= 4:

            return (
                f"📉 PUT SIGNAL\n\n"
                f"💱 Pair: {symbol}\n"
                f"📊 Trend: DOWN\n"
                f"📈 RSI: {round(rsi, 2)}\n"
                f"🔥 Score: {put_score}/5\n"
                f"⏰ Timeframe: 15min"
            )

        return None

    except Exception as e:

        return f"ERROR: {str(e)}"

# ==================================================
# MARKET SCANNER
# ==================================================
def scan_market():

    signals = []

    for pair in PAIRS:

        result = analyze_pair(pair)

        if result and not result.startswith("ERROR"):

            signals.append(result)

    return signals

# ==================================================
# AUTO SIGNAL LOOP
# ==================================================
def auto_signals():

    while True:

        try:

            signals = scan_market()

            for signal in signals:

                # ANTI DUPLICATE
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

        # CHECK EVERY 5 MIN
        time.sleep(300)

# ==================================================
# HOME
# ==================================================
@app.route("/")
def home():

    return "BOT 15MIN ONLINE"

# ==================================================
# STATUS
# ==================================================
@app.route("/status")
def status():

    return "BOT STATUS ACTIVE"

# ==================================================
# SIGNAL ROUTE
# ==================================================
@app.route("/signal")
def signal():

    signals = scan_market()

    if signals:
        return "\n\n".join(signals)

    return "NO SIGNAL"

# ==================================================
# TELEGRAM WEBHOOK
# ==================================================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    if "message" in data:

        chat_id = data["message"]["chat"]["id"]

        text = data["message"].get("text", "")

        # START
        if text == "/start":

            send_message(
                "🤖 BOT 15MIN ACTIVÉ\n\n"
                "Commandes:\n"
                "/signal - Voir signaux\n"
                "/status - Vérifier bot"
            )

        # STATUS
        elif text == "/status":

            send_message("✅ BOT ONLINE")

        # SIGNALS
        elif text == "/signal":

            signals = scan_market()

            if signals:

                send_message("\n\n".join(signals))

            else:

                send_message("NO SIGNAL")

    return "ok"

# ==================================================
# START BOT
# ==================================================
if __name__ == "__main__":

    # AUTO TELEGRAM SIGNALS
    thread = Thread(target=auto_signals)
    thread.daemon = True
    thread.start()

    # FLASK
    PORT = int(os.environ.get("PORT", 5000"))

    app.run(
        host="0.0.0.0",
        port=PORT
        )
