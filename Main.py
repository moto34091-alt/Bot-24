from flask import Flask
import requests
import os

app = Flask(__name__)

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=data)

@app.route("/")
def home():
    return "BOT ONLINE"

@app.route("/signal")
def signal():
    send_telegram("📈 BOT CONNECTÉ AVEC SUCCÈS")
    return "SIGNAL ENVOYÉ"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
