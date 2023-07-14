import asyncio
import random
import re
import json
import sys
import time
from collections import Counter
from typing import Optional

import aiohttp
from aiohttp import TCPConnector
from pyppeteer.browser import Browser
from pyppeteer.launcher import connect
from pyppeteer.page import Page
from pyppeteer.errors import TimeoutError, ElementHandleError, NetworkError
from loguru import logger

from damai.errors import LoginError, NotElementError, CongestionError
from damai.utils import get_sign, timestamp, make_ticket_data, make_order_url


class Perform:

    DEFAULT_CONFIG = dict(PORT=9222)

    def __init__(self):
        self.browser: Optional[Browser] = None

    def update_default_config(self, configs: dict):
        for key in self.DEFAULT_CONFIG.keys():
            if key in configs:
                self.DEFAULT_CONFIG[key] = configs[key]

    async def init_browser(self, **config):
        # 未开启调式浏览器时，browserURL有30s重试
        self.browser = await connect(
            browserURL=f"http://127.0.0.1:{self.DEFAULT_CONFIG['PORT']}", **config
        )

    @property
    async def page(self) -> Page:
        pages = await self.browser.pages()
        return pages[0]

    async def auto_jump(self):
        """确保停留在订单页"""
        page = await self.page
        url = make_order_url(718335834447, 5012364593181, 1)
        await page.goto(url)

    def submit(self, item_id, sku_id, tickets):
        raise NotImplementedError()


