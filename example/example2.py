import asyncio

from damai.performer import WebDriverPerform, ApiFetchPerform


ITEM_ID = 721234813852
SUK_ID = 5190876482301
TICKETS = 1


async def run():
    instant = WebDriverPerform()
    # instant = ApiFetchPerform()
    # instant.update_default_config(dict(COOKIE=''))
    await instant.init_browser()
    await instant.submit(ITEM_ID, SUK_ID, TICKETS)


asyncio.run(run())
