import datetime
import os
import time
import requests
import exports
import logger
import skylink
import xbmc
import xbmcaddon
import utils


class SkylinkMonitor(xbmc.Monitor):
    _addon = None
    _next_update = 0

    def __init__(self):
        xbmc.Monitor.__init__(self)
        self._addon = xbmcaddon.Addon()
        ts = self._addon.getSetting('next_update')
        self._next_update = datetime.datetime.now() if ts == '' else datetime.datetime.fromtimestamp(float(ts))

    def __del__(self):
        logger.log.info('service destroyed')

    def notify(self, text, error=False):
        text = text.encode("utf-8") if type(text) is unicode else text
        icon = 'DefaultIconError.png' if error else ''
        xbmc.executebuiltin('Notification("%s","%s",5000,%s)' % (self._addon.getAddonInfo('name').encode("utf-8"), text, icon))

    def onSettingsChanged(self):
        self._addon = xbmcaddon.Addon()  # refresh for updated settings!
        if not self.abortRequested():
            try:
                res = self.update(True)
                if res != -1:
                    self.notify(self._addon.getLocalizedString(30400 + res))
            except skylink.SkylinkException as e:
                self.notify(self._addon.getLocalizedString(e.id), True)

    def schedule_next(self, seconds):
        dt = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        logger.log.info('Next update %s' % dt)
        self._next_update = dt

    def update(self, try_reconnect=False):
        result = -1

        _playlist_generate = 'true' == self._addon.getSetting('playlist_generate')
        _epg_generate = 'true' == self._addon.getSetting('epg_generate')
        if not _playlist_generate and not _epg_generate:
            return result

        _username = self._addon.getSetting('username')
        _password = self._addon.getSetting('password')
        _profile = xbmc.translatePath(self._addon.getAddonInfo('profile'))
        _provider = 'skylink.sk' if int(self._addon.getSetting('provider')) == 0 else 'skylink.cz'
        _pin_protected_content = 'false' != self._addon.getSetting('pin_protected_content')
        sl = skylink.Skylink(_username, _password, _profile, _provider, _pin_protected_content)
        logger.log.info('SL created')

        try:
            channels = sl.channels()
        except skylink.TooManyDevicesException as e:
            if self._addon.getSetting('reuse_last_device') == 'true':
                device = utils.get_last_used_device(e.devices)
            else:
                device = utils.select_device(e.devices) if try_reconnect else ''

            if device != '':
                logger.log.info('reconnecting as: ' + device)
                sl.reconnect(device)
                channels = sl.channels()
            else:
                raise

        if _playlist_generate:
            try:
                path = os.path.join(self._addon.getSetting('playlist_folder'), self._addon.getSetting('playlist_file'))
                _skylink_logos = 'true' == self._addon.getSetting('sl_logos')
                logger.log.info('Updating playlist [%d channels]' % len(channels))
                exports.create_m3u(channels, path, sl._api_url if _skylink_logos else None)
                result = 1
            except IOError as e:
                logger.log.error(str(e))
                raise skylink.SkylinkException(30503)

        if _epg_generate:
            try:
                days = int(self._addon.getSetting('epg_days'))
                path = os.path.join(self._addon.getSetting('epp_folder'), self._addon.getSetting('epg_file'))
                logger.log.info('Updating EPG [%d days from %s]' % (days, datetime.datetime.now()))
                today = datetime.datetime.now()
                exports.create_epg(channels, sl.epg(channels, today, today + datetime.timedelta(days=days)), path)
                result = 2
            except IOError as e:
                logger.log.error(str(e))
                raise skylink.SkylinkException(30504)

        return result

    def tick(self):
        if datetime.datetime.now() > self._next_update:
            try:
                self.schedule_next(12 * 60 * 60)
                self.update()
            except skylink.UserNotDefinedException:
                pass
            except requests.exceptions.ConnectionError:
                self.schedule_next(60)
                logger.log.info('Can''t update, no internet connection')
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
