#!/usr/bin/env python
#
#       Client175
#
#       Copyright 2009 Chris Seickel
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


import cherrypy, json, os, pwd, urllib, urllib2, sys
from BeautifulSoup import BeautifulSoup
from time import sleep
from datetime import datetime, timedelta
import mpd_proxy2 as mpd_proxy
from mpd import MPDError
from covers import CoverSearch
import requests
import metadata
from metadata._base import NotReadable, NotWritable

cherrypy.config.update( {
    'server.thread_pool': 10,
    'server.socket_host': '0.0.0.0'
} )
LOCAL_DIR = os.path.join(os.getcwd(), os.path.dirname(__file__))
try:
    cherrypy.config.update(os.path.join(LOCAL_DIR, sys.argv[1]))
except:
    cherrypy.config.update(os.path.join(LOCAL_DIR, "site.conf"))

SERVER_ROOT = cherrypy.config.get('server_root', '/')
MUSIC_DIR = cherrypy.config.get('music_directory', '/var/lib/mpd/music/')
MUSIC_DIR = os.path.expanduser(MUSIC_DIR)
COVERS_DIR = os.path.join(LOCAL_DIR, "static", "covers")
LOCAL_COVERS = cherrypy.config.get('local_covers', None)
if LOCAL_COVERS:
    for i in range(len(LOCAL_COVERS)):
        LOCAL_COVERS[i] = os.path.expanduser(LOCAL_COVERS[i])

LYRICS_DIR = os.path.join(LOCAL_DIR, "static", "lyrics")
if not os.path.exists(LYRICS_DIR):
    os.makedirs(LYRICS_DIR)
    
HOST = "localhost"
PORT = 6600
PASSWORD = None
RUN_AS = pwd.getpwuid(os.getuid())[0]

if os.environ.has_key("MPD_HOST"):
    mpd_host = str(os.environ["MPD_HOST"])
    if "@" in mpd_host:
        mpd_host = mpd_host.split("@")
        PASSWORD = mpd_host[0]
        HOST = mpd_host[1]
    else:
        HOST = mpd_host

if os.environ.has_key("MPD_PORT"):
    PORT = int(os.environ["MPD_PORT"])

HOST = cherrypy.config.get('mpd_host', HOST)
PORT = cherrypy.config.get('mpd_port', PORT)
PASSWORD = cherrypy.config.get('mpd_password', PASSWORD)
RUN_AS = cherrypy.config.get('run_as', RUN_AS)


mpd = mpd_proxy.Mpd(HOST, PORT, PASSWORD)
mpd.include_playlist_counts = cherrypy.config.get('include_playlist_counts', True)
cs = CoverSearch(COVERS_DIR, LOCAL_COVERS)


