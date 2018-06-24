import datetime
import io

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}

LOGOS_DIR = 'special://home/addons/plugin.video.sl/resources/logos'


def html_escape(text):
    return "".join(html_escape_table.get(c, c) for c in text)


def create_m3u(channels, path):
    with io.open(path, 'w', encoding='utf8') as file:
        file.write(u'#EXTM3U\n')

        for c in channels:
            file.write(u'#EXTINF:-1 tvg-id="%s" tvg-logotvg-logo="%s/%s.png",%s\n' % (
            c['stationid'], LOGOS_DIR, c['stationid'], c['title']))
            file.write(u'plugin://plugin.video.sl/?action=play&id=%s\n' % c['id'])


def create_epg(channels, epg, path, addon=None):
    with io.open(path, 'w', encoding='utf8') as file:
        file.write(u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        file.write(u'<tv>\n')

        for c in channels:
            file.write(u'<channel id="%d">\n' % c['stationid'])
            file.write(u'<display-name>%s</display-name>\n' % c['title'])
            #        file.write('<url>http://www.hrt.hr</url>\n')
            #        file.write('<icon src="http://phazer.info/img/kanali/hrt1.png" />\n')
            file.write(u'</channel>\n')

        for e in epg:
            for c in e:
                for p in e[str(c)]:
                    # delta = datetime.datetime.fromtimestamp(p['start']) - datetime.datetime.utcfromtimestamp(p['start'])
                    b = datetime.datetime.fromtimestamp(p['start']) - datetime.timedelta(hours=1)
                    e = b + datetime.timedelta(minutes=p['duration'])
                    file.write(u'<programme channel="%s" start="%s" stop="%s">\n' % (
                    c, b.strftime('%Y%m%d%H%M%S'), e.strftime('%Y%m%d%H%M%S')))
                    if 'title' in p:
                        file.write(u'<title>%s</title>\n' % html_escape(p['title']))
                    if 'description' in p:
                        file.write(u'<desc>%s</desc>\n' % html_escape(p['description']))
                    if 'cover' in p:
                        file.write(u'<icon src="https://livetv.skylink.sk/%s" />\n' % html_escape(p['cover']))
                    if (addon is not None) and ('genre' in p) and (10000 <= p['genre'][0] <= 11000):
                        file.write('<category>%s</category>\n' % addon.getLocalizedString(p['genre'][0] + 20900))
                    file.write(u'</programme>\n')

        file.write(u'</tv>\n')
