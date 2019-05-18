import datetime
import logging
import sys

from ext.config import cfg

APPNAME = cfg.appname
LOG_LEVEL = logging.DEBUG

logger = logging.getLogger(APPNAME)
formatter = logging.Formatter(
    '[%(asctime)s][%(filename)s][line:%(lineno)d][%(levelname)s]:%(message)s')

# 文件日志
file_handler = logging.FileHandler('%s_%s.log' % (APPNAME, datetime.datetime.now().strftime('%Y%m%d')),
                                   encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 控制台日志
console_handler = logging.StreamHandler(sys.stdout)
console_handler.formatter = formatter
logger.addHandler(console_handler)

# 日志等级
logger.setLevel(cfg.setting['LOG_LEVEL'])
