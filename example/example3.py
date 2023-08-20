import asyncio
import json
import sys

from loguru import logger

from damai.performer import ApiFetchPerform
from damai.utils import make_ticket_data
from damai.orderview import OrderView


class Gather(ApiFetchPerform):

    """根据POLL， COUNT进行并发

    建议不要改动，且不要多次调用。
    """

    POLL = 1
    COUNT = 2

    async def submit(self, item_id, sku_id, tickets):
        for _ in range(self.POLL):
            tasks = [self.leak_submit(item_id, sku_id, tickets) for _ in range(self.COUNT)]
            await asyncio.gather(*tasks)

    async def leak_submit(self, item_id, sku_id, tickets):
        build_response = await self.build_order(f'{item_id}_{tickets}_{sku_id}')
        try:
            data = build_response.get("data")
            data = make_ticket_data(data)
            crate_response = await self.create_order(data)
        except Exception as e:
            ret = ' '.join(build_response.get("ret", ''))
            logger.error(f'{type(e)} {e} {ret}')
            return ret
        else:
            build_ret = ' '.join(build_response.get("ret", ''))
            crate_ret = ' '.join(crate_response.get("ret", ''))
            logger.info(f'生成：{build_ret}, 创建：{crate_ret}')
            if "调用成功" in crate_ret:
                logger.info("抢票成功，前往app订单管理付款")
                notice(self.DEFAULT_CONFIG['ADDRESS'])
                sys.exit()
            return build_ret + crate_ret


class SalableQuantity(Gather):
    """判断是否有库存，来减少一些不必要请求，避免频繁导致出现滑块。

    使用此类价格请使用int或list，否则会不兼容。

    支持按票价优先级抢，如
    PRICE=[3, 2, 1] ==> 前几次会抢3，没抢到会查依次查询PRICE对应的余票进行抢
    """

    DEFAULT_CONFIG = dict(
        **Gather.DEFAULT_CONFIG,
        CONCERT=1, PRICE=1
    )

    def __init__(self):
        super().__init__()
        self.order = OrderView()

    async def submit(self, item_id, sku_id, tickets):
        await super().submit(item_id, sku_id, tickets)
        await asyncio.sleep(2)

        data_id = self.get_data_id(item_id)
        # 查询可接受的库存
        while True:
            gen = self.pc_tags(item_id, data_id)
            for tags, sku_id in gen:
                if tags:
                    logger.debug(f'{tags}, {sku_id}')
                    continue

                future = await asyncio.gather(
                    self.leak_submit(item_id, sku_id, tickets),
                    self.leak_submit(item_id, sku_id, tickets)
                )
                ret = ' '.join(future)

                if any(i in ret for i in self.NECESSARY):
                    return

                if "RGV587_ERROR" in ret:
                    await asyncio.sleep(9.5)
                    break

                await asyncio.sleep(2)
                break

    def get_data_id(self, item_id):
        calendars = self.order.get_calendar_id_list(item_id)
        concert = self.DEFAULT_CONFIG["CONCERT"]
        concert = [concert] if isinstance(concert, int) else concert
        return [calendars[c - 1] for c in concert]

    def pc_tags(self, item_id, data_id):
        for id_ in data_id:
            data = self.order.make_perform_request(item_id, id_)
            perform = data.get("perform", {})
            sku_list = perform.get("skuList", [])
            price = self.DEFAULT_CONFIG["PRICE"]
            price = [price] if isinstance(price, int) else price
            for index in price:
                info = sku_list[index - 1]
                yield info.get("tags"), info.get('skuId')

    async def h5_tags(self, item_id):
        """暂时未用"""
        data = await self.get_detail(item_id)
        d = data.get("data", {})
        if not d:
            raise ValueError(data.get('ret'))
        result = json.loads(d["result"])
        performs = result["detailViewComponentMap"]["item"]["item"]["performBases"]
        sku = performs[0]['performs'][0]['skuList'][1]
        return sku.get("promotionTags", None)


def notice(*args, **kwargs):
    """通知功能
    对代码了解后不要通知也可以，但对代码不了解的请实现，有时候异步代码抢到了报错了
    别忘记付款。
    """
    logger.info(f"通知功能: {args}, {kwargs}")
