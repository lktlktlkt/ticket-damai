"""全局配置，在项目中某些类中已提前配置。可单独调用运行，不必依赖此模块。"""


"""Ticket"""
ITEM_ID = None
# 务必使用整数
CONCERT = 1    # 场次
PRICE = 1     # 价格 格式 1 或者 [1, 2]
TICKET = 1       # 购票数量

RUN_DATE = None    # 抢票时间，为了兼容优先购，有特权或者演出无优先购可不配置，格式：20230619122000
DELAY = 0   # 延迟，1=1s。大于0会在RUN_DATE加对应的时间

"""API"""
COOKIE = None   # api请求必填
FAST = 2     # 快速抢票的次数，超出后会加延迟
RETRY = 100    # 退出购票的条件，能确保不出现验证码可以把值配置的更高，持续时间长
APP_KEY = 12574478
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")

"""System"""
PERFORM = 'damai.performer.ApiFetchPerform'
LOG_LEVEL = "DEBUG"



