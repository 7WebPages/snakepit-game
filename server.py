import os
import asyncio
import json
from aiohttp import web

import settings
from game import Game

async def handle(request):
    ALLOWED_FILES = ["index.html", "style.css"]
    name = request.match_info.get('name', 'index.html')
    if name in ALLOWED_FILES:
        try:
            with open(name, 'rb') as index:
                return web.Response(body=index.read())
        except FileNotFoundError:
            pass
    return web.Response(status=404)


async def wshandler(request):
    print("Connected")
    app = request.app
    game = app["game"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player = None
    while True:
        msg = await ws.receive()
        if msg.tp == web.MsgType.text:
            print("Got message %s" % msg.data)

            data = json.loads(msg.data)
            if type(data) == int and player:
                # Interpret as key code
                player.keypress(data)
            if type(data) != list:
                continue
            if not player:
                if data[0] == "new_player":
                    player = game.new_player(data[1], ws)
            elif data[0] == "join":
                if not game.running:
                    game.reset_world()

                    print("Starting game loop")
                    asyncio.ensure_future(game_loop(game))

                game.join(player)

        elif msg.tp == web.MsgType.close:
            break

    if player:
        game.player_disconnected(player)

    print("Closed connection")
    return ws

async def game_loop(game):
    game.running = True
    while 1:
        game.next_frame()
        if not game.count_alive_players():
            print("Stopping game loop")
            break
        await asyncio.sleep(1./settings.GAME_SPEED)
    game.running = False


event_loop = asyncio.get_event_loop()
event_loop.set_debug(True)

app = web.Application()

app["game"] = Game()

app.router.add_route('GET', '/connect', wshandler)
app.router.add_route('GET', '/{name}', handle)
app.router.add_route('GET', '/', handle)

# get port for heroku
port = int(os.environ.get('PORT', 5000))
web.run_app(app, port=port)
