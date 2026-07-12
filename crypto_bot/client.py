import os

from aiosend import CryptoPay
from aiosend.webhook import FlaskManager
from flask import Flask

app = Flask(__name__)
cp = CryptoPay(
    os.environ.get("CRYPTOBOT_TOKEN", ""),
    webhook_manager=FlaskManager(app, "/cryptobot-webhook"),
)
print(app.url_map)
print("FLASK INSTANCE:", id(app))