class ApiFetchPerform(Perform):

    """接口请求购票"""

    DEFAULT_CONFIG = dict(
        **Perform.DEFAULT_CONFIG,
        USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
                   " Chrome/112.0.0.0 Safari/537.36",
        APP_KEY=12574478, RETRY=100, FAST=2, COOKIE=None
    )
    NECESSARY = {"商品信息已过期", "Session", "令牌过期", "FAIL_SYS_USER_VALIDATE", "未支付订单"}
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

    async def build_order(self, buy_param):
        ep = {
            "channel": "damai_app", "damai": "1", "umpChannel": '100031004',
            "subChannel": 'damai@damaih5_h5', "atomSplit": '1', "serviceVersion": "2.0.0",
            "customerType": "default"
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
        bx_ua, bx_umidtoken = await self.ua_and_umidtoken()
        data = {'data': data, 'bx-ua': bx_ua, 'bx-umidtoken': bx_umidtoken}
        async with self.session.post(url, params=params, data=data,
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
        bx_ua, bx_umidtoken = await self.ua_and_umidtoken()
        data = {'data': data, 'bx-ua': bx_ua, 'bx-umidtoken': bx_umidtoken}
        async with self.session.post(url, params=params, data=data,
                                     headers=self.headers) as response:
            return await response.json()

    async def ua_and_umidtoken(self) -> list:
        """获取订单页的bx-ua， bx-umidtoken
        return [bx-ua, bx-umidtoken]
        """
        page = await self.page
        try:
            futures = (
                page.evaluate('this.__baxia__.postFYModule.getFYToken()'),
                page.evaluate('this.__baxia__.postFYModule.getUidToken()')
            )
            results = await asyncio.gather(*futures)
            return [result for result in results]
        except (ElementHandleError, NetworkError):
            title = await page.title()
            logger.error(f"目前停留标签页面为：{title}")
            await self.close()
            raise ElementHandleError('bx_ua, umidtoken需要Page为订单页面, 先切换至订单页')

    async def close(self):
        await self.session.close()


class WebDriverPerform(Perform):

    """模拟浏览器购票

    在开票后一直点击提交订单，会出现“请勿重复提交订单”，然后出现“网络拥堵“提示。
    几次开票测试中，出现“网络拥堵”，关闭后点击提交立马又出现，出现后几秒内刷新都没用。
    在捡漏成功时，感觉每次都没出现“请勿重复提交订单”，可能疯狂发送请求过去其实没啥用。
    出现网络拥堵，立即刷新页面，再次提交订单，反正直接捡漏成功。

    推荐把浏览器缩放50%，后面发现页面被修改了，不缩放可能造成无法勾选实名观演人
    """

    DEFAULT_CONFIG = dict(
        **Perform.DEFAULT_CONFIG,
        CRITICAL_WAIT=450, WARN_WAIT=100, SUBMIT_FREQUENCY=2,
        SHUTDOWN=60 * 10
    )

    async def submit(self, item_id, sku_id, tickets):
        page = await self.browser.newPage()
        url = make_order_url(item_id, sku_id, tickets)
        start = time.time()
        while True:
            logger.info(f'{"*"*10}刷新{"*"*10}')
            try:
                await asyncio.wait([page.goto(url), page.waitForNavigation()])
                await self.select_real_name(page, tickets)
                await page.waitFor(self.DEFAULT_CONFIG['CRITICAL_WAIT'])
                await self.polling(page)
            except (CongestionError, NotElementError) as e:
                logger.error(e)
                continue
            except LoginError as e:
                logger.error(e)
                break
            except Exception as e:
                logger.error(e)

            if time.time() - start > self.DEFAULT_CONFIG['SHUTDOWN']:
                return

    async def select_real_name(self, page, ticket_num: int = 1):
        """选择实名制观演人，根据ticket_num勾选人数，默认勾选第一个。

        使用waitForSelector后， 网页元素改变和网络原因会抛出TimeoutError。
        """
        selector = "i.iconfont.icondanxuan-weixuan_"
        try:
            await page.waitForSelector(selector, timeout=2000)
        except TimeoutError:
            # 本次抢票未登录，直接结束，渠道不支持的不要使用手动退出
            if await page.title() == "登录":
                raise LoginError('未登录')
            raise NotElementError(f'`{selector}`未找到，网络问题、出现提示框、标签元素改动、渠道不支持过期其一')
        items = await page.querySelectorAll(selector)
        for num in range(0, ticket_num):
            await items[num].click()

    async def polling(self, page):
        # 需要优化
        selector = '#dmOrderSubmitBlock_DmOrderSubmitBlock div[view-name=TextView]'
        items = await page.querySelectorAll(selector)
        if not items:
            raise NotElementError(f'`{selector}`未找到')

        button = items[-1]
        while True:
            # 实测点击多了并没用，基本连续点击三次出现"网络拥堵"提示
            for _ in range(self.DEFAULT_CONFIG['SUBMIT_FREQUENCY']):
                await button.click()
                logger.info('提交订单')
                # 存在bug,买票提交且成功还在加载但是下一个异步任务已经开始，
                # 导致page.title取到的还是提交页面的title
                # 不设置也行，但是程序不会按时结束，但是可以加速抢票流程
                await page.waitFor(self.DEFAULT_CONFIG["WARN_WAIT"])
                if await page.title() in {"payment", "支付宝付款"}:
                    logger.info('polling 抢票成功，进入手机App订单管理付款')
                    sys.exit()
                await self.confirm_content_tip(page)

            if await self.is_refresh(page):
                await page.waitFor(2000)
                raise CongestionError("网络拥堵")

    async def confirm_content_tip(self, page):
        """处理点击提交订单后弹出的提示
        "出现库存不足"：开票前几分钟内出现这个可以继续捡票
        "有订单未支付"：在手机app中抢票成功；在前次抢票成功后，没有及时结束程序
        """
        confirm_content = await page.querySelectorAll('#confirmContent')
        if confirm_content:
            text = await (await confirm_content[0].getProperty('textContent')).jsonValue()
            logger.info(text)
            # 如有未支付订单提示
            if "未支付订单" in text:
                logger.info('confirm_content_tip 抢票成功，进入手机App订单管理付款')
                sys.exit()
            cancel = await page.xpath('//div[@id="confirmContent"]/../following-sibling::div/div[1]')
            await cancel[0].click()

    async def is_refresh(self, page):
        frames = page.frames
        if len(frames) > 1:
            frame = frames[1]
            warn_element = await frame.querySelector('div.warnning-text')
            text = await (await warn_element.getProperty('textContent')).jsonValue()
            text = text.replace("\n", "")
            logger.info(text)
            return "网络" in text
