import asyncio
from aiohttp import web

async def handle(request):
    index = open("index.html", 'rb')
    content = index.read()
    return web.Response(body=content)


async def wshandler(request):
    app = request.app
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    app["sockets"].append(ws)

    while 1:
        msg = await ws.receive()
        if msg.tp == web.MsgType.text:
            print("Got message %s" % msg.data)
            ws.send_str("Pressed key code: {}".format(msg.data))
        elif msg.tp == web.MsgType.close or\
             msg.tp == web.MsgType.error:
            break

    app["sockets"].remove(ws)
    print("Closed connection")
    return ws

async def game_loop(app):
    while 1:
        for ws in app["sockets"]:
            ws.send_str("game loop says: tick")
        await asyncio.sleep(2)


app = web.Application()
app["sockets"] = []

asyncio.ensure_future(game_loop(app))

app.router.add_route('GET', '/connect', wshandler)
app.router.add_route('GET', '/', handle)

web.run_app(app)
