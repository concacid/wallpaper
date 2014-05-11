#!/bin/bash

PID=$(pgrep gnome-session)
export DBUS_SESSION_BUS_ADDRESS=$(grep -z DBUS_SESSION_BUS_ADDRESS /proc/$PID/environ|cut -d= -f2-)

# Comment this BLOCK out if you don't use virtualenvwrapper
if [ -z "$WORKON_HOME" ]; then
	export WORKON_HOME=$HOME/.virtenvs

	. /usr/local/bin/virtualenvwrapper.sh
fi
# end BLOCK

python `pwd`/wallpaper.py
