import argparse
import json
import time
import logging
from argparse import Action
from typing import Any, Union, Optional, Tuple, Type, List

from ext import cfg

logger = logging.getLogger(cfg.appname)


class Exporter:
    async def export(self, data: Any):
        raise NotImplemented

    def closed(self):
        raise NotImplemented


class JSONExporter(Exporter):
    raw_data = []

    def __init__(self, filename: str = None, encoding: str = 'utf-8', cls: Any = None):
        if not filename:
            filename = f'data_{int(time.time())}.json'
        self.filename = filename
        self.encoding = encoding
        self.cls = cls

    async def export(self, data: Any):
        logger.debug(f'Save json data {data}')
        self.raw_data.append(data)
        with open(self.filename, mode='w', encoding=self.encoding) as _file:
            json.dump(self.raw_data, _file, cls=self.cls)

    async def closed(self):
        pass


class Args:
    def __init__(self, *name_or_flags: str, action: Union[str, Type[Action]] = None, nargs: Union[int, str] = None,
                 default: Any = None, type: Type = None, choices: List[Any] = None, required: bool = None,
                 help: Optional[str] = None, metavar: Union[str, Tuple[str, ...]] = None):
        self.name_or_flags = name_or_flags
        self.action = action
        self.nargs = nargs
        self.default = default
        self.type = type
        self.choices = choices
        self.required = required
        self.help = help
        self.metavar = metavar

    def to_map(self):
        kwargs = {
            'action': self.action,
            'nargs': self.nargs,
            'default': self.default,
            'type': self.type,
            'choices': self.choices,
            'required': self.required,
            'help': self.help,
            'metavar': self.metavar
        }
        if self.action:
            del kwargs['nargs']
            del kwargs['type']
            del kwargs['choices']
            del kwargs['metavar']
        return kwargs

    def get_name(self):
        t_name = self.name_or_flags[0].rstrip('-').replace('-', '_')
        for name in self.name_or_flags:
            if name.startswith('--'):
                t_name = name.lstrip('-').replace('-', '_')
                return t_name
        return t_name


EXPORTER: Exporter = None
