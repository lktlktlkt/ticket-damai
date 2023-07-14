import json
import pprint
import re

import requests
from loguru import logger


class OrderView:
    """生成演出订单信息"""

    def __init__(self):
        self._views = {}
        self.url = ("https://detail.damai.cn/subpage?itemId={}&dataId={}&"
                    "dataType=2&apiVersion=2.0&dmChannel=pc@damai_pc&bizCode=ali.china.damai"
                    "&scenario=itemsku&privilegeActId=")
        self.headers = {
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh,en-US;q=0.9,en;q=0.8,zh-CN;q=0.7",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": "https://search.damai.cn/search.htm",
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                           " (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
        }

    @property
    def views(self):
        return self._views

    def get_calendar_id_list(self, item_id):
        data = self._make_perform_request(item_id)
        calendar = data.get("performCalendar", {}).get("performViews", [])
        return [view.get("performId") for view in calendar]

    def get_sku_info(self, item_id, data_id=''):
        data = self._make_perform_request(item_id, data_id)
        perform = data.get("perform", {})
        sku_list = perform.get("skuList", [])
        date = perform.get("performName")
        item = dict(performName=date,
                    performBeginDTStr=perform.get("performBeginDTStr"),
                    limitQuantity=perform.get("limitQuantity"))
        li = [dict(itemId=sku.get("itemId"), skuId=sku.get("skuId"),
                   priceName=sku.get("priceName"), price=sku.get("price"))
              for sku in sku_list]
        item["skuList"] = li
        return date.split()[0], item

    def _make_perform_request(self, item_id, perform_id=''):
        response = requests.get(self.url.format(item_id, perform_id), headers=self.headers)
        response.raise_for_status()
        data = json.loads(response.text.replace("null(", "").strip(')'))
        return data

    def add(self, item_id, alias=None):
        views = {}
        for calendar in self.get_calendar_id_list(item_id):
            logger.info(f'{item_id}/{calendar}')
            date, info = self.get_sku_info(item_id, calendar)
            views[date] = info
        logger.debug(pprint.pformat(views))

        self._views[alias or item_id] = views

    def get_sell_item(self, item_id):
        url = "https://detail.damai.cn/item.htm?id={}"
        response = requests.get(url.format(item_id), self.headers)
        start_time = re.search(r'sellStartTime":(.*?),', response.text).group(1)
        start_time = int(start_time) / 1000
        item_name = re.search(r'itemName":(.*?),', response.text).group(1).replace('"', "")
        return item_name, start_time


"""为了简便，不按python规范写了, 开发中"""


class PerformField:

    def __init__(self, limitQuantity, performBeginDTStr, performName, skuList):
        self.limitQuantity = limitQuantity
        self.performBeginDTStr = performBeginDTStr
        self.performName = performName
        self.skuList = skuList

    def __str__(self):
        return str(self.__dict__)

    __repr__ = __str__


from collections import namedtuple


SkuInfo = namedtuple('SkuInfo', ('itemId', 'skuId', 'price', 'priceName'))


class SkuList:

    def __init__(self):
        self._sku_list = []

    def get_sku(self, value):
        return self._sku_list[value]

    def add_sku(self, itemId, skuId, price, priceName):
        self._sku_list.append(SkuInfo(itemId, skuId, price, priceName))

    def __getitem__(self, item):
        if isinstance(item, int):
            try:
                return self._sku_list[item-1].skuId
            except IndexError:
                raise ValueError(f'当前可选票档为{tuple(range(1, len(self._sku_list)+1))}')
        elif isinstance(item, str):
            try:
                return next(sku.skuId for sku in self._sku_list if item == sku.priceName)
            except StopIteration:
                raise ValueError(f'{item}查询不到')
        else:
            raise TypeError('只支持int,str')

    def __str__(self):
        return str(self._sku_list)

    __repr__ = __str__


class PerformDict:

    def __init__(self):
        self._perform = {}

    @property
    def ticket(self):
        return self._perform

    def get_perform(self, perform) -> PerformField:
        return self.ticket[perform]

    def add_perform(self, date, limitQuantity, performBeginDTStr, performName, skuList):
        self._perform[date] = PerformField(limitQuantity, performBeginDTStr, performName, skuList)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._perform[list(self._perform.keys())[item]]
        elif isinstance(item, str):
            return self._perform[item]
        else:
            raise TypeError('只支持int,str')


class Ticket:

    def __init__(self):
        self._ticket = {}

    def add_item(self, item_id):
        pass


if __name__ == '__main__':
    with open('../view.json', encoding='utf-8') as fp:
        data = json.load(fp)
        ticket = PerformDict()
        perform = data.get("perform", {})
        sku_list = perform.get("skuList", [])
        date = perform.get("performName")
        performBeginDTStr = perform.get("performBeginDTStr")
        limitQuantity = perform.get("limitQuantity")

        sk = SkuList()
        for sku in sku_list:
            sk.add_sku(itemId=sku.get("itemId"), skuId=sku.get("skuId"), priceName=sku.get("priceName"), price=sku.get("price"))
        ticket.add_perform(date.split()[0], limitQuantity, performBeginDTStr, date, sk)

        p = ticket.get_perform('2023-07-15')
        print(ticket[0])
        # print(p.skuList)

