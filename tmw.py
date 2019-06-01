import argparse
import importlib
import logging
import os
import asyncio
import re

from typing import List, Mapping, Any, Type

import base
from base.http import HttpEngine
from ext.config import cfg, RuleConfig
import ext.logger

logger = logging.getLogger(cfg.appname)


def load_config():
    exp_name = cfg.get('SETTING.EXPORTER').split('.')
    base.EXPORTER = getattr(importlib.import_module('.'.join(exp_name[:-1])), exp_name[-1])()


def load_engines(path='engines') -> List[Type[HttpEngine]]:
    imp_str = path.replace('/', '.')
    imp_str = imp_str.replace('\\', '.')
    engines = []
    for f_name in os.listdir(path):
        if f_name.startswith('_') or not re.match(r'[\w]+\.py', f_name) or not os.path.isfile(path + '/' + f_name):
            continue
        f_module = importlib.import_module(imp_str + '.' + f_name[:-3])
        for c_name in dir(f_module):
            if c_name.startswith('_'):
                continue
            cls = getattr(f_module, c_name)
            if isinstance(cls, type) and issubclass(cls, HttpEngine) and getattr(cls, 'name', None):
                engines.append(cls)
    return engines


def get_engines_name():
    return [cls.name for cls in load_engines()]


# todo: 引擎配置检查
def engine_config_handler():
    pass


# todo: 事实证明使用异步想加速真的是太天真，谷哥在个别页面很爽快的问要验证码，
#  最后还是要 delay，记得加 delay
# todo: 有的搜索引擎很鸡贼，在没有翻到最后一页的情况下，有些页面显示内容很多，
#  有些页面结果很少，而且网上没有控制搜索内容条数的参数，需要想个巧妙的办法。
# todo: 有些搜索引擎吃相很难看，为了更好的后台统计，强制通过自身 url 跳转，
#  美曰其名为保护用户，不得不为惊雷算法拍手叫好。
class TellMeWhere:
    def __init__(self, input_args: Mapping[str, Any]):
        logger.info(f'Start running...')
        self.args = input_args
        self.engines = load_engines()

    async def tell_me(self):
        load_config()
        for engine in self.engines:
            t_dict = {}
            t_dict['proxies'] = self.args['proxies']
            for arg in engine.args:
                if arg.get_name() in self.args:
                    t_dict[arg.get_name()] = self.args[arg.get_name()]
            if engine.name in self.args['engine']:
                e = engine(t_dict)
                # await e.run()
                await e.run()


    def closed(self):
        cfg.closed()


async def startup(args: Mapping[str, Any]):
    tmw = TellMeWhere(args)
    await tmw.tell_me()
    tmw.closed()


if __name__ == '__main__':
    rules = RuleConfig()
    parser = argparse.ArgumentParser()
    get_engines_name()

    # todo: 尝试寻找可以读取多个层次的加参方法
    #  读取结果如：{'engine': ['baidu'], 'baidu': {'keyword': 'xxx', 'title': 'aaa'}}
    #  忘了这个计划吧
    engine_names = get_engines_name()
    parser.add_argument('-e', '--engine', nargs='+', type=str, choices=engine_names, required=True, metavar='name',
                        help='Specifies the name of the engine called. Opt: %s' % '/'.join(engine_names))
    parser.add_argument('-p', '--proxies', nargs='*', type=str, metavar='url',
                        help='HTTP/HTTPS/SOCKS4/SOCKS5 proxy or file path. eg. socks5://127.0.0.1:1080')
    # parser.add_argument('-o', '--output', nargs='*', type=str, choices=['json'], required=False,
    #                     metavar='format', help='Output results in json format')

    # Load engine args
    engines = load_engines()
    for engine in load_engines():
        if not engine.args:
            continue
        engine_args_group = parser.add_argument_group(engine.name, conflict_handler='resolve')
        for arg in engine.args:
            engine_args_group.add_argument(*arg.name_or_flags, **arg.to_map())
    args = parser.parse_args()

    args = vars(args)
    # Proxy list preprocessing
    t_proxies = []
    if args['proxies']:
        for proxy in args['proxies']:
            t_proxies.extend(ext.args_string_processing(proxy, ext.CASE_LOWER))
    args['proxies'] = t_proxies

    # Program run
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(startup(args))
    LOOP.close()
    cfg.closed()
