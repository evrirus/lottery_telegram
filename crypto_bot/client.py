import os

from aiosend import TESTNET, CryptoPay
from aiosend.webhook import FlaskManager
from flask import Flask

app = Flask(__name__)
cp = CryptoPay(
    os.environ.get("CRYPTOBOT_TOKEN", ""),
    webhook_manager=FlaskManager(app, "/cryptobot-webhook"),
    network=TESTNET
)