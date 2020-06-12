#Disclaimer:
#Please note: This script has not been tested for injection attacks, unsure if we could potentially have HTML/ PY injected (especially given the source is available)
#WARNING: Given we are passing user input to the command shell this could be dangerous and allow a system to be compromised. (this is somewhat mitigated with the input checks) 
#IE: Use at your own risk, by using this script, you agree that the author will take no responsibility for your network being hacked/broken etc.
#tested on IIS running python. (IIS must have CGI set to impersonate user true, the website user is configured as a low permission user, the a app pool also uses this user.)

#Notes:
# the password for your Linux steam service accounts must be stored in your host keyvault to set the password: - using the keyring library
#keyring.set_password('twitter', 'xkcd', 'correct horse battery staple')
#mods files will have to be formatted right to work correctly (IE spacing), and it will only turn them on rather than configure them. https://dontstarve.gamepedia.com/Guides/Simple_Dedicated_Server_Setup
#sample line
#    ["workshop-1299647282"] = { enabled = true},

#PS. i'll be spewing when/if they release an API for DST as it will mean a rewrite!

# DST will need to be running as a service for this portal to run correctly with the clustername in the init.d file: /etc/init.d/svc<Clustername.sh> (see below for a sample file)
# Your going to have to pip install the missing packages on your web server so it can run the below.

#(sleep) (login to unix) (retrieve password) (web post) (regular expressions) (race condition), (parse web headers), (for HTML escape/encoding)
import time, paramiko, keyring, cgi, re, random, os, html

#(get patch name, confirm it exists)
from mechanize import Browser
#(required to check if its OK to reboot/restart)
from datetime import datetime, timedelta
form = cgi.FieldStorage() # get the post variables.


#debug code, uncomment to get more info.
import cgitb
cgitb.enable()

## config variables - for you to configure
SitePassword = "YourPasswordHere" #yep this is lazy. we could store this in the keyvault - or a config file or heck anywhere else, but i wanted it easily accessible/modifiable. 
DSTServer ='xxx.xxx.xxx.xxx' # the IP address that your webserver can access to access your DST servers.
SteamUserName = 'steam' # DST user account name
SUUserName = 'SuperUser' #system user that has permissions to reboot the box /restart the machine.
Initial_instance = 'ClusterName' # your first/main/only DST Together cluster name, (this should be set as your filename in /etc/init.d and to start the server in the DST folder.) will be over written if the you have multiple and the user selects a differt instance.
if "Instance" in form:
    Cluster_name =  form["Instance"].value.strip()
else:
    Cluster_name = Initial_instance

#location variables (that said you'll probably need to modify paths, as mine are different to others.)
DSTPath="/home/steam/DST/"
ClusterPath="/home/steam/.klei/DoNotStarveTogether/"+Cluster_name
DSTPathMod=ClusterPath+"/Master/modoverrides.lua"

ServiceCmd="/etc/init.d/svc"+Cluster_name+".sh"

#variables setup - you shouldnt need to to touch these,
thispageurl=os.environ.get('HTTP_HOST')+os.environ.get('PATH_INFO')
if os.environ.get('HTTPS') == "on":
    thispageurl = "https://"+thispageurl
else:
    thispageurl = "http://"+thispageurl
ModSite = "https://steamcommunity.com/sharedfiles/filedetails/?id="
modpath=DSTPath+"mods/dedicated_server_mods_setup.lua"

#variable initialisation
ListPlayer = [] #create list for storing players
ListMod = []
ListInstances = []
referrer = os.environ.get('HTTP_REFERER') 
CheckFormValue = ""




#check if someone has hacked the form and trying to pass a non modID number in. (Ie. could be an injection attack)
if ("modid" in form):
    try:
        CheckFormValue = int(form["modid"].value)# this will crash if a non int value is selected and we will exit.
    except: #do nothing show them a blank page.
        print('Status: 200 OK')
        print('Content-type: text/html')
        print('')
        exit() 
    if (not isinstance(CheckFormValue, int)): # just to be double sure they arent passing anything other than a number
        pass
        exit()
    

"""Real start!"""
print('Status: 200 OK')
print('Content-type: text/html')
print('')
print('<HTML>')
print('<HEAD><TITLE>Welcome to my test page!</TITLE>')
print('<style>table td, table td * {vertical-align: top;}</style>')
print('</HEAD><BODY>')

