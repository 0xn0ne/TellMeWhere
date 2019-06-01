#!/usr/bin/python
# Since there is no good assignment scheme for the "BaseConfig" class,
# this will be the case for the time being.
import json
from typing import Any, Mapping

import toml
import os
import logging


def depth_update_map(out, up):
    if not isinstance(out, Mapping):
        return up
    for key, val in up.items():
        if isinstance(val, Mapping):
            res = depth_update_map(out.get(key, {}), val)
            out[key] = res
        else:
            out[key] = up[key]
    return out


class BaseConfig:
    def __init__(self, path: str = 'app.conf', encoding: str = 'utf-8-sig', format: str = 'toml'):
        '''
        :param path: Config file path
        :param encoding: Config file encoding format
        :param format: Storage content protocol
        '''
        self.path: str = path
        self.encoding: str = encoding
        self.config: dict = self.__base_config__
        self.format: str = format

        if os.path.isfile(self.path):
            with open(self.path, 'r', encoding=self.encoding) as _file:
                if self.format.lower() == 'toml':
                    self.config = depth_update_map(
                        self.config, toml.load(_file))
                elif self.format.lower() == 'json':
                    self.config = depth_update_map(
                        self.config, json.load(_file))
                else:
                    raise TypeError(f'"{format}" format is not supported.')

    @property
    def __base_config__(self):
        return {
            'VERSION': '1.0.0',
            'APP_NAME': 'CONFIG_TEMPLATE',
            'SETTING': {
                'LOG_LEVEL': logging.INFO,
            }
        }

    def closed(self):
        '''
        Close and save the configuration.

        :return:
        '''
        with open(self.path, 'w', encoding=self.encoding) as _file:
            if self.format.lower() == 'toml':
                toml.dump(self.config, _file)
            elif self.format.lower() == 'json':
                json.dump(self.config, _file)
            else:
                raise TypeError(f'"{format}" format is not supported.')

    def get(self, keys: str, sep: str = '.') -> Any:
        '''
        "List" type is not processed,

        :param keys: Divisible keys (
            eg. "setting.redis.port" can get "values" from {"setting": {"redis": {"port": values}}})
        :param sep: Separator, default "."
        :return:
        '''
        keys = keys.split(sep)
        pointer = self.config
        for key in keys:
            pointer = pointer[key]
        return pointer

    def set(self, keys: str, values: Any, sep: str = '.'):
        '''
        "List" type is not processed,

        :param keys: Divisible keys
        :param sep: Separator
        :return:
        '''
        keys = keys.split(sep)
        pointer = self.config
        for key in keys[:-1]:
            pointer = pointer[key]
        pointer[keys[-1]] = values


class AppConfig(BaseConfig):
    @property
    def __base_config__(self):
        return {
            'VERSION': '1.0.0',
            'APP_NAME': 'TellMeWhere',
            'SETTING': {
                'LOG_LEVEL': logging.INFO,
                'EXPORTER': 'base.JSONExporter'
            }
        }

    @property
    def version(self):
        return self.config['VERSION']

    @version.setter
    def version(self, version):
        self.config['VERSION'] = version.lower()

    @property
    def appname(self):
        return self.config['APP_NAME']

    @appname.setter
    def appname(self, appname):
        self.config['APP_NAME'] = appname.upper()

    @property
    def setting(self):
        return self.config['SETTING']

    def set_setting(self, key, data):
        self.config['SETTING'][key] = data


