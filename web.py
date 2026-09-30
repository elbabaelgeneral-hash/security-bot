from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running ✅"

@app.route("/health")
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
