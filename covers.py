#!/usr/bin/env python
#
#       covers.py
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
#
#       The design of this module was inspired by the cover search found in
#       Exaile (http://www.exaile.org/).


import hashlib, re, urllib, os, time, shutil, threading
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta

class CoverSearch():
    """
        Searches for covers from amazon.com (via musicbrainz.org),
        then Last.fm.  If neither return a valid album image, an
        artist image from last.fm will be used.
    """

    def __init__(self, cover_dir=None, local_covers=[]):
        self.local_covers = local_covers
        if cover_dir is not None:
            self.cover_dir = cover_dir
        else:
            self.cover_dir = os.path.expanduser(os.path.join('~','.Covers'))

        if not os.path.exists(self.cover_dir):
            os.makedirs(self.cover_dir)

        self.urlMB = 'http://musicbrainz.org/ws/1/release/?type=xml&title=%(album)s&artist=%(artist)s&limit=1'
        self.regexMB = re.compile('\<asin\>([^\<]*)\<\/asin\>', re.IGNORECASE)

        self.urlFM = "http://ws.audioscrobbler.com/1.0/album/%(artist)s/%(album)s/info.xml"

        self.urlFM_artist = "http://ws.audioscrobbler.com/1.0/artist/%s/similar.xml"
        self.regexFM_artist = re.compile('picture\=\"([^\"]*)\"', re.IGNORECASE)

        self.lock = threading.RLock()
        self.delta = timedelta(seconds=1)


    def _delay(self, timeVar):
        # Be kind, don't make more than one request per second to
        # each service.
        lastSearch = self.__dict__.get(timeVar, None)
        if lastSearch:
            n = datetime.utcnow()
            dif = n - lastSearch
            while dif < self.delta:
                time.sleep(0.1)
                n = datetime.utcnow()
                dif = n - self.__dict__[timeVar]
        try:
            self.lock.acquire()
            self.__dict__[timeVar] = datetime.utcnow()
        finally:
            self.lock.release()


    def _findMusicBrainz(self, vars):
        self._delay('last_MB_lookup')
        data = urllib.urlopen(self.urlMB % vars).read()
        m = self.regexMB.search(data)
        if not m:
            return False
        else:
            asin = m.group(1)
            url = "http://images.amazon.com/images/P/%s.01.%sZZZZZZZ.jpg"
            for sz in ['L', 'M']:
                image = url % (asin, sz)
                h = urllib.urlopen(image)
                data = h.read()
                h.close()
                if len(data) > 1000:
                    return data
        return False


    def _findLastFM_album(self, vars):
        self._delay('last_FM_lookup')
        data = urllib.urlopen(self.urlFM % vars).read()
        x = ET.XML(data)
        if len(x) == 0:
            print 'LASTFM SEARCH: ERROR PARSING LASTFM DATA!'
            return False

        c = x.find('coverart')
        if len(c) == 0:
            print 'LASTFM SEARCH: NO COVERART NODE IN LASTFM DATA!'
            return False

        for sz in ['large', 'medium', 'small']:
            image = c.findtext(sz, '')
            if image > '' and not image.lower().endswith('.gif'):
                h = urllib.urlopen(image)
                data = h.read()
                h.close()
                if hashlib.sha1(data).hexdigest() != "57b2c37343f711c94e83a37bd91bc4d18d2ed9d5":
                    return data

        return False


    def _findLastFM_artist(self, vars):
        self._delay('last_FM_lookup')
        data = urllib.urlopen(self.urlFM_artist % vars['artist']).read()
        m = self.regexFM_artist.search(data)
        if m:
            image = m.group(1)
            if image.lower().endswith('.gif'):
                return False
            h = urllib.urlopen(image)
            data = h.read()
            h.close()
            if hashlib.sha1(data).hexdigest() != "57b2c37343f711c94e83a37bd91bc4d18d2ed9d5":
                return data
        return False


    def find(self, path='', artist='', album=''):
        for p in self.local_covers:
            coverpath = p.replace("{folder}", path)
            coverpath = coverpath.replace("{artist}", artist)
            coverpath = coverpath.replace("{album}", album)
            if os.path.exists(coverpath):
                ext = coverpath.split(".")[-1]
                covername = '%s - %s.%s'  % (artist, album, ext)
                cover_destination = os.path.join(self.cover_dir, covername)
                if not os.path.exists(cover_destination):
                    try:
                        shutil.copy2(coverpath, cover_destination)
                    except IOError:
                        print "Could not save cover to: " + cover_destination
                        print "For best performance, please ensure that the directory exists and is writable."
                        h = open(coverpath, 'r')
                        data = h.read()
                        h.close()
                        return "", data
                return covername, None

        if not artist:
            return False, None

        if album:
            covername = '%s - %s.jpg' % (artist, album)
            lookups = [
                self._findMusicBrainz,
                self._findLastFM_album,
                self._findLastFM_artist
            ]
        else:
            album = ''
            covername = '%s.jpg' % artist
            lookups = [self._findLastFM_artist]

        coverpath = os.path.join(self.cover_dir, covername)
        if os.path.isfile(coverpath):
            return covername, None

        vars = {
            'album': urllib.quote_plus(album.encode("utf-8")),
            'artist': urllib.quote_plus(artist.encode("utf-8"))
        }

        for fn in lookups:
            try:
                data = fn(vars)
                if data:
                    try:
                        h = open(coverpath, 'w')
                        h.write(data)
                        h.close()
                    except:
                        print "Could not save cover to: " + coverpath
                        print "For best performance, please ensure that the directory exists and is writable."
                        covername = ""
                    return covername, data
            except:
                pass

        return False, None