class Root:

    os.setuid(pwd.getpwnam(RUN_AS)[2])
    static = cherrypy.tools.staticdir.handler(
                section="/static",
                dir=os.path.join(LOCAL_DIR, "static"),
            )


    def check_username_and_password(username, password):
        if username == password:
            cherrypy.session['username'] = username
            return False
        return "Bad Login"
    cherrypy.config.update({'tools.session_auth.check_username_and_password': check_username_and_password})


    def _error_page_501(status, message, traceback, version):
        return message
    cherrypy.config.update({'error_page.501': _error_page_501})


    def about(self, *args):
        """
        Convert AUTHORS.txt into a web page with links.
        """
        f = open(os.path.join(LOCAL_DIR, "AUTHORS.txt"), "r")
        txt = []
        for line in f.readlines():
            if line.startswith("Website:  http://"):
                href = line.replace("Website:  ", "")
                line = "Website:  <a target='_blank' href='%s'>%s</a>" % (href, href)
            if line.startswith("License:  "):
                href = line.replace("License:  ", "")
                if not href.startswith("static/"):
                    href = "static/" + href
                line = "License:  <a target='_blank' href='%s'>%s</a>" % (href, href)
            txt.append(line)

        f.close()
        return '<html><body>' + '<br>'.join(txt) + '</body></html>'
    about.exposed = True


    def add(self, *args, **kwargs):
        if len(kwargs) > 0:
            args = list(args) + kwargs.values()
        if len(args) == 2:
            if args[0] in ('file', 'directory'):
                d = args[1]
                if d.startswith("/"):
                    d = d[1:]
                mpd.add(d)
            elif args[0] == 'playlist':
                mpd.load(args[1])
            elif args[0] == 'search':
                mpd.searchadd('smart', args[1])
            else:
                mpd.findadd(args[0], args[1])
        else:
            d = args[0]
            if d.startswith("/"):
                d = d[1:]
            if "://" in d[3:7]:
                ext = d.split("?")[0].split(".")[-1]
                if ext in ['mp3', 'pgg', 'wav', 'flac', 'aac', 'mod', 'wma']:
                    mpd.add(d)
                else:
                    sock = urllib2.urlopen(d)
                    data = sock.read()
                    info = sock.info()
                    mime = info.gettype()
                    sock.close()
                    if mime == "audio/x-scpls" or ext == "pls":
                        mpd.load_pls(data)
                    elif mime == "audio/x-mpegurl" or ext == "m3u":
                        mpd.load_m3u(data)
                    elif mime == "application/xspf+xml" or ext == "xspf":
                        mpd.load_xspf(data)
                    else:
                        raise cherrypy.HTTPError(501, message="Unsupported URI:  "+d)
            else:
                mpd.add(d)
    add.exposed = True


    def covers(self, **kwargs):
        f = kwargs.get('file')
        path = ''
        artist = kwargs.get('artist')
        album = kwargs.get('album')
        if f:
            path = os.path.join(MUSIC_DIR, f)
            path = os.path.dirname(path)
            if not artist:
                _file = mpd.lsinfo(f)
                artist = _file.get('artist')
                album = _file.get('album')
        img_path, img_data = cs.find(path, artist, album)
        u = cherrypy.url().split('covers')[0]
        if img_path:
            url = u+'static/covers/'+img_path
        else:
            if img_data:
                return img_data
            url = u+'static/covers/album_blank.png'
        raise cherrypy.HTTPRedirect(url, 301)
    covers.exposed = True


    def default(self, *args, **kwargs):
        """
        Wrap mpd commands in a REST API and return json encoded output.
        Any URL not already defined is assumed to be an mpd command.
        Usage:
            The mpd protocol command:
                list album artist "David Bowie"

            ...is equivilant to a GET request to:
                http://localhost:8080/list/album/artist/David%20Bowie
        """

        if len(kwargs) > 0:
            args = list(args) + kwargs.values()
        try:
            if len(args) == 1:
                args = args[0]
            print args
            result = mpd.execute(args)
        except MPDError, e:
            raise cherrypy.HTTPError(501, message=str(e))
        return json.dumps(result)
    default.exposed = True


    def edit(self, id, **kwargs):
        err = """THE FILE OR DIRECTORY DOES NOT EXIST!\n
        \n
        %s\n
        \n
        Please set the music_directory option in site.conf."""

        if not os.path.exists(MUSIC_DIR):
            raise cherrypy.HTTPError(501, message=err % MUSIC_DIR)

        loc = os.path.join(MUSIC_DIR, id)
        if not os.path.exists(loc):
            raise cherrypy.HTTPError(501, message=err % loc)

        if loc.lower().endswith(".wav"):
            return "WAV editing not supported."

        tags = {}
        for tag, val in kwargs.items():
            tag = tag.lower()
            if tag == 'track':
                tags['tracknumber'] = val
            elif tag == 'disc':
                tags['discnumber'] = val
            else:
                tags[tag] = val
            print '%s[%s] = "%s"' % (id, tag, val)

        f = metadata.get_format(loc)
        f.write_tags(tags)

        updating = False
        while not updating:
            try:
                mpd.update(id)
                updating = True
            except MPDError, e:
                if str(e) == "[54@0] {update} already updating":
                    sleep(0.01)
                else:
                    raise cherrypy.HTTPError(501, message=e)

        return "OK"
    edit.exposed = True


    def home(self, **kwargs):
        dl = len(mpd.list('date'))
        gl = len(mpd.list('genre'))
        pl = len(mpd.listplaylists())
        tm = mpd_proxy.prettyDuration(mpd.state['db_playtime'])
        result = {}
        result['data'] = [
            {
                'title': 'Songs',
                'type': 'directory',
                'directory': '/',
                'ptime': mpd.state['songs'],
                'id': 'directory:'
            },
            {
                'title': 'Total Playtime',
                'type': 'time',
                'directory': '/',
                'ptime': tm,
                'id': 'time:'
            },
            {
                'title': 'Albums',
                'type': 'album',
                'ptime': mpd.state['albums'],
                'id': 'album:'
            },
            {
                'title': 'Artists',
                'type': 'artist',
                'ptime': mpd.state['artists'],
                'id': 'artist:'
            },
            {
                'title': 'Dates',
                'type': 'date',
                'ptime': dl,
                'id': 'date:'
            },
            {
                'title': 'Genres',
                'type': 'genre',
                'ptime': gl,
                'id': 'genre:'
            },
            {
                'title': 'Playlists',
                'type': 'playlist',
                'ptime': pl,
                'id': 'playlist:'
            }
        ]

        result['totalCount'] = len(result['data'])
        return json.dumps(result)
    home.exposed = True


    def index(self):
        raise cherrypy.HTTPRedirect('static/index.html', 301)
    index.exposed = True


    def filter_results(self, data, filter):
        filter = filter.lower()
        d = []
        skip = ('type', 'time', 'ptime', 'songs')
        for item in data:
            for key, val in item.items():
                if key not in skip:
                    if filter in str(val).lower():
                        d.append(item)
                        break
        return d


    def lyrics(self, title, artist, **kwargs):
        cache_path = os.path.join(LYRICS_DIR, artist)
        file_path = os.path.join(cache_path, title + ".html")
        if os.path.exists(cache_path):
            if os.path.exists(file_path):
                print "====USING CACHE==="
                with open(file_path, 'r') as f:
                    return f.read()
        else:
            os.makedirs(cache_path)
            
        url = "http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect"
        p = {"artist": artist, "song": title}
        result = "Not Found"
        retry = 0
        r = None
        requests.max_retries = 0
        while retry < 3 and r is None:
            try:
                r = requests.get(url, params=p, timeout=15)
            except Exception, err:
                print "%s: \n    Retry %s\n    %s" % (url, retry, err)
                retry += 1
                sleep(3.0)
        if r is None:
            return "Could not reach ChartLyrics.com..."
            
        if r.error:
            result = r.error
        else:
            print "====GOT RESULT==="
            xml = BeautifulSoup(r.text)
            root = xml.getlyricresult
            if root:
                lyric = root.lyric
                if lyric:
                    result = lyric.contents[0]
                    
        result = result.replace("\n", "<br/>")
        with open(file_path, 'w') as f:
            print "====SAVING CACHE==="
            f.write(result)
        print result
        return result
    lyrics.exposed = True


    def moveend(self, ids, **kwargs):
        if ids:
            ids = ids.split(".")
            mpd.command_list_ok_begin()
            end = len(mpd.playlist) - 1
            for id in ids:
                if id.isdigit():
                    mpd.moveid(id, end)
            mpd.command_list_end()
            return "OK"
    moveend.exposed = True


    def movestart(self, ids, **kwargs):
        if ids:
            ids = reversed(ids.split("."))
            mpd.command_list_ok_begin()
            for id in ids:
                if id.isdigit():
                    mpd.moveid(id, 0)
            mpd.command_list_end()
            return "OK"
    movestart.exposed = True


    def password(self, passwd=None):
        if passwd is not None:
            mpd.password(passwd)
    password.exposed = True


    def playlistinfoext(self, start=0, limit=0, filter='', **kwargs):
        start = int(start)
        limit = int(limit)
        ln = int(mpd.state['playlistlength'])

        if filter:
            data = mpd.playlistsearch('any', filter)
            mpd.setPlaylistFiles(data)
            if limit:
                ln = len(data)
                end = start + limit
                if end > ln:
                    end = ln
                if start > end:
                    data = []
                else:
                    data = data[start:end]
        else:
            if limit:
                end = start + limit
                if end > ln:
                    end = ln
                if start > end:
                    data = []
                else:
                    data = mpd.playlistinfo('%d:%d' % (start, end))
            else:
                data = mpd.playlistinfo()
            mpd.setPlaylistFiles(data)

        if data and kwargs.get('albumheaders'):
            result = []

            def makeHeader(dg):
                return {
                    'album': dg('album', 'Unknown'),
                    'artist': dg('albumartist', dg('artist', 'Unknown')),
                    'file': dg('file'),
                    'cls': 'album-group-start'
                }

            a = makeHeader(data[0].get)
            result.append(a)
            for d in data:
                g = d.get
                if a['album'] != g('album', 'Unknown'):
                    result[-1]['cls'] = 'album-group-end album-group-track'
                    a = makeHeader(g)
                    result.append(a)
                elif a['artist'] != g('albumartist', g('artist', 'Unknown')):
                    a['artist'] = 'Various Artists'

                d['cls'] = 'album-group-track'
                result.append(d)
        else:
            result = data

        if limit:
            return json.dumps({'totalCount': ln, 'data': result})
        else:
            return json.dumps(result)
    playlistinfoext.exposed = True


    def protocol(self, cmd):
        """
        Run mpd protocol command as string and return raw text results.
        """
        try:
            return mpd.raw(cmd)
        except MPDError, e:
            raise cherrypy.HTTPError(501, message=str(e))
    protocol.exposed = True


    def query(self, cmd, start=0, limit=0, sort='', dir='ASC', filter='', **kwargs):
        if not cmd:
            return self.home()

        if cmd == 'playlistinfo':
            return self.playlistinfoext(start, limit, filter, **kwargs)

        node = kwargs.get("node", False)
        if node:
            m = int(kwargs.get('mincount', 0))
            return self.tree(cmd, node, m)

        start = int(start)
        limit = int(limit)
        if sort:
            data = mpd.execute_sorted(cmd, sort, dir=='DESC')
        else:
            data = mpd.execute(cmd)

        if filter:
            data = self.filter_results(data, filter)

        if limit:
            ln = len(data)
            end = start + limit
            if end > ln:
                end = ln
            if start > end:
                d = []
            else:
                d = data[start:end]
            result = {}
            result['totalCount'] = ln
            result['data'] = d
        else:
            result = data

        if cmd.startswith('list '):
            return json.dumps(result)

        if cmd == 'listplaylists':
            return json.dumps(result)

        if limit:
            data = result['data']

        for i in range(len(data)):
            d = data[i]
            if d['type'] == 'file':
                pl = mpd.getPlaylistByFile(d['file'])
                if pl:
                    data[i] = pl

        return json.dumps(result)
    query.exposed = True


    def status(self, **kwargs):
        client_uptime = kwargs.get('uptime')
        client_updating_db = kwargs.get('updating_db', '')
        if not client_uptime:
            s = mpd.sync()
            return json.dumps(s)
        n = 0
        while n < 50:
            if mpd.state.get('uptime', '') <> client_uptime:
                return json.dumps(mpd.state)
            if mpd.state.get('updating_db', '') <> client_updating_db:
                return json.dumps(mpd.state)
            sleep(0.1)
            n += 1
        return 'NO CHANGE'
    status.exposed = True


    def tree(self, cmd, node, mincount=0, **kwargs):
        if node == 'directory:':
            result = []
            rawdata = mpd.listall()
            data = []
            for d in rawdata:
                directory = d.get("directory")
                if directory:
                    parts = directory.split("/")
                    data.append({
                        'title': parts.pop(),
                        'parent': '/'.join(parts),
                        'directory': directory,
                        'type': 'directory',
                        'leaf': True
                    })

            def loadChildren(parent, parentpath):
                children = [x for x in data if x['parent'] == parentpath]
                if children:
                    parent['leaf'] = False
                    parent['children'] = []
                    for c in children:
                        parent['children'].append(c)
                        loadChildren(c, c['directory'])

            root = {}
            loadChildren(root, '')
            result = root['children']
        elif node == 'outputs:':
            result = []
            rawdata = mpd.outputs()
            for item in rawdata:
                if item['outputenabled'] == '1':
                    cls = 'icon-output-on'
                else:
                    cls = 'icon-output-off'
                result.append({
                    'text': item['outputname'],
                    'id': item['outputid'],
                    'type': 'output',
                    'iconCls': cls,
                    'leaf': True
                })
        else:
            itemType = node.split(":")[0]
            data = [x for x in mpd.execute_sorted(cmd, 'title') if x.get('title')]
            if mincount:
                mincount -= 1
                data = [x for x in data if x['songs'] > mincount]

            if itemType == 'directory':
                result = [x for x in data if x['type'] == itemType]
            elif len(data) > 200:
                result = []
                iconCls = 'icon-group-unknown icon-group-'+itemType
                cls = 'group-by-letter'
                letters = sorted(set([x['title'][0].upper() for x in data]))
                special = {
                    'text': "'(.0-9?",
                    'iconCls': iconCls,
                    'cls': cls,
                    'children': [x for x in data if x['title'][0] < 'A']
                }
                result.append(special)
                for char in letters:
                    if char >= 'A' and char < 'Z':
                        container = {
                            'text': char,
                            'iconCls': iconCls,
                            'cls': cls,
                            'children': [x for x in data if x['title'][0].upper() == char]
                        }
                        result.append(container)
                container = {
                    'text': 'Z+',
                    'iconCls': iconCls,
                    'cls': cls,
                    'children': [x for x in data if x['title'][0].upper() > 'Y']
                }
                result.append(container)
            else:
                result = data
        return json.dumps(result)
    tree.exposed = True