#test code to get all the HTTP header info.
#for thing in os.environ:
    #print(thing,":",os.environ.get(thing) ,"<BR>")
#print(thispageurl)

#set up form:
print('<form action="',thispageurl,'" ID="FormID" method="post">')
if ("inpass" not in form) or (thispageurl != referrer): # they haven't put the password in yet, or they have come from another page.
    print('<input type="password" name="inpass">') #password box, not labled on purpose.
    print('<input type="submit" value="Submit">')
    print('</form>')
    print('</BODY></HTML>')
    exit()
elif form["inpass"].value != SitePassword: #they put the password in wrong. give them a fake message
    print("Hi <b>", form["inpass"].value, "</b>you've stumbiled across my test page, do you like how i got your value from the other form - from the same page/URL!? - MAGIC!")
    print('</BODY></HTML>')
    exit()



###################################################################################################
#the magic! - you are validated

def updatefile(installmod): #code to add to the mod file here.
    getCurrentMods() #populate mods list, it will also be done later, however it would need to be updated with the new installed mod anyways.
    formModID = form["modid"].value
    ServerListMod = []
    #build a list of server mods to use later.
    stdin, stdout, stderr = client.exec_command("cat "+modpath) # Extract all mods from the server file
    for line in stdout: 
        if line[:15] == "ServerModSetup(":
            endpos = line.find(')')
            ServerListMod.append(line[16:endpos-1]) 
 
    #check if we already have the mod installed in this instance
    for line in ListMod:
        dashes = line.find(" --")
        if line[0:dashes] == installmod:
            print('<BR><p style=\"color:red;\">Mod already installed</p>')
            return
    #check what the mod they actually want to install is:
    url = ModSite+installmod
    br = Browser()
    br.open(url)
    title = br.title().strip()
    if title[0:16] != "Steam Workshop::":
        print('<BR><p style=\"color:red;\">Not a mod from <a href=\"https://steamcommunity.com/app/322330/workshop/\">the steam workshop site.</a></p>')
        return
    title= re.sub("Steam Workshop::", '', br.title().strip())
    
    if "ConfirmUpdate" in form: #they have already said ok on the popup confirmation. - probably should have done this via the button onclick=\"return confirm('Are you sure you want add this mod?') - but already did it this way
        print("Added to Mod list, DST service will need a restart before it goes live")
        
        #update first file (server modfile) 
        #add to the end of server mod file #/home/steam/DST/mods/dedicated_server_mods_setup.lua (note this is mods for the whole server, not just the instance of DST)
        if formModID not in ServerListMod: #we only need to update the server list if it hasnt been updated before
            client.exec_command("echo 'ServerModSetup(\""+formModID+"\") --"+title.strip()+"' >> "+modpath)
        
        
        #update second file
        #now add it into the instance file #"/home/steam/.klei/DoNotStarveTogether/"+Cluster_name+"/modoverrides.lua"
        #client.exec_command("sed -i 's/whatToReplace/replaceItWith\\addlstuff/' test.txt")
        #replace { with { \n    ["workshop-XXXXXXXXXXXXX"] = { enabled = true},
       
        #check if file exists
        fileExist = 0
        stdin, stdout, stderr = client.exec_command("cat "+DSTPathMod)
        for line in stdout: #copy file to list.
            fileExist = 1
        if fileExist==1: #if the file exists
            client.exec_command("sed -i 's/return{/return{\\n    [\\\"workshop-"+formModID+"\\\"] = { enabled = true},/' "+DSTPathMod)
        else: #if not create it
            client.exec_command("printf 'return{\\n    [\\\"workshop-"+formModID+"\\\"] = { enabled = true}\\n}' >> "+DSTPathMod)
            
    else:
        print("<p id=\"Output\"></p>")
        print("<script>var txt;")
        print ("var r = confirm(\"You are about to add the following mod: "+title+"\\n\\nYou should check with all other players before installing.\\n\\nAre you sure you want to install this mod now?\");")
        print("if (r == true) {")
        print('     txt = "<input type=\\"hidden\\" name=\\"ConfirmUpdate\\" value=\\"'+installmod+'\\"> <input type=\\"hidden\\" id=\\"modid\\" name=\\"modid\\" value=\\"'+installmod+'\\"> <input id=\\"AddMod\\" type=\\"hidden\\" name=\\"AddMod\\" value=\\"Add Mod to Server\\" >";')
        print("}")    
        print("document.getElementById(\"Output\").innerHTML = txt;")
        print("document.getElementById(\"FormID\").submit();")
        print ("</script>")


