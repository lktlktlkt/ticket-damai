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

    def add_task(self, name: Union[int, str], concert: Union[int, str, list],
                 price: Union[int, str], tickets: int):
        """添加异步任务至管理器
        name: 取决于在OrderView.add的参数
        concert, price, tickets：分别代表场次 价位 需购数量
        """
        if not isinstance(tickets, int):
            raise TypeError('购票数量必须为正整数')

        concert = concert[0] if isinstance(concert, list) else concert
        bind = self.order.views[name]
        # 这个判断逻辑是要修改的，暂时这样用
        if isinstance(price, str):
            sku_list = bind[concert]["skuList"]
            sku = next(sku for sku in sku_list if price == sku["priceName"])
        elif isinstance(price, (int, list)):
            price = price if isinstance(price, int) else price[0]
            sku_list = bind[list(bind.keys())[concert - 1]]["skuList"]
            sku = sku_list[price - 1]
        else:
            raise TypeError('`价格`支持的格式为 int or str or list')

        self.task.bind_task(name, (self.perform.submit, (sku["itemId"], sku["skuId"], tickets)))

    async def run_task(self, name):
        await self.task.run_tasks(name)
