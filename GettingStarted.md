## Introduction ##
This is intended to be run on the same server as mpd and will default to connecting to localhost:6600.  It will, however, use the MPD\_HOST and MPD\_PORT environment variables if they exist.  Tag editing will only work if the files are accessible and writable by the user running the server and the music\_directory option is set correctly in site.conf.

**Note:**  If you are interested in running the site via an existing Apache install, see the BehindApache page instead.


---


## Requirements ##
A running MPD daemon (at least version 15.0) and python 2.6 are all that you need.


---


## Installation and Setup ##

### Install from SVN (recomended) ###

  * Checkout the source from svn:  `svn checkout http://client175.googlecode.com/svn/trunk/ client175`
  * CD into the new directory:  `cd client175`
  * Edit the music\_directory option in **site.conf** to point to your music directory, this is required to edit tags.
  * Start the server:  `python server.py`
  * Open a web browser to http://localhost:8080/static/index.html

### Install Packaged Release ###
  * Download and extract the latest package from the Downloads section.
  * Edit site.conf
  * Open a terminal, cd into the directory you extracted to, and run the server:  `python server.py`
  * Open a web browser to http://localhost:8080/static/index.html


---


## Run on Startup ##
### Upstart conf file ###

Here is an example provided by chrissavery for starting the server when mpd starts on systems using Upstart (such as ubuntu.)  You should use the run\_as option in site.conf to drop down to a restricted user (also provided by chrissavery.)

To use this method, mpd will also need to be started with Upstart.  Here is an example upstart conf file for mpd.

mpd.conf:
```
# init file for mpd (music player daemon)

start on (runlevel [2345] and started networking)
stop on runlevel [016]

pre-start script

MPDCONF=/etc/mpd.conf
DBFILE=$(sed -n 's/^[[:space:]]*db_file[[:space:]]*"\?\([^"]*\)\"\?/\1/p' $MPDCONF)
PIDFILE=$(sed -n 's/^[[:space:]]*pid_file[[:space:]]*"\?\([^"]*\)\"\?/\1/p' $MPDCONF)
USER=`awk 'BEGIN{ao=0} /[ \t]*audio_output[ \t]*{/{ ao = 1 } /[ \t]*}/{ ao = 0 } /^[ \t]*user[ \t]*/{ if (ao == 0) user = $2 } END{ print substr(user, 2, length(user) - 2) }' $MPDCONF`
PIDDIR=$(dirname "$PIDFILE")

if [ ! -d "$PIDDIR" ]; then
    mkdir -m 0755 $PIDDIR
    chown $USER:audio $PIDDIR
fi

end script

expect fork
respawn
exec /usr/bin/mpd $MPDCONF
```


client175.conf:
```
# init file for client175 

start on started mpd
stop on stopping mpd

exec /usr/bin/python /opt/client175/server.py
```