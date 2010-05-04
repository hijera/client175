# Copyright (C) 2008-2009 Adam Olsen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
#
# The developers of the Exaile media player hereby grant permission
# for non-GPL compatible GStreamer and Exaile plugins to be used and
# distributed together with GStreamer and Exaile. This permission is
# above and beyond the permissions granted by the GPL license by which
# Exaile is covered. If you modify this code, you may extend this
# exception to your version of the code, but you are not obligated to
# do so. If you do not wish to do so, delete this exception statement
# from your version.

# Modified by Chris Seickel to add Album Artist tag and change Performer tag
# to match MPD's implementaion.


from metadata._base import BaseFormat
from mutagen import id3


class ID3Format(BaseFormat):
    MutagenType = id3.ID3
    tag_mapping = {
        "originalalbum": "TOAL",
        "lyricist": "TEXT",
        "part": "TSST",
        "website": "WOAR",
        "cover": "APIC",
        "originalartist": "TOPE",
        "author": "TOLY",
        "originaldate": "TDOR",
        "date": "TDRC",
        "arranger": "TPE4",
        "conductor": "TPE3",
        "performer": "TOPE",
        "artist": "TPE1",
        "albumartist": "TPE2",
        "album": "TALB",
        "copyright": "TCOP",
        "lyrics": "USLT",
        "tracknumber": "TRCK",
        "track": "TRCK",
        "version": "TIT3",
        "title": "TIT2",
        "isrc": "TSRC",
        "genre": "TCON",
        "composer": "TCOM",
        "encodedby": "TENC",
        "organization": "TPUB",
        "discnumber": "TPOS",
        "disc": "TPOS",
        "bpm": "TBPM",
        }
    writable = True
    others = False # make this true once custom tag support actually works

    def _get_tag(self, raw, t):
        if not raw.tags: return []
        if t not in self.tag_mapping.itervalues():
            t = "TXXX:" + t
        field = raw.tags.getall(t)
        if len(field) <= 0:
            return []
        ret = []
        if t == 'TDRC' or t == 'TDOR': # values are ID3TimeStamps
            for value in field:
                ret.extend([unicode(x) for x in value.text])
        elif t == 'USLT': # Lyrics are stored in plain old strings
            for value in field:
                ret.append(unicode(value.text))
        elif t == 'WOAR': # URLS are stored in url not text
            for value in field:
                ret.extend([unicode(x.replace('\n','').replace('\r','')) \
                        for x in value.url])
        elif t == 'APIC':
            ret = [x.data for x in field]
        else:
            for value in field:
                try:
                    ret.extend([unicode(x.replace('\n','').replace('\r','')) \
                        for x in value.text])
                except:
                    pass
        return ret

    def _set_tag(self, raw, tag, data):
        if tag not in self.tag_mapping.itervalues():
            tag = "TXXX:" + tag
        if raw.tags is not None:
            raw.tags.delall(tag)
        frame = id3.Frames[tag](encoding=3, text=data)
        if raw.tags is not None:
            raw.tags.add(frame)

    def _del_tag(self, raw, tag):
        if tag not in self.tag_mapping.itervalues():
            tag = "TXXX:" + tag
        if raw.tags is not None:
            raw.tags.delall(tag)

# vim: et sts=4 sw=4

