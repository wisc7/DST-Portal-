#This file is not a script but a mix of instructions with commands to run. 

#Instructions are commented out user entry to update is in <> brackets.

#From an empty VM (debian): from the standard user account:


#login as root

su

<YourRootPassword>

#install sudo

apt-get install sudo 

/sbin/adduser <your user account> sudo


#(close/exit and relog in)

exit 

#install steamcmd instructions below mostly from: https://developer.valvesoftware.com/wiki/SteamCMD#Linux

#create a new user:

sudo useradd -m steam


#Add non free repos to debian.

sudo nano /etc/apt/sources.list 

<add the following line to the end of the file:  deb http://http.us.debian.org/debian stable main contrib non-free >

<save and exit>


sudo apt update

sudo dpkg --add-architecture i386

sudo apt install lib32gcc1 steamcmd 

sudo -iu steam

bash

./steamcmd +login anonymous +force_install_dir /home/steam/DST +app_update 343050 +quit
