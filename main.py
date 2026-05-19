# =====================================================
# WEBHOOK TELEGRAM
# =====================================================
@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.get_json()

    # =================================================
    # MESSAGE TELEGRAM
    # =================================================
    if "message" in data:

        message = data["message"]

        chat_id = message["chat"]["id"]

        text = message.get("text", "")

        # =============================================
        # START
        # =============================================
        if text == "/start":

            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

            send_data = {
                "chat_id": chat_id,
                "text":
                "🤖 SNIPER BOT ACTIVÉ\n\n"
                "💬 Select option:",
                "reply_markup": main_menu()
            }

            requests.post(url, json=send_data)

        # =============================================
        # STATUS
        # =============================================
        elif text == "/status":

            send_message("✅ BOT ONLINE")

        # =============================================
        # SIGNAL
        # =============================================
        elif text == "/signal":

            signals = scan_market()

            if signals:

                send_message("\n\n".join(signals))

            else:

                send_message("NO SIGNAL")

    # =================================================
    # CALLBACK BUTTONS
    # =================================================
    if "callback_query" in data:

        callback = data["callback_query"]

        chat_id = callback["message"]["chat"]["id"]

        action = callback["data"]

        # =============================================
        # LANGUAGE MENU
        # =============================================
        if action == "language":

            send_menu = {
                "chat_id": chat_id,
                "text": "🌐 Language settings\n\n💬 Select your language:",
                "reply_markup": language_menu()
            }

            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json=send_menu
            )

        # =============================================
        # EXECUTE
        # =============================================
        elif action == "execute":

            send_menu = {
                "chat_id": chat_id,
                "text": "📊 Choisissez un marché :",
                "reply_markup": market_menu()
            }

            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json=send_menu
            )

        # =============================================
        # FOREX MENU
        # =============================================
        elif action == "market_forex":

            send_menu = {
                "chat_id": chat_id,
                "text": "💱 Choisissez une paire Forex :",
                "reply_markup": forex_menu()
            }

            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json=send_menu
            )

        # =============================================
        # CRYPTO MENU
        # =============================================
        elif action == "market_crypto":

            send_menu = {
                "chat_id": chat_id,
                "text": "🪙 Choisissez une Crypto :",
                "reply_markup": crypto_menu()
            }

            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json=send_menu
            )

        # =============================================
        # AUTO SIGNAL ON
        # =============================================
        elif action == "auto_on":

            send_message("✅ AUTO SIGNAL ACTIVÉ")

        # =============================================
        # AUTO SIGNAL OFF
        # =============================================
        elif action == "auto_off":

            send_message("🛑 AUTO SIGNAL DÉSACTIVÉ")

        # =============================================
        # HELP
        # =============================================
        elif action == "help":

            send_message(
                "❓ AIDE\n\n"
                "🚀 Exécuter → scanner\n"
                "📡 Auto Signal → signaux auto\n"
                "🌐 Langues → changer langue\n"
                "💱 Forex & Crypto disponibles"
            )

    return "ok"
