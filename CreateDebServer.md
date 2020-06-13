#This file provides instructions on how to install DST on a clean install of debian.  it is not a script, but a mix of instructions with commands to run. 

#Instructions are commented out user entry to update is in <> brackets.

#From an empty VM (debian): from the standard user account:


#login as root

su

<YourRootPassword>

#install sudo

apt-get install sudo 

/sbin/adduser <your user account> sudo

#(exit SU then exit the regular user and relog in to the server again)

exit 

exit 

<relog/SSH in to debian server again with the regualar user that now has SUDO access.>

#install steamcmd instructions below mostly from: https://developer.valvesoftware.com/wiki/SteamCMD#Linux

#create a new user:

sudo useradd -m steam

#configure the account to have a password.

passwd steam

#<set a strong steam password - this is required by the portal>

#Add non free repos to debian.

sudo nano /etc/apt/sources.list 

<add the following line to the end of the file:  deb http://http.us.debian.org/debian stable main contrib non-free >

<save and exit file>


sudo apt update

sudo dpkg --add-architecture i386

sudo apt install lib32gcc1 steamcmd 

sudo -iu steam

bash

steamcmd +login anonymous +force_install_dir /home/steam/DST +app_update 343050 +quit
