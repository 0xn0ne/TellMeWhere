import logging
import re
from urllib.parse import urljoin

from aiohttp import ClientResponse
from parsel import Selector

import ext
from base import Args
from base.http import SearchEngine, Request
from ext import cfg
from ext.url_hanlder import Url

logger = logging.getLogger(cfg.appname)


# todo:完成爬虫开发
#  无法应付 form 的 POST 请求和 js 跳转
class CrawlerSearch(SearchEngine):
    name: str = 'crawler'
    args: list = [
        Args('-cu', '--curl', type=str, nargs='+', help='Crawling target websites'),
        Args('-ck', '--ckeyword', type=str, nargs='+', help='Keywords that must be included in the page'),
    ]
    proxies = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    }
    allow_domain = set()
    retry_times = 3

    async def startup(self):
        self.input_args['curl'] = ext.args_string_processing(self.input_args['curl'])
        self.input_args['ckeyword'] = set(ext.args_string_processing(self.input_args['ckeyword']))

        flag = False
        if not self.allow_domain:
            flag = True
        for url in self.input_args['curl']:
            if flag:
                o_url = Url(url)
                self.allow_domain.add(o_url.netloc)
            yield Request(url, headers=self.headers, ext_data=self.input_args)

    async def process(self, response: ClientResponse, request: Request = None):
        if 'Content-Type' in response.headers and 'text' not in response.headers['Content-Type']:
            return
        text = await response.text()
        sel = Selector(text)
        for key in self.input_args['ckeyword']:
            if key in text:
                logger.debug(f'Find keyword {key} in html')
                yield {
                    'source': response.url.__str__(),
                    'keyword': key,
                    'brief': '...' + re.findall('.{,20}%s.{,20}' % key, text)[0] + '...'
                }
        for link in sel.xpath('//a/@href').extract():
            if link.startswith('javascript') or link.startswith('mailto:'):
                continue
            url = Url(urljoin(response.url.__str__(), link))
            if url.netloc in self.allow_domain:
                yield Request(url, headers=self.headers, ext_data=self.input_args)

    async def request_handler(self, request: Request):
        retry_times = self.retry_times
        while retry_times:
            try:
                await super().request_handler(request)
                break
            except Exception as e:
                retry_times -= 1
                logger.error(f'Retries remaining: {retry_times}. {e}')
