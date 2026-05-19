# =====================================================
# MENU PRINCIPAL
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
# MENU LANGUES
# =====================================================
def language_menu():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "🇫🇷 Français",
                    "callback_data": "lang_fr"
                },

                {
                    "text": "🇬🇧 English",
                    "callback_data": "lang_en"
                }
            ],

            [
                {
                    "text": "🇵🇹 Português",
                    "callback_data": "lang_pt"
                },

                {
                    "text": "🇨🇩 Swahili",
                    "callback_data": "lang_sw"
                }
            ],

            [
                {
                    "text": "🇨🇩 Lingala",
                    "callback_data": "lang_ln"
                }
            ]
        ]
    }

# =====================================================
# CHOIX MARCHÉ
# =====================================================
def market_menu():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "💱 Forex",
                    "callback_data": "market_forex"
                },

                {
                    "text": "🪙 Crypto",
                    "callback_data": "market_crypto"
                }
            ],

            [
                {
                    "text": "🥇 Gold",
                    "callback_data": "market_gold"
                },

                {
                    "text": "📈 Indices",
                    "callback_data": "market_indices"
                }
            ]
        ]
    }

# =====================================================
# FOREX MENU
# =====================================================
def forex_menu():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "EUR/USD",
                    "callback_data": "EUR/USD"
                },

                {
                    "text": "GBP/USD",
                    "callback_data": "GBP/USD"
                }
            ],

            [
                {
                    "text": "USD/JPY",
                    "callback_data": "USD/JPY"
                },

                {
                    "text": "AUD/USD",
                    "callback_data": "AUD/USD"
                }
            ]
        ]
    }

# =====================================================
# CRYPTO MENU
# =====================================================
def crypto_menu():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "BTC/USD",
                    "callback_data": "BTC/USD"
                },

                {
                    "text": "ETH/USD",
                    "callback_data": "ETH/USD"
                }
            ],

            [
                {
                    "text": "SOL/USD",
                    "callback_data": "SOL/USD"
                },

                {
                    "text": "XRP/USD",
                    "callback_data": "XRP/USD"
                }
            ]
        ]
    }

# =====================================================
# START COMMAND
# =====================================================
if text == "/start":

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data_send = {
        "chat_id": chat_id,
        "text":
        "🤖 SNIPER BOT ACTIVÉ\n\n"
        "💬: Select your language:",
        "reply_markup": main_menu()
    }

    requests.post(url, json=data_send)

# =====================================================
# CALLBACK BUTTONS
# =====================================================
if "callback_query" in data:

    callback = data["callback_query"]

    chat_id = callback["message"]["chat"]["id"]

    action = callback["data"]

    # ==========================================
    # LANGUAGE
    # ==========================================
    if action == "language":

        send_menu = {
            "chat_id": chat_id,
            "text": "🌐 Language settings\n\n💬: Select your language:",
            "reply_markup": language_menu()
        }

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json=send_menu
        )

    # ==========================================
    # EXECUTE
    # ==========================================
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

    # ==========================================
    # FOREX
    # ==========================================
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

    # ==========================================
    # CRYPTO
    # ==========================================
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

    # ==========================================
    # AUTO SIGNAL ON
    # ==========================================
    elif action == "auto_on":

        send_message("✅ AUTO SIGNAL ACTIVÉ")

    # ==========================================
    # AUTO SIGNAL OFF
    # ==========================================
    elif action == "auto_off":

        send_message("🛑 AUTO SIGNAL DÉSACTIVÉ")

    # ==========================================
    # HELP
    # ==========================================
    elif action == "help":

        send_message(
            "❓ AIDE\n\n"
            "🚀 Exécuter → lancer scanner\n"
            "📡 Auto Signal → signaux automatiques\n"
            "🌐 Langues → changer langue\n"
            "💱 Forex & Crypto disponibles"
        )
