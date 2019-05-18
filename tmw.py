import argparse
import json
import logging
import re
import aiohttp
import asyncio

from aiohttp import ClientProxyConnectionError
from aiosocksy import Socks5Auth
from aiosocksy.connector import ProxyConnector, ProxyClientRequest
from parsel import Selector
from typing import Union, List, Mapping

from ext.config import cfg, BaseConfig, RuleConfig
from ext.url_hanlder import Url
import ext.logger

logger = logging.getLogger(cfg.appname)


# todo: 配置检查
def config_load():
    pass


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
    def __init__(self, args: dict, rules: BaseConfig = None):
        if not rules:
            self.rules = RuleConfig()
        self.args = args
        logger.info(f'Start running...')

    async def tell_me(self):
        for item in self.rules.config:
            if self.args['engine'] and item['name'] not in self.args['engine']:
                continue
            logger.info(f'Start handler protocol: {item["protocol"]}, target {item["name"]}')
            net = NetwordHandler(item, self.args, item['protocol'])
            async for net_generator in net.run():
                await self.output_handler(item['name'], self.content_handler(net_generator, item))

    async def content_handler(self, text_generator, rules: dict):
        def parse_multilevel(content: str, sel_rules):
            sel: Selector = Selector(content)
            result = {}
            for name in sel_rules:
                if isinstance(sel_rules[name], Mapping):
                    result[name] = []
                    for elm in sel.xpath(sel_rules[name]['selector']):
                        result[name].append(parse_multilevel(elm.extract(), sel_rules[name]['child']))
                elif isinstance(sel_rules[name], str):
                    result[name] = ''.join(sel.xpath(sel_rules[name]).extract())
            return result

        async for text, source in text_generator:
            # print('temp_debug', text)
            # exit()
            result = None
            if rules['selector'] == 'xpath':
                result = parse_multilevel(text, rules['parse'])
            elif rules['selector'] == 'api':
                result = json.loads(text)

            result['source'] = source
            yield result

    async def output_handler(self, name: str, result_generator):
        summary = {}
        def count_keys_nums(obj:dict):
            count = 0
            count += len(obj)
            for k in obj:
                if isinstance(obj[k], Mapping):
                    count += count_keys_nums(obj[k])
            return count
        async for result in result_generator:
            if name not in summary:
                summary[name] = []
            logger.debug(f'Output: {result}')
            summary[name].append(result)
        if self.args['output']:
            output_format = [it.upper() for it in self.args['output']]
        else:
            output_format = []
        if 'JSON' in output_format:
            logger.info(f'Output JSON format...')
            with open('%s_%s.json' % (cfg.appname, name), 'w') as _file:
                json.dump(summary, _file)

    def closed(self):
        self.rules.closed()


class NetwordHandler:
    def __init__(self, rules: dict, args: dict, protocol: str = 'HTTP'):
        self.rules = rules
        self.args = args
        self.protocol = protocol

    async def run(self):
        if self.protocol.upper() == 'HTTP':
            yield self.http_handler()

    async def http_handler(self) -> Union[str, bytes]:
        conn = None
        auth = None
        proxy_url = None
        if self.rules['proxies']:
            proxies = Url(self.rules['proxies'])
            if proxies.scheme == 'socks5' or proxies.scheme == 'socks4':
                auth = Socks5Auth(proxies.username, proxies.password)
                conn = ProxyConnector()
                proxy_url = proxies.url_index()
                # conn = SocksConnector.from_url(proxies.url_index())
            elif proxies.scheme == 'http' or proxies.scheme == 'https':
                auth = aiohttp.BasicAuth(proxies.username, proxies.password)
                proxy_url = proxies.url_index()
        async with aiohttp.ClientSession(connector=conn, request_class=ProxyClientRequest) as session:
            async for url in self.gen_url(self.rules['url'], self.rules['query']):
                logger.info(f'Request url: {url.url_full()}')
                try:
                    async with session.request(self.rules['method'], url.url_full(), headers=self.rules['headers'],
                                               data=self.rules['body'], proxy=proxy_url, proxy_auth=auth) as response:
                        yield await response.text(), url.url_full()
                except ClientProxyConnectionError:
                    logger.error(f'Client proxy connection error. {proxy_url}')

    async def gen_url(self, base_url: str, querys: dict):
        round_0 = True
        start = self.args['start'] if self.args['start'] else 0
        end = self.args['end'] if self.args['end'] else 3
        url = Url(base_url)
        url.path.format(**self.args)
        while start < end:
            for query in querys:
                if querys[query]['type'] == 'const' and round_0:
                    url.query[query] = querys[query]['value']
                elif querys[query]['type'] == 'pages':
                    url.query[query] = start * querys[query]['value']
                    if round_0:
                        continue
                    yield url
                elif querys[query]['type'] == 'key':
                    for key in querys[query]['value']:
                        url.query[query] = key.format(**self.args)
                        if round_0 and not len(querys[query]['value']) > 1:
                            continue
                        yield url
            if round_0:
                yield url
                round_0 = False
            start += 1


async def main(args: dict):
    tmw = TellMeWhere(args)
    await tmw.tell_me()
    tmw.closed()


if __name__ == '__main__':
    rules = RuleConfig()
    parser = argparse.ArgumentParser()

    engines = []
    for engine in rules.config:
        engines.append(engine['name'])
    parser.add_argument('-e', '--engine', nargs='*', type=str, choices=engines, metavar='name',
                        help='Specifies the name of the engine called')
    parser.add_argument('-o', '--output', nargs='*', type=str, choices=['json'], required=False,
                        metavar='number',
                        help='Output results in json, xml format')
    parser.add_argument('--start', type=int, required=False, metavar='number',
                        help='Number of pages to start searching')
    parser.add_argument('--end', type=int, required=False, metavar='number',
                        help='Number of pages to stop searching')
    sub_args_perser = parser.add_argument_group('Subparameter')
    keys = []
    for engine in rules.config:
        if engine['protocol'].upper() == 'HTTP':
            if engine['query']:
                for query in engine['query']:
                    if isinstance(engine['query'][query]['value'], List):
                        for value in engine['query'][query]['value']:
                            keys.extend(re.findall(r'{(.+?)}', value))
            if engine['body']:
                for body_key in engine['body']:
                    if isinstance(engine['body'][body_key]['value'], List):
                        for value in engine['body'][body_key]['value']:
                            keys.extend(re.findall(r'{(.+?)}', value))
    keys = set(keys)
    for key in keys:
        sub_args_perser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(main(vars(args)))
    LOOP.close()
    cfg.closed()
