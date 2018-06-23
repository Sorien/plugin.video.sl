import logging
import xbmc
import xbmcaddon


class XBMCHandler(logging.StreamHandler):
    xbmc_levels = {
        'DEBUG': 0,
        'INFO': 2,
        'WARNING': 3,
        'ERROR': 4,
        'LOGCRITICAL': 5,
    }

    def emit(self, record):
        xbmc_level = self.xbmc_levels.get(record.levelname)
        xbmc.log(self.format(record), xbmc_level)


def _get_logger():
    logger = logging.getLogger(xbmcaddon.Addon().getAddonInfo("id"))
    logger.setLevel(logging.DEBUG)
    handler = XBMCHandler()
    handler.setFormatter(logging.Formatter('[%(name)s] %(message)s'))
    logger.addHandler(handler)
    return logger


log = _get_logger()
