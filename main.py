import asyncio
from hola_proxy import get_proxy
import aiohttp
import random
import time
import base64
from aiohttp import web

class TCPReader(asyncio.StreamReader):
    def feed_data(self, data: bytes):
        super().feed_data(data)
        return (False, 1)

proxy_data = {}

@web.middleware
async def handle(request: web.Request, handler):
    print(request.method)
    print(request.url)
    print(request.headers)

    if int(time.time()) >= proxy_data.get("t", 0):
        proxy_data["l"] = await get_proxy()
        proxy_data["t"] = int(time.time()) + 5 * 60
    proxy = random.choice(proxy_data["l"])
    print(proxy)
    reader, writer = await asyncio.open_connection(proxy.host, proxy.port)
    raw_headers = request.headers.copy()
    auth = base64.urlsafe_b64encode(f"{proxy.user}:{proxy.password}".encode()).decode()
    raw_headers["Proxy-Authorization"] = f"Basic {auth}"
    headers_proxy = [f"{k}: {v}" for k, v in raw_headers.items()]
    headers_proxy_str = "\r\n".join(headers_proxy)
    headers = ""
    if headers_proxy_str:
        headers = "\r\n"+headers_proxy_str
    url = request.url if request.url.scheme else f"{request.url.host}:{request.url.port}"
    data = f'{request.method} {url} HTTP/1.1{headers}\r\n\r\n'.encode()+await request.content.read()
    writer.write(data)
    await writer.drain()
    reader_US = TCPReader(loop=request._loop)
    reader_US.set_transport(request._protocol.transport)
    writer_user = aiohttp.http.StreamWriter(request._protocol, request._loop)
    request.protocol.set_parser(reader_US)
    ison = [1]
    request.protocol.keep_alive(False)
    async def server_to_user():
        while ison:
            read = await reader.read(1024)
            if read and ison:
                writer_user._write(read)
                await writer_user.drain()
            else:
                ison.clear()
    async def user_to_server():
        while ison:
            read = await reader_US.read(1024)
            if read and ison:
                writer.write(read)
            else:
                ison.clear()
    await asyncio.gather(user_to_server(), server_to_user())
    request.protocol.close()
    writer.close()


app = web.Application()
app.middlewares.append(handle)

web.run_app(app)