from flask import Flask
import requests
import os

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route("/")
def home():
    return "BOT ONLINE"

@app.route("/signal")
def signal():

    if not TOKEN or not CHAT_ID:
        return "TOKEN OU CHAT_ID MANQUANT"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": "📈 BOT CONNECTÉ AVEC SUCCÈS"
    }

    requests.post(url, data=data)

    return "SIGNAL ENVOYÉ"

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
