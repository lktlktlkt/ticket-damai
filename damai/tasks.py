import asyncio


class TaskManager:
    def __init__(self):
        self.tasks = {}

    def bind_task(self, name, task):
        if name not in self.tasks:
            self.tasks[name] = []
        self.tasks[name].append(task)

    def unbind_task(self, name):
        if name in self.tasks:
            del self.tasks[name]

    async def run_tasks(self, name):
        if name in self.tasks:
            tasks = self.tasks[name]
            tasks = [asyncio.create_task(func(*args)) for func, args in tasks]
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
            self.unbind_task(name)
            for task in tasks:
                if not task.done():
                    task.cancel()