root = Root()

# Uncomment the following to use your own favicon instead of CP's default.
#favicon_path = os.path.join(LOCAL_DIR, "favicon.ico")
#root.favicon_ico = tools.staticfile.handler(filename=favicon_path)

cherrypy.tree.mount(root, SERVER_ROOT)

def cleanup():
    print "     CLEANUP CALLED"
    mpd.kill()
    

def serverless():
    """Start with no server (for mod_python or other WSGI HTTP servers).

    You can also use this mode interactively:
        >>> import cpdeploy
        >>> cpdeploy.serverless()
    """
    cherrypy.server.unsubscribe()
    cherrypy.config.update({
        'log.error_file': os.path.join(os.path.dirname(__file__), 'site.log'),
        'environment': 'production',
        })


def serve():
    """Start with the builtin server."""
    cherrypy.config.update({'log.screen': True})
    if hasattr(cherrypy.engine, 'signal_handler'):
        cherrypy.engine.signal_handler.subscribe()
        cherrypy.engine.subscribe("stop", cleanup)
    cherrypy.engine.start()



if __name__ == "__main__":
    shost = cherrypy.config.get('server.socket_host')
    sport = cherrypy.config.get('server.socket_port')
    if shost == '0.0.0.0':
        shost = 'localhost'
    if sport is None:
        sport = "8080"

    print ""
    print "=" * 60
    print "Server Ready."
    print "Client175 is available at:  http://%s:%s/%s" % (shost, sport, SERVER_ROOT)
    print "=" * 60
    print ""

    serve()
