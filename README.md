# DST-Portal-
A python web management portal for the game "Don't Starve Together"

This portal was created so i could give friends just enough permissions to add mods and reboot/restart the server when it was running slow.
Some understanding of DST / the ability to read code may be required to use this portal until further instructions have been provided.
It would be easy to modify the web portal to include features such as kick/ban by using the existing functions/code to base the new features on.
  (however this wasnt requried for my intended purpose)

I'll be the first to admit its a bit of a hack job, but it serves it's purpose. (would be nice to add user roles and a proper login - but i wanted to make it as simple as possible and reduce external requirements)

This portal was designed so that the web server could operate on a different server to the DST dedicated Unix server.

Files
Web portal:
> "index.py"  the front end python file for the web server, relies on the two files below to start and stop the service.

(I ran this on my windows IIS web server with python installed - requires CGI)
  This post highlights how to install python for use with IIS.
  https://stackoverflow.com/questions/6823316/python-on-iis-how


Unix DST files:
> "~/DST/startCluster.sh"
this installs and starts the Unix dedicated server (reboots every night at 4AM as well as restarts for updates)

> "/etc/Init.d/svcCluster.sh"
this starts the server when the PC starts, it also restarts the servers called from the web portal.
