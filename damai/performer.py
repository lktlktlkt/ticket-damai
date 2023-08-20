import asyncio
import random
import re
import json
from collections import Counter

import aiohttp
from aiohttp import TCPConnector
from loguru import logger
from retry import retry

from damai.utils import get_sign, timestamp, make_ticket_data


class Perform:
    DEFAULT_CONFIG = dict()

    def update_default_config(self, configs: dict):
        for key in self.DEFAULT_CONFIG.keys():
            if key in configs:
                self.DEFAULT_CONFIG[key] = configs[key]

    def submit(self, item_id, sku_id, tickets):
        raise NotImplementedError()


class ApiFetchPerform(Perform):

    """接口请求购票"""

    DEFAULT_CONFIG = dict(
        **Perform.DEFAULT_CONFIG,
        USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
                   " Chrome/112.0.0.0 Safari/537.36",
        APP_KEY=12574478, RETRY=100, FAST=2, COOKIE=None, ADDRESS=''
    )
    NECESSARY = {"商品信息已过期", "Session", "令牌过期", "FAIL_SYS_USER_VALIDATE",
                 "未支付订单", "异常", "特权"}
    SECONDARY = {"库存", "挤爆"}

    def __init__(self):
        super().__init__()
        self.connector = TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=self.connector)

    @property
    def headers(self):
        return {
            "content-type": "application/x-www-form-urlencoded",
            "cookie": self.DEFAULT_CONFIG["COOKIE"],
            "globalcode": "ali.china.damai",
            "origin": "https://m.damai.cn",
            "referer": "https://m.damai.cn/",
            "user-agent": self.DEFAULT_CONFIG["USER_AGENT"]
        }

    @property
    def token(self):
        return re.search(r'_m_h5_tk=(.*?)_', self.DEFAULT_CONFIG["COOKIE"]).group(1)

    def update_default_config(self, configs):
        super().update_default_config(configs)
        if not self.DEFAULT_CONFIG["COOKIE"]:
            raise ValueError(f"{self}需要配置COOKIE")

    async def submit(self, item_id, sku_id, tickets):
        """购票流程

        RETRY: 退出购票的条件，当响应某个值到达一定次数将结束购票。如果能确保不出现验证码
        可以把值配置的更高，持续时间长捡票。
        """
        fast = self.DEFAULT_CONFIG["FAST"] - 1
        counter = Counter()
        c_ret = ''

        while all(counter.get(i, 0) < self.DEFAULT_CONFIG["RETRY"] for i in self.SECONDARY):
            response = await self.build_order(f'{item_id}_{tickets}_{sku_id}')
            b_ret = ' '.join(response["ret"])
            logger.info(f'生成订单：{b_ret}')

            if "调用成功" in b_ret:
                data = response.get("data", {})
                if not data.get("data"):
                    break
                data = make_ticket_data(data)
                response = await self.create_order(data)
                c_ret = ' '.join(response["ret"])
                logger.info(f"创建订单：{c_ret}")
                counter.update([self.detection(c_ret)])
                if "调用成功" in c_ret:
                    logger.info("抢票成功，前往app订单管理付款")
                    break
            counter.update([self.detection(b_ret)])

            if any(i in b_ret or i in c_ret for i in self.NECESSARY):
                break

            if fast:
                fast -= 1
                continue

            await asyncio.sleep(random.uniform(1, 1.5))

    def detection(self, sting):
        for field in {*self.SECONDARY, *self.NECESSARY}:
            if field in sting:
                return field
            return sting

    async def build_order(self, buy_param, sign_key=None):
        if not sign_key:
            sign_key = await self.get_sign_key(buy_param.split("_")[0])

        ep = {
            "channel": "damai_app", "damai": "1", "umpChannel": '100031004',
            "subChannel": 'damai@damaih5_h5', "atomSplit": '1', "serviceVersion": "2.0.0",
            "customerType": "default", "signKey": sign_key
        }
        data = {
            "buyNow": True, "exParams": json.dumps(ep, separators=(",", ":")),
            "buyParam": buy_param, "dmChannel": 'damai@damaih5_h5'
        }
        data = json.dumps(data, separators=(",", ":"))
        t = timestamp()
        sign = get_sign(self.token, t, self.DEFAULT_CONFIG["APP_KEY"], data)
        url = f'https://mtop.damai.cn/h5/mtop.trade.order.build.h5/4.0/?'
        params = {
            "jsv": "2.7.2", "appKey": self.DEFAULT_CONFIG["APP_KEY"], "t": t, "sign": sign,
            "type": "originaljson", "dataType": "json", "v": "4.0", "H5Request": "true",
            "AntiCreep": "true", "AntiFlood": "true", "api": "mtop.trade.order.build.h5",
            "method": "POST", "ttid": "#t#ip##_h5_2014", "globalCode": "ali.china.damai",
            "tb_eagleeyex_scm_project": "20190509-aone2-join-test"
        }
        async with self.session.post(url, params=params, data={'data': data},
                                     headers=self.headers) as response:
            return await response.json()

    async def create_order(self, data):
        t = timestamp()
        sign = get_sign(self.token, t, self.DEFAULT_CONFIG["APP_KEY"], data)
        url = 'https://mtop.damai.cn/h5/mtop.trade.order.create.h5/4.0/?'
        params = {
            "jsv": "2.7.2", "appKey": self.DEFAULT_CONFIG["APP_KEY"], "t": t, "sign": sign, "v": "4.0",
            "post": "1", "type": "originaljson", "timeout": "15000", "dataType": "json",
            "isSec": "1", "ecode": "1", "AntiCreep": "true", "ttid": "#t#ip##_h5_2014",
            "globalCode": "ali.china.damai", "tb_eagleeyex_scm_project": "20190509-aone2-join-test",
            "H5Request": "true", "api": "mtop.trade.order.create.h5"
        }
        async with self.session.post(url, params=params, data={'data': data},
                                     headers=self.headers) as response:
            return await response.json()

    async def get_detail(self, item_id):
        data = json.dumps({"itemId": item_id, "dmChannel": "damai@damaih5_h5"},
                          separators=(",", ":"))
        t = timestamp()
        sign = get_sign(self.token, t, self.DEFAULT_CONFIG["APP_KEY"], data)
        params = {
            "jsv": "2.7.2", "appKey": self.DEFAULT_CONFIG["APP_KEY"], "t": t,
            "sign": sign, "type": "originaljson", "dataType": "json",
            "v": "1.2", "H5Request": "true", "AntiCreep": "true", "AntiFlood": "true",
            "api": "mtop.alibaba.damai.detail.getdetail", "data": data
        }
        url = 'https://mtop.damai.cn/h5/mtop.alibaba.damai.detail.getdetail/1.2/?'
        async with self.session.get(url, headers=self.headers, params=params) as response:
            return await response.json()

    @retry(tries=3)
    async def get_subpage_detail(self, item_id):
        t = timestamp()
        data = {
            "itemId": item_id, "bizCode": "ali.china.damai", "scenario": "itemsku",
            "exParams": json.dumps({"dataType": 4, "dataId": "", "privilegeActId": ""}, separators=(",", ":")),
            "platform": "8", "comboChannel": "2", "dmChannel": "damai@damaih5_h5"
        }
        data = json.dumps(data, separators=(",", ":"))
        sign = get_sign(self.token, t, self.DEFAULT_CONFIG["APP_KEY"], data)
        params = {
            "jsv": "2.7.2", "appKey": self.DEFAULT_CONFIG["APP_KEY"], "t": t, "forceAntiCreep": "true",
            "sign": sign, "type": "originaljson", "dataType": "json", "timeout": 10000, "valueType": "original",
            "v": "2.0", "H5Request": "true", "AntiCreep": "true", "useH5": "true",
            "api": "mtop.alibaba.detail.subpage.getdetail", "data": data
        }
        url = "https://mtop.damai.cn/h5/mtop.alibaba.detail.subpage.getdetail/2.0/?"
        async with self.session.get(url, headers=self.headers, params=params) as response:
            return await response.json()

    async def get_sign_key(self, item_id):
        data = await self.get_subpage_detail(item_id)
        result = data.get("data", {}).get("result")
        return json.loads(result).get("itemBasicInfo", {}).get("t")

    async def close(self):
        await self.session.close()
