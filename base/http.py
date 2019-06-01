import json
import logging
import random

import aiohttp

from typing import Any, Mapping, List, Union

from aiohttp import ClientSession, ClientResponse
from aiohttp.typedefs import LooseHeaders
from aiosocksy import Socks5Auth
from aiosocksy.connector import ProxyConnector, ProxyClientRequest
from parsel import Selector

import base
from ext.config import cfg
from ext.url_hanlder import Url

logger = logging.getLogger(cfg.appname)


class Request:
    def __init__(self, url: Union[Url, str], method: str = 'GET', headers: LooseHeaders = None, data: Any = None,
                 _json: Any = None, timeout: int = 180, ext_data: Any = None):
        if isinstance(url, str):
            url = Url(url)
        self.url: Url = url
        self.method = method
        self.headers = headers
        self.data = data
        self._json = _json
        self.timeout = timeout
        self.ext_data = ext_data


class HttpEngine:
    name: str
    args: List[base.Args]
    input_args: Mapping
    proxies: Union[str, List]
    requested_items: Any

    # selector_type: str
    # selector_rule: Mapping

    def __init__(self, input_args: Mapping[str, str]):
        # todo: 辣眼睛，不解释
        if not self.name or not isinstance(self.name, str):
            raise ValueError('The value of name is invalid')
        if not self.args or not isinstance(self.args, (List, type(None))):
            raise ValueError('The value of args is invalid')
        if not isinstance(self.proxies, (str, List, type(None))):
            raise ValueError('The value of proxy is invalid')

        self.input_args = input_args
        if not self.proxies:
            self.proxies = []
        if isinstance(self.proxies, str):
            self.proxies = [self.proxies]
        if input_args['proxies']:
            self.proxies.extend(input_args['proxies'])
        self.session: ClientSession
        self.request_list: List[Request] = []
        self.requested_items = set()

    async def startup(self):
        """
        Design your initialization url, You can customize this method or
          add a Request instance directly to self.request_list. Remember,
          To ensure that there is an Rquest instance in self.request_list.

        :yield: Just base.http.Request else drop.
        """
        yield None

    async def run(self):
        """
        HTTP session initialization

        :return: None
        """
        conn = ProxyConnector()

        if not self.proxies:
            self.proxies = []
        if isinstance(self.proxies, str):
            self.proxies = [self.proxies]

        async with aiohttp.ClientSession(connector=conn, request_class=ProxyClientRequest) as self.session:
            try:
                async for ret in self.startup():
                    if isinstance(ret, Request):
                        await self.push_request(ret)
            except TypeError:
                logger.error('self.startup() returned in the wrong way, please use yield to return data.')
            async for req in self._get_request():
                await self.request_handler(req)

    async def request_filter(self, request: Request) -> bool:
        url = request.url.url_index() + request.url.path + request.url.query_string(flag=True)
        if url in self.requested_items:
            return True
        self.requested_items.add(url)
        return False

    async def request_handler(self, request: Request):
        """
        This method can be rewritten to handle the request exception, or do more.

        :param request: base.http.Request
        :return:
        """
        auth = None
        proxy_url = None
        if self.proxies:
            proxy_str = random.choice(self.proxies)
            proxy = Url(proxy_str)
            if proxy.scheme == 'socks5' or proxy.scheme == 'socks4':
                auth = Socks5Auth(proxy.username, proxy.password)
                proxy_url = proxy.url_index()
            elif proxy.scheme == 'http' or proxy.scheme == 'https':
                auth = aiohttp.BasicAuth(proxy.username, proxy.password)
                proxy_url = proxy.url_index()
        logger.info(f'Open {request.url.url_full()}')
        logger.debug(f'Current proxy: {proxy_url}')
        async with self.session.request(request.method, request.url.url_full(), headers=request.headers,
                                        data=request.data, timeout=request.timeout, json=request._json, proxy=proxy_url,
                                        proxy_auth=auth) as response:
            async for ret in self.process(response, request):
                if isinstance(ret, Request):
                    await self.push_request(ret)
                else:
                    await self.storage(ret)

    async def push_request(self, request: Request):
        """
        Push base.http.Request instance to list

        :param request: base.http.Request instance
        :return:
        """
        if not isinstance(request, Request):
            raise ValueError
        if await self.request_filter(request):
            return
        self.request_list.append(request)

    async def _get_request(self):
        """
        Get instances in self.request_list dynamically

        :yield: base.http.Request instance
        """
        while True:
            if not len(self.request_list) > 0:
                break
            yield self.request_list.pop(0)

    async def process(self, response: ClientResponse, request: Request = None):
        """
        Design your process, you can customize the method, url, header, body, and give the rest to tmw

        :yield: base.http.Request instance
          Other types of data are passed into the self.storage() function
        """
        yield None

    async def parse(self, text: str, request: Request = None, selector_type: str = 'xpath',
                    selector: Mapping[str, Any] = None):
        """
        You can customize it or use the default parsing function.

        :param text: Response text
        :param request: base.http.Request instance
        :param selector_type: Selector type
        :param selector: Selector rule
        :return: Parse result
        """

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

        output = {}
        if selector_type == 'xpath':
            output = parse_multilevel(text, selector)
        elif selector_type == 'api':
            output = json.loads(text)
        if request:
            output['source'] = request.url
        return output

    async def storage(self, result: Any):
        """
        You can customize it or use the default storage function. base.JSONExporter store is used by default.

        :param result: Parsing result
        :return: None
        """
        await base.EXPORTER.export(result)


