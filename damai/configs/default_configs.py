"""全局配置，在项目中某些类中已提前配置。可单独调用运行，不必依赖此模块。"""


"""Ticket"""
ITEM_ID = None
CONCERT = None    # 场次 格式："2023-07-15"  使用yaml配置暂时加引号
PRICE = None     # 价格串 格式："看台317元"
TICKET = 1       # 购票数量

RUN_DATE = None    # 抢票时间，为了兼容优先购，有特权或者演出无优先购可不配置，格式：202306191220
PORT = 9222    # 调式浏览器端口，Chrome，Edge可用
AUTO_JUMP = 1   # 1: 开启自动跳转至订单页，0: 关闭


"""API"""
COOKIE = None   # api请求必填
FAST = 2     # 快速抢票的次数，超出后会加延迟
RETRY = 100    # 退出购票的条件，能确保不出现验证码可以把值配置的更高，持续时间长
APP_KEY = 12574478
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")


"""WebDriver"""
# CRITICAL_WAIT: 必须设置，由于为异步任务，会造成实名人还未勾选成功，就提交订单。
# 可根据设备及网络调整
CRITICAL_WAIT = 450    # 1000=1s
# 详见damai.performer.WebDriverPerform.polling
WARN_WAIT = 100
SHUTDOWN = 60 * 10    # 选票持续时间

# BATCH = False    # 批量功能，未开发
# BATCH_WAIT = 0    # 如果开启了批量，建议这个设置一个批量 >=100


"""System"""
# 'damai.performer.WebDriverPerform'
PERFORM = 'damai.performer.ApiFetchPerform'