def restartserver(playersOnline): # do the service restart.
    if playersOnline > 0: 
        print("Can't do it captian there are now players online!<BR>")
    else:   
        #print("Not yet implemented: restarting... give it 30 or so seconds...<BR>")
        #restart service
        client.close()
        #gonna need to run this as a SU
        SURetPass = keyring.get_password('steam_service', SUUserName)
        client.connect(DSTServer, username=SUUserName, password=SURetPass)
        stdin, stdout, stderr = client.exec_command("sudo -S "+ServiceCmd+" restart")
        stdin.write(SURetPass+'\n')
        stdin.flush()
        for line in stdout:
            print(line)
        #switch back to the regular user
        client.close()
        client.connect(DSTServer, username=SteamUserName, password=RetPass)

        
def rebootserver(playersOnline): # do the actual reboot.
    currCluster = Cluster_name #store the current cluster
    AllPlayersOnline = playersOnline
    ListInstances.remove(currCluster) 
    
    for line in ListInstances:
        Cluster_name = line
        playersonline()
        AllPlayersOnline = AllPlayersOnline+len(ListPlayer)
    
    #reset it back
    Cluster_name = currCluster
    ListInstances.append(currCluster)
    playersonline()
    
    if AllPlayersOnline > 0:
        print("Can't do it captian there are now players online on one of the instances!<BR>")
    else:   
        client.close()
        #gonna need to run this as a SU
        SURetPass = keyring.get_password('steam_service', SUUserName)
        client.connect(DSTServer, username=SUUserName, password=SURetPass)
        stdin, stdout, stderr = client.exec_command("sudo -S "+ServiceCmd+" stop")
        stdin.write(SURetPass+'\n')
        stdin.flush()
        for line in stdout:
            print(line)
        stdin, stdout, stderr = client.exec_command("sudo -S reboot")
        stdin.write(SURetPass+'\n') 
        stdin.flush()
        print("Server is restarting, give it a couple minutes then refresh the page")
        for line in stderr: #didnt seem to work without this
            pass
        client.close()
        #no point reconnecting server is restarting
        #client.connect(DSTServer, username=SteamUserName, password=RetPass) 

def getCurrentMods():
    InstanceListMod = []
    ListMod.clear() 
    stdin, stdout, stderr = client.exec_command("cat "+DSTPathMod) # Extract everything from the instance mod file.
    for line in stdout:
        firstPos = line.find('"')
        endpos = line.find('-')
        if (line[firstPos+1:endpos] == "workshop" and "true" in line):
            firstPos = line.find('-')
            endpos = line.find(']')
            InstanceListMod.append(line[firstPos+1:endpos-1])
        
    stdin, stdout, stderr = client.exec_command("cat "+modpath) # Extract all mods from the server file
    for line in stdout: 
        if line[:15] == "ServerModSetup(":
            endpos = line.find(')')
            line = line = re.sub("\"\)", '', line)
            if line[16:endpos-1] in InstanceListMod:
                ListMod.append(line[16:]) 

