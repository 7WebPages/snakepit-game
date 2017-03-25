import asyncio
from aiohttp import web

async def handle(request):
    index = open("index.html", 'rb')
    content = index.read()
    return web.Response(body=content, content_type='text/html')


async def wshandler(request):
    app = request.app
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    if app["game_loop"] is None or \
       app["game_loop"].cancelled():
        app["game_loop"] = asyncio.ensure_future(game_loop(app))
        # this is required to propagate exceptions
        app["game_loop"].add_done_callback(lambda t: t.result()
                                           if not t.cancelled() else None)
    app["sockets"].append(ws)
    while 1:
        msg = await ws.receive()
        if msg.tp == web.MsgType.text:
            ws.send_str("Pressed key code: {}".format(msg.data))
            print("Got message %s" % msg.data)
        elif msg.tp == web.MsgType.close or\
             msg.tp == web.MsgType.error:
            break

    app["sockets"].remove(ws)

    if len(app["sockets"]) == 0:
        print("Stopping game loop")
        app["game_loop"].cancel()

    print("Closed connection")
    return ws

async def game_loop(app):
    print("Game loop started")
    while 1:
        for ws in app["sockets"]:
            ws.send_str("game loop passed")
        await asyncio.sleep(2)


app = web.Application()

app["sockets"] = []
app["game_loop"] = None

app.router.add_route('GET', '/connect', wshandler)
app.router.add_route('GET', '/', handle)

web.run_app(app)
