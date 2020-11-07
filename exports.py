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


def create_m3u(channels, path, logo_url=None):
    with io.open(path, 'w', encoding='utf8') as file:
        file.write(u'#EXTM3U\n')

        for c in channels:
            catchup_url = u'plugin://plugin.video.sl/?stationid=%s&askpin=%s&catchup_id={catchup-id}' % (c['stationid'], c['pin'])
            catchup = u'catchup-days="7" catchup-source="'+catchup_url+'"' if c['replayable'] else ''
            file.write(u'#EXTINF:-1 tvg-id="%s" tvg-logo="%s" %s,%s\n' % (
                c['stationid'],
                logo_url + logo_sl_location(c['title']) if logo_url is not None else logo_id(c['title']),
                catchup,
                c['title']))
            file.write(u'plugin://plugin.video.sl/?id=%s&askpin=%s\n' % (c['id'], c['pin']))


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

        year = datetime.datetime.now().year
        for e in epg:
            for c in e:
                for p in e[str(c)]:
                    b = datetime.datetime.utcfromtimestamp(p['start'])
                    e = b + datetime.timedelta(minutes=p['duration'])
                    file.write(u'<programme channel="%s" start="%s" stop="%s" catchup-id="%s">\n' % (
                        c, b.strftime('%Y%m%d%H%M%S'), e.strftime('%Y%m%d%H%M%S'), p['locId']))
                    if 'title' in p:
                        file.write(u'<title>%s</title>\n' % html_escape(p['title']))
                    if 'description' in p and p['description'] != '':
                        file.write(u'<desc>%s</desc>\n' % html_escape(p['description']))
                    if 'cover' in p:
                        file.write(u'<icon src="%s"/>\n' % html_escape(p['cover']))
                    if 'genres' in p and len(p['genres']) > 0:
                        file.write('<category>%s</category>\n' % html_escape(', '.join(p['genres'])))
                    if 'credits' in p and len(p['credits']) > 0:
                        file.write(u'<credits>\n')
                        for cr in p['credits']:
                            if 'p' in cr:
                                if ('r' not in cr) or (cr['r'] == 4):
                                    file.write(u'<actor>%s</actor>\n' % html_escape(cr['p'].strip()))
                                elif cr['r'] == 1:
                                    file.write(u'<director>%s</director>\n' % html_escape(cr['p'].strip()))
                                elif cr['r'] == 2:
                                    file.write(u'<writer>%s</writer>\n' % html_escape(cr['p'].strip()))
                                elif cr['r'] == 3:
                                    file.write(u'<producer>%s</producer>\n' % html_escape(cr['p'].strip()))
                        file.write(u'</credits>\n')
                    if 'seasonNo' in p and p['seasonNo'] > 0 and 'episodeNo' in p and p['episodeNo'] > 0:
                        if p['seasonNo'] != year and p['seasonNo'] != year + 1:
                            file.write(u'<episode-num system="xmltv_ns">%d.%d.</episode-num>\n' %
                                       (p['seasonNo'] - 1, p['episodeNo'] - 1))
                    file.write(u'</programme>\n')

        file.write(u'</tv>\n')
