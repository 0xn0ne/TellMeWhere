import importlib

from typing import List, Union

import base
from ext.config import cfg


def load_config():
    exp_name = cfg.get('SETTING.EXPORTER').split('.')
    base.EXPLOTER = getattr(importlib.import_module('.'.join(exp_name[:-1])), exp_name[-1])


CASE_LOWER = 'LOWER'
CASE_UPPER = 'UPPER'


def args_string_processing(s: Union[str, List[str]], case: str = None) -> List[str]:
    if not s:
        return []
    if isinstance(s, str):
        s = [s]
    res: List[str] = []
    for it in s:
        t_res: List[str] = []
        if it.startswith('file://'):
            with open(it[7:]) as _file:
                for line in _file.read().split('\n'):
                    if not line:
                        continue
                    t_res.append(line)
        else:
            t_res.append(it)
        for t in t_res:
            if not isinstance(case, str):
                res.append(t)
            elif case.upper() == CASE_UPPER:
                res.append(t.upper())
            elif case.upper() == CASE_LOWER:
                res.append(t.lower())
    return res
