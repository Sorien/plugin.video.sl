import datetime
import os
import time
import requests
import exports
import logger
import skylink
import account
import xbmc
import xbmcaddon
import xbmcgui
import sys

reload(sys)
sys.setdefaultencoding('utf8')

class SkylinkMonitor(xbmc.Monitor):
    _addon = xbmcaddon.Addon()
    _next_update = 0
    _accounts = []

    def __init__(self):
        xbmc.Monitor.__init__(self)
        ts = self._addon.getSetting('next_update')
        self._next_update = datetime.datetime.now() if ts == '' else datetime.datetime.fromtimestamp(float(ts))
        self.update_accounts()

    def update_accounts(self):
        logger.log.info('Updating accounts...')

        account_sk = account.Account('sk', self._addon.getSetting('username_sk'), self._addon.getSetting('password_sk'), 'skylink.sk')
        account_cz = account.Account('cz', self._addon.getSetting('username_cz'), self._addon.getSetting('password_cz'), 'skylink.cz')

        self._accounts.append(account_sk)
        self._accounts.append(account_cz)

    def make_unique_list(self, channels):
        logger.log.info('Filtering channels to create unique list...')

        names_list = []
        channels_list = []
        for channel in channels:
            if not channel['stationid'] in names_list:
                names_list.append(channel['stationid'])
                channels_list.append(channel)

        return channels_list

    def notify(self, text, error=False):
        icon = u'DefaultIconError.png' if error else ''
        xbmc.executebuiltin(u'Notification("%s","%s",5000, %s)' % (self._addon.getAddonInfo('name'), text, icon))

    def select_device(self, d):
        dialog = xbmcgui.Dialog()
        items = []
        for device in d:
            items.append(device['name'].replace("+", " "))
        return dialog.select(self._addon.getLocalizedString(30403), items)

    def onSettingsChanged(self):
        self.update_accounts()

        if not self.abortRequested():
            try:
                res = self.update(True)
                self.notify(self._addon.getLocalizedString(30400 + res))
            except skylink.SkylinkException as e:
                self.notify(self._addon.getLocalizedString(e.id), True)

    def shedule_next(self, seconds):
        dt = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        logger.log.info('Next update %s' % dt)
        self._next_update = dt

    def update(self, try_reconnect=False):
        channels = []

        for account in self._accounts:
            if not account.is_valid():
                continue

            sl = skylink.Skylink(account, xbmc.translatePath(self._addon.getAddonInfo('profile')).decode("utf-8"))

            logger.log.info('Getting channels for account: %s' % (account.username))

            try:
                channels = channels + sl.channels()
            except skylink.TooManyDevicesException as e:
                if try_reconnect:
                    d = self.select_device(e.devices)
                    if d > -1:
                        logger.log.info('reconnecting as: ' + e.devices[d]['id'])
                        sl.reconnect(e.devices[d]['id'])
                        channels = channels + sl.channels()
                    else:
                        raise
                else:
                    raise

        if bool(self._addon.getSetting('playlist_unique')):
            channels = self.make_unique_list(channels)

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
                exports.create_epg(channels, sl.epg(channels, datetime.datetime.now(), days), path, self._addon)
                result = 2
            except IOError as e:
                logger.log.error(str(e))
                raise skylink.SkylinkException(30504)

        return result

    def tick(self):
        if datetime.datetime.now() > self._next_update:
            try:
                self.shedule_next(12 * 60 * 60)
                self.update()
            except skylink.UserNotDefinedException:
                pass
            except requests.exceptions.ConnectionError:
                self.shedule_next(60)
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
