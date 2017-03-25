import asyncio
from aiohttp import web

from concurrent.futures import ThreadPoolExecutor
import threading
from time import sleep


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

def game_loop(asyncio_loop):
    print("Game loop thread id {}".format(threading.get_ident()))
    # a coroutine to run in main thread
    async def notify():
        print("Notify thread id {}".format(threading.get_ident()))
        await tick.acquire()
        tick.notify_all()
        tick.release()

    while 1:
        task = asyncio.run_coroutine_threadsafe(notify(), asyncio_loop)
        # blocking the thread
        sleep(1)
        # make sure the task has finished
        task.result()

print("Main thread id {}".format(threading.get_ident()))

asyncio_loop = asyncio.get_event_loop()
executor = ThreadPoolExecutor(max_workers=1)
asyncio_loop.run_in_executor(executor, game_loop, asyncio_loop)

app = web.Application()

app.router.add_route('GET', '/connect', wshandler)
app.router.add_route('GET', '/', handle)

web.run_app(app)
