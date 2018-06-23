import datetime
import os
import time

import exports
import logger
import skylink
import xbmc
import xbmcaddon


class SkylinkMonitor(xbmc.Monitor):
    _addon = xbmcaddon.Addon()
    _next_update = 0

    def __init__(self):
        xbmc.Monitor.__init__(self)
        ts = self._addon.getSetting('next_update')
        self._next_update = datetime.datetime.now() if ts == '' else datetime.datetime.fromtimestamp(float(ts))

    def notify(self, text, error=False):
        icon = 'DefaultIconError.png' if error else ''
        xbmc.executebuiltin('Notification("%s","%s",5000, %s)' % (self._addon.getAddonInfo('name'), text, icon))

    def onSettingsChanged(self):
        if not self.abortRequested():
            try:
                res = self.update()
                self.notify(self._addon.getLocalizedString(30400 + res))
            except skylink.SkylinkException as e:
                self.notify(self._addon.getLocalizedString(e.id), True)

    def shedule_next(self):
        dt = datetime.datetime.now() + datetime.timedelta(hours=12)
        logger.log.info('Next update %s' % dt)
        self._next_update = dt

    def update(self):
        self.shedule_next()

        s = skylink.Skylink(self._addon.getSetting('username'), self._addon.getSetting('password'),
                            xbmc.translatePath(self._addon.getAddonInfo('profile')).decode("utf-8"),
                            'skylink.sk' if int(self._addon.getSetting('provider')) == 0 else 'skylink.cz')
        channels = s.channels()

        logger.log.info('Updating playlist [%d channels]' % len(channels))
        try:
            path = os.path.join(self._addon.getSetting('playlist_folder'), self._addon.getSetting('playlist_file'))
            exports.create_m3u(channels, path)
            result = 1
        except IOError as e:
            logger.log.error(str(e))
            raise skylink.SkylinkException(30503)

        if bool(self._addon.getSetting('epg_generate')):
            days = int(self._addon.getSetting('epg_days'))
            logger.log.info('Updating EPG [%d days from %s]' % (days, datetime.datetime.now()))
            path = os.path.join(self._addon.getSetting('epp_folder'), self._addon.getSetting('epg_file'))
            try:
                exports.create_epg(channels, s.epg(channels, datetime.datetime.now(), days), path, self._addon)
                result = 2
            except IOError as e:
                logger.log.error(str(e))
                raise skylink.SkylinkException(30504)

        return result

    def tick(self):
        if datetime.datetime.now() > self._next_update:
            try:
                self.update()
            except skylink.UserNotDefinedException:
                pass
            except skylink.SkylinkException as e:
                self.notify(self._addon.getLocalizedString(e.id), True)

    def save(self):
        self._addon.setSetting('next_update', str(time.mktime(self._next_update.timetuple())))
        logger.log.info('Saving next update %s' % self._next_update)


if __name__ == '__main__':
    monitor = SkylinkMonitor()

    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            monitor.save()
            break

        monitor.tick()