class RuleConfig(BaseConfig):
    def __init__(self, path: str = 'engine.json', encoding: str = 'utf-8-sig', format: str = 'json'):
        super().__init__(path, encoding, format)

    @property
    def __base_config__(self):
        return [
            {
                'protocol': 'HTTP',
                'name': 'google',
                'method': 'GET',
                'url': 'https://www.google.com/search',
                'query': {
                    'q': {'type': 'key', 'value': ['{keyword}', 'inurl:{url}']},
                    'start': {'type': 'pages', 'value': 10},
                    'num': {'type': 'const', 'value': 10}
                },
                'selector': 'xpath',
                'parse': {
                    'result': {
                        'selector': '//div[@class="g"]',
                        'child': {
                            'title': '//*[@class="LC20lb"]/text()',
                            'url': '//div[@class="r"]/a/@href',
                            'brief': '//*[@class="st"]/text()'
                        }
                    },
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
                },
                'body': None,
                'proxies': 'socks5://127.0.0.1:1080'
            },
            {
                'protocol': 'HTTP',
                'name': 'bing',
                'method': 'GET',
                'url': 'https://www.bing.com/search',
                'query': {
                    'q': {'type': 'key', 'value': ['{keyword}', '{url}']},
                    'first': {'type': 'pages', 'value': 10}
                },
                'selector': 'xpath',
                'parse': {
                    'result': {
                        'selector': '//li[@class="b_algo"]',
                        'child': {
                            'title': '//h2/a/text()',
                            'url': '//h2/a/@href',
                            'brief': '//div[@class="b_caption"]/p/text()'
                        }
                    },
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
                },
                'body': None,
                'proxies': None
            },
            {
                'protocol': 'HTTP',
                'name': 'bing_cn',
                'method': 'GET',
                'url': 'https://cn.bing.com/search',
                'query': {
                    'q': {'type': 'key', 'value': ['{keyword}', '{url}']},
                    'first': {'type': 'pages', 'value': 10}
                },
                'selector': 'xpath',
                'parse': {
                    'result': {
                        'selector': '//li[@class="b_algo"]',
                        'child': {
                            'title': '//h2/a/text()',
                            'url': '//h2/a/@href',
                            'brief': '//div[@class="b_caption"]/p/text()'
                        }
                    },
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
                },
                'body': None,
                'proxies': None
            },
            {
                'protocol': 'HTTP',
                'name': 'baidu',
                'method': 'GET',
                'url': 'https://www.baidu.com/s',
                'query': {
                    'wd': {'type': 'key', 'value': ['intitle:{keyword}', 'inurl:{url}']},
                    'pn': {'type': 'pages', 'value': 10},
                    'rn': {'type': 'const', 'value': 10}
                },
                'selector': 'xpath',
                'parse': {
                    'result': {
                        'selector': '//*[contains(@class, "c-container")]',
                        'child': {
                            'title': '//*[contains(@class, "t")]/a/text()',
                            'url': '//*[contains(@class, "t")]/a/@href',
                            'brief': '//*[contains(@class, "c-abstract") or contains(@class, "f13")]/text()'
                        }
                    },
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
                },
                'body': None,
                'proxies': None
            },
            {
                'protocol': 'HTTP',
                'name': 'github',
                'method': 'GET',
                'url': 'https://www.github.com/search',
                'query': {
                    'q': {'type': 'key', 'value': ['{keyword} in:file,path', '{keyword} extension:{ext}',
                                                   'filename:{keyword} language:{lang}']},
                    'p': {'type': 'pages', 'value': 1},
                    'type': {'type': 'const', 'value': 'Repositories'}
                },
                'selector': 'xpath',
                'parse': {
                    'result': {
                        'selector': '//*[contains(@class, "repo-list-item")]',
                        'child': {
                            'title': '//h3/a/text()',
                            'url': '//h3/a/@href',
                            'brief': '//*[contains(@class, "d-inline-block text-gray")]/text()',
                            'updated_time': '//relative-time/text()'
                        }
                    },
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
                },
                'body': None,
                'proxies': None
            },
            {
                'protocol': 'HTTP',
                'name': 'pansou',
                'method': 'GET',
                'url': 'http://106.15.195.249:8011/search_new',
                'query': {
                    'q': {'type': 'key', 'value': ['{keyword}']},
                    'p': {'type': 'pages', 'value': 1},
                },
                'selector': 'api',
                'parse': {},
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
                },
                'body': None,
                'proxies': None
            },
            {
                'protocol': 'HTTP',
                'name': 'wowenda',
                'method': 'GET',
                'url': 'http://wowenda.com/search',
                'query': {
                    'wd': {'type': 'key', 'value': ['{keyword}']},
                    'page': {'type': 'pages', 'value': 1},
                },
                'selector': 'xpath',
                'parse': {
                    'ul': {
                        'selector': '//ul',
                        'child': {
                            'title': '//li[@class="bt"]/text()',
                            'url': '//li[@class="bt"]/a/@href',
                            'brief': '//li[@class="sm"]/a/text()',
                        }
                    }
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
                },
                'body': None,
                'proxies': None
            },
        ]


cfg = AppConfig()

if __name__ == '__main__':
    tmp_config = BaseConfig()
    tmp_config.config = {'111': {'222': {'333': 100}}}
    print(tmp_config.get('111.222'))
    tmp_config.set('111', 9999)
    print(tmp_config.config)
