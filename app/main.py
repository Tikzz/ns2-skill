from app import app
from flask import request, jsonify
import json
from app.shuffle import Shuffle, Player
import logging


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.route('/shuffle', methods=['POST'])
def shuffle():
    logging.info(request.form)
    ns2ids = json.loads(request.form['ns2ids'])
    hiveskills = json.loads(request.form['hiveskills'])
    shuffle = Shuffle(ns2ids, hiveskills)

    return shuffle.json

@app.route('/player/scoreboard_data', methods=['POST'])
def get_hs_teams():
    ns2id = json.loads(request.form['ns2id'])
    hiveskill = json.loads(request.form['hiveskill'])
    player = Player(ns2id, hiveskill)

    return player.json

if __name__ == '__main__':
    app.debug = True
    app.run(debug=True)