def playersonline():
    tries = 0
    #while we didnt get a read
    while (len(ListPlayer) == 0 or CountHeaders > 2) and tries <= 10: # didn't get a good read or read it twice.
        ListPlayer.clear()
        CountHeaders=0
        tries = tries + 1
        try:  #if they smash the refresh button, it could error!
            client.exec_command('rm '+DSTPath+'bin/screenlog.0') # remove the old screen log file. (if it exists)
            client.exec_command('screen -S '+Cluster_name+'_Master -X log on') #turn on screen logging for the master shard.
            client.exec_command('screen -S '+Cluster_name+'_Master -X stuff \"c_listallplayers()^M\"') #get a list of players
            client.exec_command('screen -S '+Cluster_name+'_Master -X colon \"logfile flush 0.01^M\"') #flush to disk
            time.sleep(0.1) #wait for the write to disk
            client.exec_command('screen -S '+Cluster_name+'_Master -X log off') #turn off the logging.
            stdin, stdout, stderr = client.exec_command("cat "+DSTPath+"bin/screenlog.0")
            client.exec_command('rm '+DSTPath+'bin/screenlog.0')
        except:
            time.sleep(random.random()*5) # (they smashed the refresh button, or two people logging in at once - make them wait a random amount of time up to 5 seconds.)
        for line in stdout: #copy file to list.
            ListPlayer.append(line)
        for line in ListPlayer: 
            if re.search('.+listallplayers.+', line.strip()): #find header lines lines
                CountHeaders = CountHeaders+1
    if tries > 10:
        ListPlayer.append("Error 1 - don't smash the buttons!")
        #print("something went wrong: try again (don't smash the refresh button!).")
        #return
    try: #if the app got confused with them smashing the refresh button we could have an issue here. (log file existed with nothing in it?)
        ListPlayer.pop(0) # get rid of the two header lines
        ListPlayer.pop(0)
    except:
        ListPlayer.append("Error 2 - Either server is not up or don't smash the buttons!")
    print('</pre>')
    print("Players Online:",len(ListPlayer),"<BR>")
    print("<select name=\"players\" size=\"",len(ListPlayer)+2,"\" style=\"width:250px\">")
    if len(ListPlayer) == 0:
        print("<option value=\"None\">None</option>")
    else:
        for line in ListPlayer:
            line = re.sub("[\(\[].*?[\)\]]", "", line)
            line = re.sub(':', '', line)
            print("<option value=\"",line,"\">",line,"</option>")
    print("</select><BR>")
    
def GetLastRestart():
    pid =""
    #get PID of DST server from: /home/steam/DST/dstserver.pid
    stdin, stdout, stderr = client.exec_command("cat "+DSTPath+"dst"+Cluster_name+".pid") # 
    for line in stdout:
        pid = line.strip()
    for line in stderr:
        print("Can't find DST service",DSTPath+"dst"+Cluster_name+".pid",", maybe try waiting until it finishes loading, or contact the server admin.<BR><BR>")
    if pid != "": #wasn't assigned a variable in the last line as the pid was not read.
        stdin, stdout, stderr = client.exec_command("ps -eo pid,lstart |grep "+pid)
        for line in stdout:
            line = line.replace(pid,"").strip()
            LastRestartTimeFun = datetime.strptime(line, '%c')
            print("Last restart:",LastRestartTimeFun,"<BR>")
        return LastRestartTimeFun
    else:
        return datetime.now() # if it breaks return now as a failsafe.

def GetInstances():
    ListInstances.clear()
    #Spos = 0 # position of dot in line.
    stdin, stdout, stderr = client.exec_command("screen -ls")
    for line in stdout: #copy file to list.
        Spos = line.find('.')
        Epos = line.find('(')
        if "Master" in line:
            ListInstances.append(line[Spos+1:Epos-1].replace("_Master","")) 
    stdin, stdout, stderr = client.exec_command("echo $(awk -F \"=\" '/cluster_name/ {printf $2}' "+ClusterPath+"/cluster.ini)") 
    for line in stdout:
        ServerNameIn = line
    return line

def listClusterOptions():
    print("Cluster Options:<BR>")
    print("<select name=\"Cluster\" size=\"10\"><BR>")
    stdin, stdout, stderr = client.exec_command("cat "+ClusterPath+"/cluster.ini") 
    for line in stdout:
        if line[0:1] != '[' and line != '' and line.strip() and "cluster_password" not in line:
            eqpos = line.find('=')-1
            print("<option value=\""+line[0:eqpos]+"\">"+html.escape(line.strip())+"</option>")

def listCurrentMods(): #will show all mods on the server in the mod files. and provide a link to them.
    getCurrentMods()
    print("Mods Installed:",len(ListMod),"<BR>")
    print("<select name=\"Mods\" size=\"",len(ListMod)+2,"\"><BR>")
    if len(ListMod) == 0:
        print("<option value=\"None\">None</option>")
    else:
        for line in ListMod:
            print("<option value=\""+line.strip()+"\">"+line.strip()+"</option>")
    print("</select><BR>")

###########################################################################################################################################################################    
#start here - remember they are validated, so we'll get the password again.
print('<input type="hidden" name="inpass" value="'+SitePassword.strip()+'">' ) #yep, 1. Im being lazy, and 2. its the clear text password, but if they got this far they should already know it (susceptible attack, but hey, its a DST Portal!) - I also run mine though SSL. 

