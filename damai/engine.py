from typing import Union

from damai.orderview import OrderView
from damai.tasks import TaskManager

from damai.utils import load_object


class ExecutionEngine:

    def __init__(self, configs):
        self.configs = configs
        self.task = TaskManager()
        self.order = OrderView()
        self.perform = load_object(self.configs["PERFORM"])()
        self.perform.update_default_config(self.configs)

    def add_task(self, name: Union[int, str], concert: str, price: str, tickets: int):
        """添加异步任务至管理器
        name: 取决于在OrderView.add的参数
        concert, price, tickets：分别代表场次 价位 需购数量
        """
        bind = self.order.views[name]
        sku_list = bind[concert]["skuList"]
        sku = next(sku for sku in sku_list if price == sku["priceName"])
        self.task.bind_task(name, (self.perform.submit, (sku["itemId"], sku["skuId"], tickets)))

    async def run_task(self, name):
        await self.task.run_tasks(name)
