import asyncio
import json
import logging
import os

import aiohttp

STREAM_URL = "https://stream-fxpractice.oanda.com"
ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
TOKEN = os.getenv("OANDA_API_TOKEN")
INSTRUMENT = os.getenv("INSTRUMENT", "USD_JPY")


class PricingStreamer:
    def __init__(self, q: asyncio.Queue):
        self.q = q
        self.log = logging.getLogger(__name__)

    async def run(self):
        url = f"{STREAM_URL}/v3/accounts/{ACCOUNT_ID}/pricing/stream"
        headers = {"Authorization": f"Bearer {TOKEN}"}
        params = {"instruments": INSTRUMENT}
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, headers=headers, params=params) as r:
                async for raw in r.content:
                    if raw.strip():
                        msg = json.loads(raw)
                        if msg.get("type") == "PRICE":
                            await self.q.put(msg)
