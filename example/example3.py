import asyncio

from loguru import logger

from damai.performer import ApiFetchPerform
from damai.utils import make_ticket_data


class Gather(ApiFetchPerform):

    """并发测试"""

    POLL = 2
    COUNT = 2

    async def submit(self, item_id, sku_id, tickets):
        for _ in range(self.POLL):
            tasks = [self._submit(item_id, sku_id, tickets) for _ in range(self.COUNT)]
            await asyncio.gather(*tasks)

    async def _submit(self, item_id, sku_id, tickets):
        try:
            build_response = await self.build_order(f'{item_id}_{tickets}_{sku_id}')
            data = build_response.get("data")
            data = make_ticket_data(data)
            crate_response = await self.create_order(data)
        except Exception as e:
            logger.error(f'{type(e)} {e}')
        else:
            logger.info(f'生成：{build_response.get("ret")}')
            logger.info(f'创建：{crate_response.get("ret")}')
            if "调用成功" in " ".join(crate_response.get("ret", [])):
                logger.info("购买成功，到app订单管理中付款")


class Repeat(ApiFetchPerform):

    """重复提交测试"""

    POLL = 3

    async def submit(self, item_id, sku_id, tickets):
        response = await self.build_order(f'{item_id}_{tickets}_{sku_id}')
        b_ret = ' '.join(response["ret"])
        logger.info(f'生成订单：{b_ret}')

        if "调用成功" not in b_ret:
            return

        data = response.get("data", {})
        if not data.get("data"):
            return

        data = make_ticket_data(data)
        for _ in range(self.POLL):
            await self.create_order_future(data)
            await asyncio.sleep(0.5)

    async def create_order_future(self, data):
        results = asyncio.gather(self.create_order(data), self.create_order(data))
        for response in results:
            logger.info(f'创建订单：{" ".join(response["ret"])}')
            if "调用成功" in " ".join(response["ret"]):
                logger.info("购买成功，到app订单管理中付款")



