from typing import Union, List

from base import Args
from base.http import HttpEngine, SearchEngine, Request


# todo: 完成样例编写
#  对常用搜索语法进行支持
#  "" 强制关键词
#  inurl: 必须存在 url 中
#  filetype: 指定文件类型
#  intext: 必须存在文本中
#  intitle: 必须存在标题中
#  cache: 缓存页面
#  info: ???
#  link: ???


class Example(HttpEngine):
    # Engine name
    name: str = 'example'
    # Engine args for add_argument
    args: list = [
        Args('-k', '--keyword', help='Example keyword')
    ]
    args_input: dict = {}
    # Proxy server used. eg: socks5://127.0.0.1:1080
    proxies: Union[str, List] = None
    # The type of content selector used
    selector_type: str = 'xpath'
    # Selector rule used
    selector_rule: dict = {}

    async def requests(self):
        yield None


class ExampleSearch(SearchEngine):
    # Engine name
    name: str = 'example_search'
    # Engine args for add_argument
    args: list = [
        Args('-sk', '--keyword', help='Example search keyword'),
        Args('-ss', '--search-start', help='Example start page'),
        Args('-si', '--search-step', help='Example page turning steps'),
        Args('-se', '--search-end', help='Example end page')
    ]
    args_input: dict = {}
    # Proxy server used. eg: socks5://127.0.0.1:1080
    proxies: Union[str, List] = None
    # The type of content selector used
    selector_type: str = 'xpath'
    # Selector rule used
    selector_rule: dict = {}


    async def startup(self):
        # reme
        # use this set start
        Request('http://example.com')
        # or use this
        yield Request('http://example.com')

    async def requests(self):
        yield None
