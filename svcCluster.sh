#!/bin/sh

### BEGIN INIT INFO
# Provides:          DST
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start DST Service at boot time.
# Description:       Starts the DST "Start up" script also used by the python web portal for restarts.
### END INIT INFO

# This file goes in /etc/init.d
# to automate this script on startup:sudo update-rc.d <thisfilename> defaults


# dont forget to get a new cluster token for new instances - http://dst-dedicated.mathielo.com/docs/ClusterToken.html
# dont forget to set the ports to different ports in the master and Caves settings.ini files!

#adapted from/modified this forum post:
#https://dontstarve.fandom.com/wiki/Guides/Automatically_Start_Dedicated_Server_(Linux)



NAME="Dont Starve together"
#The user that you installed DST server as
USER="steam"
SCREENREF="DST"
#should be the same as the dedicated server's install directory
BINARYPATH="/home/steam/DST/"
#BINARYNAME="dontstarve_dedicated_server_nullrenderer"
BINARYNAME="startCluster.sh" #change me 1 of 4 for additional instances (points to your start file)
PIDFILE="dstCluster.pid" #change me 2 of 4 for additional instances
DAEMON="/home/steam/DST/startCluster.sh" #change me 3 of 4 for additional instances
DAEMON_OPTS="--baz=quux"
STOP_SIGNAL=INT

cd "$BINARYPATH"


CLUSTER_NAME="Cluster" #change me 4 of 4 for additional instances
MASTER_NAME="Master"
CAVE_NAME="Caves"

command_m(){
    su - steam -c "screen -S ${CLUSTER_NAME}_${MASTER_NAME} -p 0 -X stuff \"$1^M\""
}

command_c(){
    su - steam -c "screen -S ${CLUSTER_NAME}_${CAVE_NAME} -p 0 -X stuff \"$1^M\""
}

stop_server(){
    command_m 'c_announce("Server stopped by force! Shutting down!")'
    echo "running shutdown commands"
    sleep "2s"
    command_c 'c_shutdown()'
    command_m 'c_shutdown()'

    # The server gets a couple seconds to shutdown before checking.
    sleep "4s"

    if su - steam -c "screen -list" | grep -q ${CLUSTER_NAME}; then
        echo "didnt shut down in 4 seconds so giving it 20"
        sleep "20s"
    # Should the server still be running; Kill it #
        if su - steam -c "screen -list" | grep -q ${CLUSTER_NAME}; then
            echo "had to kill it"
            command_c "^C"
            command_m "^C"
        fi
    fi
}



running() {
if [ -n "`pgrep -f $BINARYNAME`" ]; then
        return 0
else
        return 1
fi
}

start() {
if ! running; then
        echo -n "Starting the $NAME server... "
        #start-stop-daemon --start --chuid $USER --user $USER --chdir $BINARYPATH --exec "/usr/bin/screen" -- -dmS $SCREENREF $BINARYPATH
        start-stop-daemon --start --background --chuid $USER --user $USER --chdir $BINARYPATH --pidfile $PIDFILE --exec $DAEMON -- $DAEMON_OPTS
        pgrep -f $BINARYNAME > $PIDFILE
        if [ -s $PIDFILE ]; then
                echo "Done"
        else
                echo "Failed"
                rm $PIDFILE
        fi
else
        echo "The $NAME server is already started."
fi
}

#running = `pgrep -f $BINARYNAME`
stop() {
if running; then
        echo -n "Stopping the $NAME server... "
        stop_server
        start-stop-daemon --stop --chuid $USER --user $USER --chdir $BINARYPATH --pidfile $PIDFILE
        kill `pgrep -f $BINARYNAME`
        while running; do
                sleep 1
        done
        rm $PIDFILE
        echo "Done"

else
        echo "The $NAME server is already stopped."
fi
}

case "$1" in
start)
start
;;
stop)
stop
;;
restart)
stop
start
;;
status)
if running; then
        echo "The $NAME server is started."
else
        echo "The $NAME server is stopped."
fi
;;
*)
echo "Usage: $0 (start|stop|restart|status)"
exit 1
esac
exit 0
