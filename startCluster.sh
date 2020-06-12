#!/bin/bash

#this file should be placed in your install folder eg ~/DST
#Code for starting DST - startCluster.sh
# adapted from / origional source located in this forum post: 
#https://forums.kleientertainment.com/forums/topic/100595-self-updating-server-startup-script-linux/
# you could update this to use the builds.json method, as mentioned in the comments, which this source code does not.

#### User Variables; Set your preferences ####

CLUSTER_NAME="Cluster" #change me for additional instances 1 of 1
MASTER_NAME="Master"
CAVE_NAME="Caves"

CHECK_UPDATE_FREQ="20m"

DONT_STARVE_CLUSTER_DIR="$HOME/.klei/DoNotStarveTogether"
DONT_STARVE_DIR="$HOME/DST"

#### Script Variables; Do not modify ####

lv_file="/tmp/${CLUSTER_NAME}_latest_version"
DONT_STARVE_BIN="./dontstarve_dedicated_server_nullrenderer"

#### Functions ####

function needs_update() {
    klei_url="https://forums.kleientertainment.com/game-updates/dst/"
    latest_version=$(curl -s $klei_url | grep -Po "\s+\d{6,}$" | head -n 1)
    if [[ -e $lv_file ]]; then
        current_version=$(head -n 1 $lv_file)
    fi
    echo $latest_version > $lv_file
    if [[ $current_version -lt $latest_version ]]; then
        echo "1"
    else
        echo "-1"
    fi
}

function exists() {
    if [[ ! -e $1 ]]; then
        failed "File/Dir not found: $1"
    fi
}

function failed() {
    echo "Error: $@" >&2
    exit 1
}

function command_m() {
    screen -S ${CLUSTER_NAME}_${MASTER_NAME} -p 0 -X stuff "$1^M"
}

function command_c() {
    screen -S ${CLUSTER_NAME}_${CAVE_NAME} -p 0 -X stuff "$1^M"
}

function stop_server() {
    command_m 'c_announce("Server stopped by force! Shutting down!")'
    echo "Shutting down by force"
    sleep "2s"
    command_c 'c_shutdown()'
    command_m 'c_shutdown()'

    # The server gets 30 seconds to shutdown normally #
    sleep "30s"

    # Should the server still be running; Kill it #
    if screen -list | grep -q ${CLUSTER_NAME}; then
        echo "had to kill it"
        command_c "^C"
        command_m "^C"
    fi
    exit 1
}

#### Script routine ####

trap stop_server 2

# Check for missing files #

exists "$DONT_STARVE_CLUSTER_DIR/$CLUSTER_NAME/cluster.ini"
exists "$DONT_STARVE_CLUSTER_DIR/$CLUSTER_NAME/cluster_token.txt"
exists "$DONT_STARVE_CLUSTER_DIR/$CLUSTER_NAME/$MASTER_NAME/server.ini"
exists "$DONT_STARVE_CLUSTER_DIR/$CLUSTER_NAME/$CAVE_NAME/server.ini"

# Check for an update beforehand #
needs_update 2>&1 >/dev/null

while [[ true ]]; do

    # Force an update #
    mv "$DONT_STARVE_DIR/mods/dedicated_server_mods_setup.lua" "$DONT_STARVE_DIR/mods/dedicated_server_mods_setup.lua.bak"
    echo "Start updating the game."
    steamcmd +force_install_dir $DONT_STARVE_DIR +login anonymous +app_update 343050 +quit
    mv "$DONT_STARVE_DIR/mods/dedicated_server_mods_setup.lua.bak" "$DONT_STARVE_DIR/mods/dedicated_server_mods_setup.lua"

    # Check for DST binary #
    exists "$DONT_STARVE_DIR/bin"

    # Run Shards #
    cd "$DONT_STARVE_DIR/bin"
    echo "Starting ${CAVE_NAME}."
    screen -d -m -S ${CLUSTER_NAME}_${CAVE_NAME} $DONT_STARVE_BIN -cluster $CLUSTER_NAME  -shard $CAVE_NAME
    echo "Starting ${MASTER_NAME}."
    screen -d -m -S ${CLUSTER_NAME}_${MASTER_NAME} $DONT_STARVE_BIN -cluster $CLUSTER_NAME  -shard $MASTER_NAME
    # Checks for updates #
    while [[ true ]]; do

        # Check for updates every 20 minutes #
        sleep $CHECK_UPDATE_FREQ

        # If there is an update, we will start the shutdown process #
        result=$(needs_update)
        if [[ $result -gt 0 ]]; then
            echo "The server needs an update. Will restart in 15 minutes."
            command_m 'c_announce("Klei released an update! The server restarts in 15 minutes!")'
            sleep "10m"
            command_m 'c_announce("Klei released an update! The server restarts in 5 minutes!")'
            sleep "4m"
            command_m 'c_announce("Klei released an update! The server restarts in 1 minute!")'
            sleep "1m"
            command_m 'c_announce("Restarting now!")'
            sleep "2s"
            command_c 'c_shutdown()'
            command_m 'c_shutdown()'
            break
        fi

        H=$(date +%-H%M)
        if (( 400 <= $H && $H < 420 )); then
            echo "Server will be going down for nightly restart in 15 minutes."
            command_m 'c_announce("Server will be going down for nightly restart in 15 minutes!")'
            sleep "10m"
            command_m 'c_announce("Server will be going down for nightly restart in 5 minutes!")'
            sleep "4m"
            command_m 'c_announce("Server will be going down for nightly restart in 1 minute! See you on the other side")'
            sleep "1m"
            command_m 'c_announce("Restarting now!")'
            sleep "2s"
            command_c 'c_shutdown()'
            command_m 'c_shutdown()'
            break
        fi

    done

    # We wait till the game shuts down #
    echo "Waiting for shards to shut down."
    while [[ true ]]; do
        if ! screen -list | grep -q ${CLUSTER_NAME}; then
            echo "Shards are down. Restarting."
            break
        fi
    done
done
