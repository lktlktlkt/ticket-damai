import hashlib
import json
import time
from importlib import import_module
from urllib import parse


def dumps(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def get_sign(token, t, app_key, data):
    md5 = hashlib.md5()
    md5.update((token + '&' + str(t) + '&' + str(app_key) + '&' + data).encode('utf-8'))
    return md5.hexdigest()


def timestamp():
    return int(time.time() * 1000)


def load_object(path):
    if not isinstance(path, str):
        if callable(path):
            return path
        else:
            raise TypeError("Unexpected argument type, expected string "
                            "or object, got: %s" % type(path))

    try:
        dot = path.rindex('.')
    except ValueError:
        raise ValueError(f"Error loading object '{path}': not a full path")

    module, name = path[:dot], path[dot + 1:]
    mod = import_module(module)

    try:
        obj = getattr(mod, name)
    except AttributeError:
        raise NameError(f"Module '{module}' doesn't define any object named '{name}'")

    return obj


def make_ticket_data(order_build_data: dict):
    """构造订单form-data，购票人数，直接按账号实名人添加的顺序，不做详细处理
    order_build_data: 生成接口响应数据
    """
    params = {}
    data_field = ['dmContactName', 'dmContactEmail', 'dmContactPhone', 'dmViewer',
                  'dmDeliverySelectCard', 'dmDeliveryAddress', 'dmPayType',
                  'confirmOrder_1', 'dmEttributesHiddenBlock_DmAttributesBlock', 'item']
    data = order_build_data["data"]
    data_dict = {key: data[key] for field in data_field for key in data.keys() if
                 field == key or field == key.split('_')[0]}

    viewer = next(key for key in data_dict.keys() if key.split('_')[0] == "dmViewer")

    buyer_total_num = data_dict[viewer]["fields"].get('buyerTotalNum')
    if buyer_total_num:
        data_dict[viewer]["fields"]["selectedNum"] = buyer_total_num
        for index in range(buyer_total_num):
            data_dict[viewer]["fields"]["viewerList"][index]["isUsed"] = True
    params['data'] = dumps(data_dict).replace('"true"', 'true')

    linkage = order_build_data["linkage"]
    linkage_dict = {field: linkage[field] for field in ['common', 'signature']}
    linkage_dict['common'].pop('queryParams', None)
    linkage_dict['common'].pop('structures', None)
    params['linkage'] = dumps(linkage_dict)

    hierarchy = order_build_data["hierarchy"]
    hierarchy_dict = {field: hierarchy[field] for field in ['structure']}
    params['hierarchy'] = dumps(hierarchy_dict)

    feature = {
            "subChannel": "damai@damaih5_h5",
            "returnUrl": "https://m.damai.cn/damai/pay-success/index.html?"
                         "spm=a2o71.orderconfirm.bottom.dconfirm&sqm=dianying.h5.unknown.value",
            "serviceVersion": "2.0.0", "dataTags": "sqm:dianying.h5.unknown.value"
         }

    return dumps({"params": dumps(params), "feature": dumps(feature)})


def make_order_url(item_id, sku_id, tickets):
    prefix = {
        "damai": "1", "channel": "damai_app", "umpChannel": "10002",
        "atomSplit": "1", "serviceVersion": "1.8.5"
    }
    url = "https://m.damai.cn/app/dmfe/h5-ultron-buy/index.html?"
    ex_params_str = "exParams=" + parse.quote(json.dumps(prefix, separators=(",", ":")))
    buy_param = f'{item_id}_{tickets}_{sku_id}'
    params = {'buyParam': buy_param, 'buyNow': "true", 'privilegeActId': ""}
    return f'{url}{ex_params_str}&{parse.urlencode(params)}'
