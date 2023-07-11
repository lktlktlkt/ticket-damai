import asyncio

from damai.performer import ApiFetchPerform
from damai.utils import make_ticket_data

from loguru import logger

POLL = 2
COUNT = 2


class Gather(ApiFetchPerform):

    async def submit(self, item_id, sku_id, tickets):
        for _ in range(POLL):
            tasks = [self._submit(item_id, sku_id, tickets) for _ in range(COUNT)]
            await asyncio.gather(*tasks)
        await super().submit(item_id, sku_id, tickets)

    async def _submit(self, item_id, sku_id, tickets):
        crate_response = {}
        try:
            build_response = await self.build_order(f'{item_id}_{tickets}_{sku_id}')
            data = build_response.get("data")
            if data:
                data = make_ticket_data(data)
                crate_response = await self.create_order(data)
        except Exception as e:
            logger.info(f'{type(e)} {e}')
        else:
            logger.info(f'生成：{build_response.get("ret")}')
            logger.info(f'创建：{crate_response.get("ret")}')
