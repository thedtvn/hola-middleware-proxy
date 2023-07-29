import re
import uuid
import random
import aiohttp
import asyncio
import xml.etree.ElementTree as ET

from yarl import URL

USER_AGENT = "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
EXT_BROWSER = "chrome"
PRODUCT = "cws"
CCGI_URL = "https://client.hola.org"

async def get_ver():
    async with aiohttp.ClientSession() as s:
        async with s.get("https://clients2.google.com/service/update2/crx", params={"acceptformat": ["crx2,crx3"], "prodversion": ["113.0"], "x": ["id=gkojfkhlekighikafcpjkiklfbnlmeio&uc="]}) as r:
            response_text = await r.text()
            return re.findall("version=\"(.+?)\"", response_text)[1]

async def background_init(user_id, EXT_VER):
    post_data = {
        "login": "1",
        "ver": EXT_VER,
    }
    query_string = {
        "uuid": user_id,
    }
    async with aiohttp.ClientSession(base_url=CCGI_URL, headers={"User-Agent": USER_AGENT}) as s:
        async with s.post("/client_cgi/background_init", params=query_string, data=post_data) as r:
            return await r.json()

async def vpn_countries():
    EXT_VER = await get_ver()
    query_string = {
        "ver": EXT_VER,
    }
    async with aiohttp.ClientSession(base_url=CCGI_URL, headers={"User-Agent": USER_AGENT}) as s:
        async with s.post("/client_cgi/vpn_countries.json", params=query_string) as r:
            return await r.json()

async def get_proxy(types_connect:str ="direct", country:str = "us"):
    EXT_VER = await get_ver()
    user_uuid = uuid.uuid4().hex
    username = "user-uuid-"+user_uuid
    session_key = (await background_init(user_uuid, EXT_VER))["key"]
    pram = {
        "country": country,
        "limit": 3,
        "ping_id": random.random(),
        "ext_ver": EXT_VER,
        "browser": EXT_BROWSER,
        "product": PRODUCT,
        "uuid": user_uuid,
        "session_key": session_key,
        "is_premium": 0,
    }
    async with aiohttp.ClientSession(base_url=CCGI_URL, headers={"User-Agent": USER_AGENT}) as s:
        async with s.post("/client_cgi/zgettunnels", params=pram) as r:
            data = await r.json()
    ip_list = [URL.build(scheme=i[1], host=i[0], port=data["port"][types_connect], user=username, password=data["agent_key"]) for i in data["protocol"].items()]
    return ip_list