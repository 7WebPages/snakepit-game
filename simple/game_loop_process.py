import asyncio
from aiohttp import web

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Queue, Process
import os
from time import sleep


async def handle(request):
    index = open("index.html", 'rb')
    content = index.read()
    return web.Response(body=content)


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
    # coroutine to run in main thread
    async def notify():
        await tick.acquire()
        tick.notify_all()
        tick.release()

    queue = Queue()

    # function to run in a different process
    def worker():
        while 1:
            print("doing heavy calculation in process {}".format(os.getpid()))
            sleep(1)
            queue.put("calculation result")

    Process(target=worker).start()

    while 1:
        # blocks this thread but not main thread with event loop
        result = queue.get()
        print("getting {} in process {}".format(result, os.getpid()))
        task = asyncio.run_coroutine_threadsafe(notify(), asyncio_loop)
        task.result()

asyncio_loop = asyncio.get_event_loop()
executor = ThreadPoolExecutor(max_workers=1)
asyncio_loop.run_in_executor(executor, game_loop, asyncio_loop)

app = web.Application()

app.router.add_route('GET', '/connect', wshandler)
app.router.add_route('GET', '/', handle)

web.run_app(app)
