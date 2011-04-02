Ext.Ajax.disableCaching = false
Ext.namespace('mpd')
Ext.namespace('console')
console.log = console.log || Ext.emptyFn

mpd.events = new Ext.util.Observable()
Ext.apply(mpd.events, {
    _suspendedEvents: [],
    resume: function (eventName) {
        var i = this._suspendedEvents.indexOf(eventName)
        if (i >= 0) {
            this._suspendedEvents.splice(i, 1)
        }
    },
    suspend: function (eventName) {
        if (this._suspendedEvents.indexOf(eventName) == -1) {
            this._suspendedEvents.push(eventName)
        }
    },
    fireEvent: function() {
        var eventName = arguments[0]
        if (this._suspendedEvents.indexOf(eventName) == -1) {
            Ext.util.Observable.prototype.fireEvent.apply(this, arguments)
        }
    }
})

mpd.events.addEvents("repeat", "playlists", "consume", "random", "uptime",
    "elapsed", "volume", "single", "db_update", "updating_db", "artists", "playtime",
    "albums", "db_playtime", "playlistlength", "playlist", "xfade", "state",
    "playlistname", "song", "songs")


mpd.timer_delay = 100
mpd.status = {'state': 'stop'}
mpd._updateValue = function(key, val) {
    if (val != Ext.value(mpd.status[key], null)) {
        mpd.status[key] = val
        mpd.events.fireEvent.defer(10, mpd.events, [key, val])
    }
}

mpd._updateElapsed = function () {
    /**
     * Update the elapsed time.  Working off of the clients clock and
     * calculating the time since the last known value prevents drift
     * from javascript polling, which is not precise enough.
     **/
    var now = new Date()
    var diff = Math.round( now.getElapsed(this.startDate)/1000 )
    var e = this.startElapsed + diff
    mpd._updateValue('elapsed', e)
}

mpd._elapsedRunner = new Ext.util.TaskRunner()


mpd.checkStatus = new Ext.util.DelayedTask(function() {
    Ext.Ajax.request({
        url: '../status',
        params: {
            'uptime': mpd.status.uptime,
            'updating_db': mpd.status.updating_db
        },
        success: function (req, opt) {
            try {
                var txt = req.responseText
                if (txt != 'NO CHANGE') {
                    mpd._elapsedRunner.stopAll()
                    var obj = Ext.util.JSON.decode(txt)
                    Ext.iterate(obj, mpd._updateValue)
                    /**
                     * Rather than constantly polling for elapsed time changes,
                     * just update the elapsed time internally.  It has
                     * a smoother appearance that way and is actually
                     * more accurate on average.
                     **/
                    if (mpd.status.state == 'play') {
                        var task = {
                            startDate: new Date(),
                            startElapsed: parseInt(mpd.status.elapsed),
                            run: mpd._updateElapsed,
                            interval: 1000
                        }
                        mpd._elapsedRunner.start(task)
                    }
                }
                mpd.checkStatus.delay(100)
            } catch (e) {
                console.log(e)
                mpd.checkStatus.delay(3000)
            }
        },
        failure: function (req, opt) {
            mpd.checkStatus.delay(3000)
        }
    })
})



mpd.cmd = function (aCmd, callBack) {
    var url = ".."
    if (Ext.isArray(aCmd)) {
        Ext.each(aCmd, function(item) {
            url += "/" + encodeURIComponent(item)
        })
        Ext.Ajax.request({
            url: url,
            success: function(response, opts) {
                if (Ext.isFunction(callBack)) {
                    d = Ext.util.JSON.decode(response.responseText)
                    callBack(d, aCmd)
                }
            },
            failure: function (req, opt) {
                var m = "The following error was encontered when sending the command:&nbsp;&nbsp;<b>" +
                    aCmd.join(" ") + "</b><br/><br/>"
                var t = req.responseText || req.responseStatus
                Ext.Msg.alert("MPD Error", m + t)
            }
        })
    } else {
        Ext.Ajax.request({
            url: "../protocol/" + encodeURIComponent(aCmd),
            success: function(response, opts) {
                if (Ext.isFunction(callBack)) {
                    callBack(response.responseText, aCmd)
                }
            },
            failure: function (req, opt) {
                var m = "The following error was encontered when sending the command:&nbsp;&nbsp;<b>" +
                    aCmd.join(" ") + "</b><br/><br/>"
                var t = req.responseText || req.responseStatus
                Ext.Msg.alert("MPD Error", m + t)
            }
        })
    }
}

mpd.setvol_tmr = null
function setvol(v) {
    mpd.setvol_tmr=null
    mpd.cmd(['setvol', v])
    mpd.events.resume('volume')
}
mpd.setvol = function(v) {
    if (mpd.setvol_tmr) clearTimeout(mpd.setvol_tmr)
    mpd.events.suspend('volume')
    mpd.setvol_tmr = setvol.defer(100, null, [v])
}


mpd.seek_tmr = null
function seek(v) {
    mpd.seek_tmr=null
    mpd.cmd(['seek', mpd.status.song, v])
    mpd.events.resume('elapsed')
}
mpd.seek = function(v) {
    if (mpd.seek_tmr) clearTimeout(mpd.seek_tmr)
    mpd.events.suspend('elapsed')
    mpd.seek_tmr = seek.defer(100, null, [v])
}


function hmsFromSec(sec) {
    var hms = "0:00"
    try {
        sec = parseInt(sec)
    } catch (err) {
        return "0:00"
    }
    if (sec > 0) {
        var h = 0
        if (sec >= 3600) {
            h = Math.floor(sec / 3600)
            sec = sec % 3600
        }
        var m = Math.floor(sec / 60)
        var s = sec % 60
        if (h > 0) {
            h = h + ":"
            if (m.toString().length == 1) {
                m = "0" + m
            }
        } else {
            h = ""
        }
        m = m + ":"
        if (s.toString().length == 1) {
            s = "0" + s
        }
        hms = h + m + s
    } else {
        return "0:00"
    }
    return hms
}
