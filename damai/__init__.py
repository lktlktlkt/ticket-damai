"""
仅供参考，学习。不得不经同意转载。

上个仓库不小心在新的push中提交了自己的敏感数据。

前提，使用谷歌浏览器或Edge，然后使用浏览器远程调试功能？"
谷歌一下" pyppeteer connect browserWSEndpoint 或者 pyppeteer connect browserURL
示例代码：examples timing.py

默认使用api购票，可配置`PERFORM`。可自行实现，继承`Perform`,按submit签名
'damai.performer.ApiFetchPerform'
'damai.performer.WebDriverPerform'

WebDriver：
    抢是抢不过直接发请求的，但也不是不能用，主要捡漏。如果是第一次放票应该能捡回流票，
    要是抢的是退票那基本抢不到。

    实测提交订单并不是疯狂发请求过去，能抢成功基本点击两次就可以了。出现提示框再刷新。
    最近几天的演唱会中几十万想看的基本都捡票成功。

Api：
    **必须配置Cookie

    提前运行程序，调度器准时发送请求，超过抢票时间则直接捡票。但是还是得依赖浏览器。

    开抢会无延迟默认抢两次(可自行配置)，后面请求会加延迟，进入捡票，太频繁会出现验证码。
    可能得加毫秒延迟，测试中第一次导致了生成订单失败(调度器开启生成订单，商品已过期，过快导致了)。

Python3.7.5
"""


from damai.engine import ExecutionEngine
from damai.runner import Runner
