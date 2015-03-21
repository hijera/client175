## 0.5a Released December 17, 2010 ##

  * Added control over mpd outputs
  * Added support for adding URLs to playlist (files, pls, m3u, and xspf)
  * Fixed Filter in tab browser


## 0.4 Released November 20, 2010 ##

  * Switched to LyricsWiki lookup
  * Fixed bug with mpd passwords
  * Added 'run\_as' option
  * Fixed bug with adding to playlist from a paged list


## 0.3 Released July 16, 2010 ##

  * Requires MPD version 15+
  * Playlist loading vastly improved, large playlists are no longer an issue.
  * Added 'include\_playlist\_counts' option to site.conf, to disable counting length and playtime when listing stored playlists
  * Improved search feature to return artists and albums first, then songs with the search term in title tag, instead of just a big list of songs with matches in any tag
  * Lots of code cleanup and bug fixes on the server


## 0.2a Released July 2, 2010 ##

  * Significant performance improvements to loading large data sets, particularly the playlist
  * Playlist sidebar now supports paging, to prevent over loading the browser with huge playlists
  * Added options to site.conf for setting MPD's host and port
  * Window title is now set to current song's title and artist
  * Loading/Replacing playlist will restart playback if it was playing at the time
  * Added ability to run mpd protocol commands directly via the search and filter boxes.  Any search that starts with "mpd " will be interpreted as an mpd command.


## 0.1 Released June 26, 2010 ##

  * Initial Release