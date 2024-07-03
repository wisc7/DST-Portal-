> This file provides instructions on how to install DST on a clean install of debian.  it is not a script, but a mix of instructions with commands to run. (These instructions can pretty much be used for any dedicated server though, just get the APID from the steam site: https://developer.valvesoftware.com/wiki/Dedicated_Servers_List and change the forced folder location. (then figure out the start up commands for the server)

> #Instructions are commented out user entry to update is in <> brackets.

> #From an empty VM (debian): from the standard user account:


> #login as root

su

<YourRootPassword>

> #install sudo

apt-get install sudo 

/sbin/adduser <your user account> sudo

> #(exit SU then exit the regular user and relog in to the server again)

exit 

exit 

<relog/SSH in to debian server again with the regualar user that now has SUDO access.>

> #install steamcmd instructions below mostly from: https://developer.valvesoftware.com/wiki/SteamCMD#Linux

> #create a new user:

sudo useradd -m steam

> #configure the account to have a password.

passwd steam

> #<set a strong steam password - this is required by the portal>

> #Add non free repos to debian. (you could pick another one closer to you but were only dling steam from here so not to big an issue)
> #only do one of the following option 1/2

> Option 1:

sudo nano /etc/apt/sources.list 

<add the following line to the end of the file:  deb http://http.us.debian.org/debian stable main contrib non-free >

<save and exit file>

> Option 2: 

sudo sh -c 'printf "\ndeb http://http.us.debian.org/debian stable main contrib non-free\n" >> /etc/apt/sources.list'

> End Options:

sudo apt update

sudo dpkg --add-architecture i386

sudo apt install lib32gcc1 steamcmd 

sudo -iu steam

bash

steamcmd +login anonymous +force_install_dir /home/steam/DST +app_update 343050 +quit
