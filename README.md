# pick-ticket-damai

大麦捡漏/aiohttp  **仅供参考，学习**

### 环境

- Python >= 3.7

- 依赖模块安装：```pip install -r requirements.txt -i https://pypi.douban.com/simple```
- 运行：python run.py 

### 使用
- cookie：[详见](https://github.com/lktlktlkt/ticket-damai/issues/6);
     damai.example.cookie中实现了获取方法

- 主要配置：自用建议使用yaml进行配置

    ```python
    ITEM_ID = None  # 演唱会url中id或itemId
    CONCERT = 1   # 场次
    PRICE = 1    # 价格 格式 1 或者 [1, 2], 依次对应票档。目前只有`SalableQuantity`类支持list，否则值为下标0
    TICKET = 1   # 购票数量
    
    RUN_DATE = None   # 自定义抢票时间。为兼容优先购，有特权或者演出无优先购可不配置，格式：20230619122100
    
    COOKIE = None   # 必填
    
    """System"""
    # 可继承`ApiFetchPerform`，自定购票逻辑，在example.example3中有扩展
    PERFORM = 'damai.performer.ApiFetchPerform
    ```

- 在代码中主要关注performer，example3。类中有使用注释。

### ps
- 提前登录, 提前在大麦app中添加观演人及收货地址电话。