#get credentials from the local machines keyvault server
RetPass = keyring.get_password('steam_service', SteamUserName)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(DSTServer, username=SteamUserName, password=RetPass)

#debug code
#for x in form:
#    print(x,":","<BR>")
#print("<HR>")

#Instance details - set instance name
ServerName = GetInstances()

print ("Instance Name:")
#print ('  <input type="text" id="ServerName" name="ServerName" value="'+html.escape(ServerName.strip())+'\" readonly><br><br></P>')
print(html.escape(ServerName.strip())+"<BR>")

print("<P>Instance: ")
print('<select name="Instance" id="Instance" onchange="this.form.submit()">')
for elem in ListInstances:
    print('  <option ')
    if elem == Cluster_name:
        print('selected')
    print(' value="'+elem+'">'+elem+'</option>')
#print('  <option ')
#if Cluster_name == "none":
#    print('selected')
#print(' value="none">none</option>')    
print('</select></p><br>')


print("<TABLE><TR><TD>")
playersonline() # get players online, print in a HTML table


if "AddMod" in form: #they clicked the add mod to server button
    if "modid" in form: #they also filled in the modid
        #print(form["modid"].value)
        updatefile(form["modid"].value)
    else: # they didnt add a number
        print("You need to add a Mod ID from <a href=\"https://steamcommunity.com/app/322330/workshop/\">the steam workshop site.</a>")

print("</TD><TD style=\"width:10px\">&nbsp;</TD><TD>")
listCurrentMods()  # Print mods
print("</TD><TD style=\"width:10px\">&nbsp;</TD><TD>")
listClusterOptions()
print("</TD></TR></TABLE>")


if "reboot" in form: #they want to reboot!
    LastRestartTime = GetLastRestart()
    #get get last reboot time
    stdin, stdout, stderr = client.exec_command("who -b")
    for line in stdout:
        line = line.replace("         system boot  ","").strip()
        LastRebootTime = datetime.strptime(line.strip()+":00", '%Y-%m-%d %X')
        #print (LastRestartTime)
    #make sure it hasn't been rebooted in the last hour. (should probably check that other instance werent rebooted in the last five, but screw it) 
    if (datetime.now()-timedelta(hours = 1) >  LastRebootTime) and (datetime.now()-timedelta(minutes = 5) >  LastRestartTime):
        rebootserver(len(ListPlayer))
    else:
        print("It needs to be at least an hour between reboots, and five minutes after restarting DST/or the service is not currently running!")

if "restart" in form: #they want to restart!
    LastRestartTime = GetLastRestart()
    #make sure it hasn't been restarted in the last 5 min. (this should also give the server enough time to get up and running)
    if datetime.now()-timedelta(minutes = 5) >  LastRestartTime:
        restartserver(len(ListPlayer))
    else:
        print("It needs to be at least five minutes before we can restart DST again/or the service is not currently running!")

client.close()
print("<BR><BR>")
print("Mod number to add to server: <BR><input type=\"number\" id=\"modid\" name=\"modid\"> <input  id=\"AddMod\" type=\"submit\" name=\"AddMod\" value=\"Add Mod to Server\" >")
print("<BR><BR>")
#print("<input  id=\"But_reboot\" type=\"submit\" name=\"reboot\" value=\"Reboot Server\"" , end = "")
print("<input onclick=\"return confirm('Are you sure you want to reboot the server?');\" name =\"reboot\" id=\"But_reboot\" type=\"submit\" value=\"Reboot Server\"" , end = "")
if len(ListPlayer)>0:
    print(" Disabled", end = "")
print(" />")
#print("<input  id=\"But_restart\" type=\"submit\" name=\"restart\" value=\"Restart DST\"" , end = "")
print("<input onclick=\"return confirm('Are you sure you want to restart the DST Service?');\"  id=\"But_restart\" type=\"submit\" name=\"restart\" value=\"Restart DST\"" , end = "")
if len(ListPlayer)>0:
    print(" Disabled", end = "")
print(" />")
print('<input type="submit" id="regular" value="Refresh" />')
print('</form>')
if len(ListPlayer)>0:
    print("*Note: you can only reboot/restart when players are not on-line and the server is up!")
print('</BODY></HTML>')
