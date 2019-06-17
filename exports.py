import datetime
import io

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}


def html_escape(text):
    return "".join(html_escape_table.get(c, c) for c in text)


def logo_id(title):
    for ch in [' ', '/', '(18+)', ':']:
        title = title.replace(ch, '')
    return title.replace('+', 'plus').lower() + '.png'


def logo_sl_location(title):
    replacements = {':': '', '/': '', '+': '', ' ': '%20'}
    for ch in replacements.keys():
        title = title.replace(ch, replacements[ch])
    return 'mmchan/channelicons/' + title + '_w267.png'


def create_m3u(channels, path, url):
    with io.open(path, 'w', encoding='utf8') as file:
        file.write(u'#EXTM3U\n')

        for c in channels:
            file.write(u'#EXTINF:-1 tvg-id="%s" tvg-logo="%s",%s\n' % (
                c['stationid'],
                url + logo_sl_location(c['title']) if url is not None else logo_id(c['title']),
                c['title']))
            file.write(u'plugin://plugin.video.sl/?action=play&id=%s&askpin=%s\n' % (c['id'], c['pin']))


def create_epg(channels, epg, path):
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
                    b = datetime.datetime.utcfromtimestamp(p['start'])
                    e = b + datetime.timedelta(minutes=p['duration'])
                    file.write(u'<programme channel="%s" start="%s" stop="%s">\n' % (
                        c, b.strftime('%Y%m%d%H%M%S'), e.strftime('%Y%m%d%H%M%S')))
                    if 'title' in p:
                        file.write(u'<title>%s</title>\n' % html_escape(p['title']))
                    if 'description' in p and p['description'] != '':
                        file.write(u'<desc>%s</desc>\n' % html_escape(p['description']))
                    if 'cover' in p:
                        file.write(u'<icon src="%s"/>\n' % html_escape(p['cover']))
                    if 'genres' in p and len(p['genres']) > 0:
                        file.write('<category>%s</category>\n' % ', '.join(p['genres']))
                    file.write(u'</programme>\n')

        file.write(u'</tv>\n')
