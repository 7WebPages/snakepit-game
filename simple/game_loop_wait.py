import asyncio
from aiohttp import web

async def handle(request):
    index = open("index.html", 'rb')
    content = index.read()
    return web.Response(body=content, content_type='text/html')



tick = asyncio.Condition()

async def wshandler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    recv_task = None
    tick_task = None
    while 1:
        if not recv_task:
            recv_task = asyncio.ensure_future(ws.receive())
        if not tick_task:
            await tick.acquire()
            tick_task = asyncio.ensure_future(tick.wait())

        done, pending = await asyncio.wait(
            [recv_task,
             tick_task],
            return_when=asyncio.FIRST_COMPLETED)

        if recv_task in done:
            msg = recv_task.result()
            if msg.tp == web.MsgType.text:
                print("Got message %s" % msg.data)
                ws.send_str("Pressed key code: {}".format(msg.data))
            elif msg.tp == web.MsgType.close or\
                 msg.tp == web.MsgType.error:
                break
            recv_task = None

        if tick_task in done:
            ws.send_str("game loop ticks")
            tick.release()
            tick_task = None

    return ws

async def game_loop():
    while 1:
        await tick.acquire()
        tick.notify_all()
        tick.release()
        await asyncio.sleep(1)

asyncio.ensure_future(game_loop())

app = web.Application()

app.router.add_route('GET', '/connect', wshandler)
app.router.add_route('GET', '/', handle)

web.run_app(app)
