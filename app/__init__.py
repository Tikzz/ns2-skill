from flask import Flask
from app.shuffle import Stats
app = Flask(__name__)
stats = Stats()

from app import main