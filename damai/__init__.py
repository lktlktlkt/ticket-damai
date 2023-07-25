"""
仅供参考，学习。不得不经同意转载。

示例代码：examples timing.py

可配置`PERFORM`。可自行实现，继承`Perform`,按submit签名
'damai.performer.ApiFetchPerform'

Api：
    **必须配置Cookie

    提前运行程序，调度器准时发送请求，超过抢票时间则直接捡票。但是还是得依赖浏览器。

    开抢会无延迟默认抢两次(可自行配置)，后面请求会加延迟，进入捡票，太频繁会出现验证码。

Python3.7.5
"""


from damai.engine import ExecutionEngine
from damai.runner import Runner
