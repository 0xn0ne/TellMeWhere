import asyncio
import logging
from typing import List, Any

from aiohttp import ClientResponse

import ext
from base import Args
from base.http import SearchEngine, Request
from ext import cfg

logger = logging.getLogger(cfg.appname)


class WeixinSearch(SearchEngine):
    name: str = 'weixin'
    args: list = [
        Args('-wk', '--wkeyword', type=str, nargs='+', help='Weixin search keyword or file name'),
        Args('-ws', '--wsearch-start', type=int, help='Weixin start page', default=1),
        Args('-wt', '--wsearch-step', type=int, help='Weixin page turning steps', default=1),
        Args('-we', '--wsearch-end', type=int, help='Weixin end page', default=3),
        Args('-wi', '--winclude', action='store_true', help='Content must include content.')
    ]
    proxies = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    }
    exists_url = set()
    retry_times = 3

    async def startup(self):
        querys = {
            'type': {
                'type': 'const', 'value': '2'},
            'query': {
                'type': 'keyword', 'value': [
                    '{wkeyword}'
                ]},
            's_from': 'input',
        }

        for keyword in ext.args_string_processing(self.input_args['wkeyword']):
            nv = self.input_args
            nv['wkeyword'] = keyword
            async for url in self.gen_url('https://weixin.sogou.com/weixin', querys, nv, 'page',
                                          [page for page in range(self.input_args['wsearch_start'],
                                                                  self.input_args['wsearch_end'],
                                                                  self.input_args['wsearch_step'])]):
                # yield None
                yield Request(url.url_full(encoded=False), headers=self.headers, ext_data=nv)

    async def process(self, response: ClientResponse, request: Request = None):
        text = await response.text()
        if '请输入验证码' in text:
            sleep_time = 3600
            logger.warning(f'出现验证码，休眠 {sleep_time} s...')
            await asyncio.sleep(sleep_time)
            yield Request(response.url.__str__(), headers=self.headers, ext_data=request.ext_data)
        key_split: List[str] = []
        if self.input_args['winclude']:
            key_split = request.ext_data['wkeyword'].split()
        rule = {
            'box': {
                'selector': '//*[@class="txt-box"]',
                'child': {
                    'title': '//a//text()',
                    'href': '//a/@data-share',
                    'brief': '//*[@class="txt-info"]//text()', }
            }
        }
        data = await self.parse(text, selector=rule)
        for it in data['box']:
            logger.debug(f'Search keyword {key_split} in {it["brief"]} or {it["title"]}')
            for i in key_split:
                if self.input_args['winclude'] and i not in it['brief'] and i not in it['title']:
                    yield
            logger.debug(f'Find keyword {key_split} in {it["brief"]} or {it["title"]}')
            yield {
                'source': response.url.__str__(),
                'keyword': key_split,
                'href': it['href'],
                'title': it['title'],
                'brief': it['brief']
            }
            # yield Request(it['href'], headers=self.headers)
        # await asyncio.sleep(random.randint(12, 48))

    async def request_handler(self, request: Request):
        retry_times = self.retry_times
        while retry_times:
            # todo: 有 bug
            #  Retries remaining: 1. 'async for' requires an object with __aiter__ method, got coroutine
            # try:
            await super().request_handler(request)
            break
            # except Exception as e:
            #     retry_times -= 1
            #     logger.error(f'Retries remaining: {retry_times}. {e}')

    async def storage(self, result: Any):
        if result['href'] not in self.exists_url:
            self.exists_url.add(result['href'])
            await super().storage(result)
