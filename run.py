import json
import logging

from aiohttp import web

from shuffle import *

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

routes = web.RouteTableDef()


@routes.post('/player/scoreboard_data')
async def player(request):
    data = await request.post()
    ns2id = json.loads(data['ns2id'])
    hiveskill = json.loads(data['hiveskill'])
    stats.update()
    player = Player(ns2id, hiveskill)

    return web.json_response(player.json)


@routes.post('/shuffle')
async def shuffle(request):
    data = await request.post()
    ns2ids = json.loads(data['ns2ids'])
    hiveskills = json.loads(data['hiveskills'])
    shuffle = Shuffle(ns2ids, hiveskills)

    return web.json_response(shuffle.json)


app = web.Application()
app.add_routes(routes)

web.run_app(app, port=8100)
