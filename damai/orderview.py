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


class SkuList:

    def __init__(self, itemId, skuId, price, priceName):
        self.itemId = itemId
        self.skuId = skuId
        self.price = price
        self.priceName = priceName


class Ticket:

    def __init__(self):
        self._ticket = {}

    def add_perform(self, date, limitQuantity, performBeginDTStr, performName, skuList):
        self._ticket[date] = PerformField(limitQuantity, performBeginDTStr, performName, skuList)



