import asyncio

import fxbot.api.stream as s


async def main():
    q = asyncio.Queue()
    asyncio.create_task(s.PricingStreamer(q).run())
    for _ in range(3):
        tick = await q.get()
        print(tick["instrument"], tick["bids"][0]["price"])


asyncio.run(main())
