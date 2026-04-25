from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

alerts = []

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def get_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        res = requests.get(url, timeout=10)
        data = res.json()
        return data[coin_id]["usd"]
    except:
        return None

def monitor():
    while True:
        for alert in alerts:
            if alert["triggered"]:
                continue
            price = get_price(alert["coin"])
            if price is None:
                continue
            hit = False
            if alert["direction"] == "above" and price >= alert["target"]:
                hit = True
            elif alert["direction"] == "below" and price <= alert["target"]:
                hit = True
            if hit:
                alert["triggered"] = True
                direction_text = "تجاوز" if alert["direction"] == "above" else "نزل تحت"
                msg = f"🚨 تنبيه! {alert['coin'].upper()} {direction_text} ${alert['target']:,}\nالسعر الحالي: ${price:,}"
                send_telegram(msg)
        time.sleep(30)

threading.Thread(target=monitor, daemon=True).start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add_alert", methods=["POST"])
def add_alert():
    data = request.json
    alerts.append({
        "coin": data["coin"].lower(),
        "direction": data["direction"],
        "target": float(data["target"]),
        "triggered": False
    })
    return jsonify({"status": "ok"})

@app.route("/alerts")
def get_alerts():
    return jsonify(alerts)

@app.route("/price/<coin>")
def price(coin):
    p = get_price(coin)
    return jsonify({"price": p})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
