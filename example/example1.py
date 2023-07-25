import asyncio

from damai import ExecutionEngine
from damai.configs import Configs


ITEM_ID = 720288564028

loop = asyncio.get_event_loop()

engine = ExecutionEngine(Configs())

engine.order.add(ITEM_ID)
print(engine.order.views)

engine.add_task(ITEM_ID, '2023-07-22', '看台517元', 1)
engine.add_task(ITEM_ID, 2, 1, 1)

loop.create_task(engine.run_task(ITEM_ID))
print(engine.task.tasks)
