import asyncio
import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from damai.configs import Configs
from damai.engine import ExecutionEngine


class Runner:

    def __init__(self, configs=None):
        if isinstance(configs, dict) or configs is None:
            self.configs = Configs(configs)

        logger.add("logs/{time:YYYY-MM-DD}.log", rotation="1 day", level=self.configs["LOG_LEVEL"])

        self.engine = ExecutionEngine(self.configs)

        self.loop = asyncio.get_event_loop()

        self._scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
        self.single = False

    def start(self):
        self._execute_accord_to_config()
        if self.single:
            self._scheduler.start()
            try:
                self.loop.run_forever()
            except (Exception,):
                pass
        self.loop.run_until_complete(self.engine.perform.close())

    def _execute_accord_to_config(self):
        item_id = self.configs["ITEM_ID"]
        self.engine.order.add(item_id)
        self.engine.add_task(item_id, self.configs["CONCERT"],
                             self.configs["PRICE"], self.configs["TICKET"])
        name, date = self.engine.order.get_sell_item(item_id)

        d = self.configs.get("RUN_DATE", None)
        if d:
            date = datetime.datetime.strptime(str(d), "%Y%m%d%H%M%S").timestamp()

        delay = int(self.configs.get("DELAY", 0))
        if delay:
            date = date + delay

        run_date = datetime.datetime.fromtimestamp(date)
        logger.info(f'\n{name}\n抢票时间：{run_date}\n场次：{self.configs["CONCERT"]}\n'
                    f'价格：{self.configs["PRICE"]}\n数量：{self.configs["TICKET"]}')
        if run_date >= datetime.datetime.now():
            self.single = True
            self._scheduler.add_job(self.engine.run_task, 'date', run_date=run_date,
                                    args=(item_id, ), name=name)
        else:
            self.loop.run_until_complete(self.engine.run_task(item_id))