class SearchEngine(HttpEngine):
    async def gen_url(self, url: str, querys: Mapping[str, Mapping[str, Any]], variables: Mapping[str, Any],
                      page_key: str = None, page_iterator: List = None):
        """
        Url for generating crawling search engine.

        :param url: Request url
        :param querys: Url query data, eg. {
                query_key1: { 'type': query_key_type, 'value': query_value },
                query_key2: { 'type': query_key_type, 'value': query_value }
            }
            query_key is the query key.
            query_key_type is the type of query key. const indicates that the query value is a constant. keyword
              indicates that the query value is a keyword
            query_value is the value of the query key, and the type is str or str list. If the query_key_type is
              keyword, str.format() function will be used to pass variables in for assignment.
        :param variables: The variable that str.format () assigns to keyword string.
        :param page_key: Query key representing the number of pages
        :param page_iterator: Page number iterates objects
        :yield: ext.url_handler.Url instance
        """

        # todo: querys 支持三种类型内容：常量、翻页、关键字
        #  关键字支持子类型有搜索语法
        url = Url(url)
        url.path.format(**self.input_args)
        keys = tuple(querys.keys())

        async def build(k_i: int, qs: Mapping[str, Mapping[str, Any]]):
            result = {}
            if not k_i < len(keys):
                yield {}
                return
            if isinstance(qs[keys[k_i]], Mapping):
                if qs[keys[k_i]]['type'] == 'const':
                    result[keys[k_i]] = qs[keys[k_i]]['value']
                    async for r in build(k_i + 1, qs):
                        result.update(r)
                        yield result
                elif qs[keys[k_i]]['type'] == 'keyword':
                    if not isinstance(qs[keys[k_i]]['value'], List):
                        qs[keys[k_i]]['value'] = [qs[keys[k_i]]['value']]
                    for it in qs[keys[k_i]]['value']:
                        result[keys[k_i]] = it.format(**variables)
                        async for r in build(k_i + 1, qs):
                            result.update(r)
                            yield result
            else:
                async for r in build(k_i + 1, qs):
                    result[keys[k_i]] = qs[keys[k_i]]
                    result.update(r)
                    yield result

        if page_key:
            for page in page_iterator:
                url.query[page_key] = page
                async for r in build(0, querys):
                    url.query.update(r)
                    yield url
        else:
            async for r in build(0, querys):
                url.query.update(r)
                yield url
