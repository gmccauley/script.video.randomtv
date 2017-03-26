import xbmc
import xbmcgui
import xbmcaddon
import json
import random
import threading
import sys


def log(msg):
	xbmc.log("%s: %s" % (name,msg),level=xbmc.LOGDEBUG )
	#xbmc.log("%s: %s" % (name,msg), xbmc.LOGNOTICE)
  
  
def ResetPlayCount(myEpisode):
	xbmc.sleep(5000)
	log("--------- ResetPlayCount")
	log("-- Episode Id: " + str(myEpisode['episodeId']))
	log("-- Last Played: " + myEpisode['lastPlayed'])
	log("-- Play Count: " + str(myEpisode['playCount']))
	log("-- Resume Position: " + str(myEpisode['resume']['position']))
	log("-- Resume Total: " + str(myEpisode['resume']['total']))
	command = '{"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": { "episodeid": %d, "lastplayed": "%s", "playcount": %d, "resume": { "position": %d, "total": %d } }, "id": 1}' % (myEpisode['episodeId'], myEpisode['lastPlayed'], myEpisode['playCount'], myEpisode['resume']['position'], myEpisode['resume']['total'])
	response = json.loads(xbmc.executeJSONRPC(command))
	log("-- " + str(response))

  
class MyPlayer(xbmc.Player):
	def __init__(self, *args):
		xbmc.Player.__init__(self, *args)
		self.scriptStopped = False
		self.mediaStarted = False
		
	def onPlayBackStarted(self):
		log("------------------------ Start")
		self.mediaStarted = True

	def onPlayBackEnded(self):
		log("------------------------ End")

	def onPlayBackStopped(self):
		log("------------------------ Stop")
		self.scriptStopped = True
		
	def onPlayBackSeekChapter(self):
		log("------------------------ Next")
#


# Set some variables
addon = xbmcaddon.Addon()
addonid = addon.getAddonInfo("id")
name = addon.getAddonInfo("name")
icon = addon.getAddonInfo("icon")

busyDiag = xbmcgui.DialogBusy()
myEpisodes = []
myPlaylist = []
playlistFull = False

includedShows = addon.getSetting("includedShows")


# Select Shows Settings Dialog
if len(sys.argv) > 1:
	if sys.argv[1] == "SelectShows":
		log("--------- Settings - SelectShows")
		busyDiag.create()
		listShows = []
		listPreSelect = []
		listPostSelect = []
		command = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"sort": {"ignorearticle": true, "method": "label", "order": "ascending"}}, "id": 1}'
		allShows = json.loads(xbmc.executeJSONRPC(command))
		if allShows['result']['limits']['total'] > 0:
			for show in allShows['result']['tvshows']:
				listShows.append(show['label'])
				
				if not includedShows == "":
					if show['tvshowid'] in map(int, includedShows.split(", ")):
						listPreSelect.append(len(listShows) - 1)

			
		busyDiag.close()
		selectedShows = xbmcgui.Dialog().multiselect("Select TV Shows", listShows, preselect=listPreSelect)

		
		if not selectedShows is None:
			for selectedShow in selectedShows:
				listPostSelect.append(allShows['result']['tvshows'][selectedShow]['tvshowid'])
			
			includedShows = ", ".join(str(i) for i in listPostSelect)
			addon.setSetting("includedShows", includedShows)

		#addon.openSettings()
		xbmc.executebuiltin('Addon.OpenSettings(%s)' % addonid)
		xbmc.executebuiltin('SetFocus(205)')
	quit()
#


# Display Starting Notification
if addon.getSetting("ShowNotifications") == "true": xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(name, "Starting", 1000, icon))
log("-------------------------------------------------------------------------")
log("Starting")


# Get TV Episodes
if addon.getSetting("IncludeAll") == "true":
	command = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "id": 1}'
	allShows = json.loads(xbmc.executeJSONRPC(command))
	
	if allShows['result']['limits']['total'] > 0:
		for show in allShows['result']['tvshows']:
			command = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %d, "properties": ["showtitle", "file", "playcount", "lastplayed", "resume"] }, "id": 1}' % (show['tvshowid'])
			allEpisodes = json.loads(xbmc.executeJSONRPC(command))
			
			if allEpisodes['result']['limits']['total'] > 0:
				for episode in allEpisodes['result']['episodes']:
					if addon.getSetting("IncludeUnwatched") == "false" or episode['playcount'] > 0:
						log("Added Episode: " + episode['label'].encode('utf-8').strip())
						myEpisodes.append({'episodeId': episode['episodeid'], 'episodeShow': episode['showtitle'].encode('utf-8').strip(), 'episodeName': episode['label'].encode('utf-8').strip(), 'episodeFile': episode['file'].encode('utf-8').strip(), 'playCount': episode['playcount'], 'lastPlayed': episode['lastplayed'], 'resume': episode['resume']})
else:
	for includedShow in map(int, includedShows.split(", ")):
		command = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %d, "properties": ["showtitle", "file", "playcount", "lastplayed", "resume"] }, "id": 1}' % includedShow
		allEpisodes = json.loads(xbmc.executeJSONRPC(command))
			
		if allEpisodes['result']['limits']['total'] > 0:
			for episode in allEpisodes['result']['episodes']:
				if addon.getSetting("IncludeUnwatched") == "true" or episode['playcount'] > 0:
					log("Added Episode: " + episode['label'].encode('utf-8').strip())
					myEpisodes.append({'episodeId': episode['episodeid'], 'episodeShow': episode['showtitle'].encode('utf-8').strip(), 'episodeName': episode['label'].encode('utf-8').strip(), 'episodeFile': episode['file'].encode('utf-8').strip(), 'playCount': episode['playcount'], 'lastPlayed': episode['lastplayed'], 'resume': episode['resume']})
		

log("Total Episodes: " + str(len(myEpisodes)))


# Initialize our Player
player = MyPlayer()


# If no episodes, display notification and quit
if len(myEpisodes) == 0:
	log("No episodes")
	player.mediaStarted = False
	player.scriptStopped = True
	xbmcgui.Dialog().ok(name, "No available episodes to play", "Please check your settings")
	addon.openSettings()
else:
	log("Episodes Available")
	thePlaylist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	thePlaylist.clear()
	firstRun = True
#

while (not xbmc.abortRequested):
	while (thePlaylist.getposition() + 5) > len(myPlaylist) and not playlistFull:
		log("--------- Loop - Add to Playlist")
		log("myPlaylist Size: " + str(len(myPlaylist)))
		log("thePlaylist Size: " + str(thePlaylist.size()))

		if thePlaylist.size() == len(myEpisodes):
			log("Playlist Full")
			playlistFull = True
			break
		#
		
		log("Adding to myPlaylist")
		intLoopCount = 0
		while True:
			intLoopCount += 1
			tempEpisode = myEpisodes[random.randint(0, len(myEpisodes) - 1)]
			if not tempEpisode in myPlaylist: break
			if intLoopCount > 5: break
		#

		myPlaylist.append(tempEpisode)
		thePlaylist.add(url=myPlaylist[len(myPlaylist) - 1]['episodeFile'])
		log("-- Episode Id: " + str(myPlaylist[len(myPlaylist) - 1]['episodeId']) + "  --  " + myPlaylist[len(myPlaylist) - 1]['episodeShow'] + " - " + myPlaylist[len(myPlaylist) - 1]['episodeName'])
	#
	xbmc.sleep(100)


	if firstRun:
		log("--------- firstRun")
		player.play(item=thePlaylist)
		xbmc.executebuiltin('PlayerControl(Repeat)')
		firstRun = False
	#


	if player.mediaStarted:
		log("--------- mediaStarted")
		if 'lastEpisode' in locals():
			log("-- lastEpisode")
			if addon.getSetting("UpdatePlayCount") == "false":
				log("-- Start ResetPlayCount Thread")
				thread = threading.Thread(target=ResetPlayCount, args=(myPlaylist[lastEpisode],))
				thread.start()
			#
		#

		log("-- Started: " + myPlaylist[thePlaylist.getposition()]['episodeShow'] + " - " + myPlaylist[thePlaylist.getposition()]['episodeName'])
		if addon.getSetting("ShowNotifications") == "true": xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(name, myPlaylist[thePlaylist.getposition()]['episodeShow'] + "\r\n" + myPlaylist[thePlaylist.getposition()]['episodeName'], 5000, icon))
		
		log("-- Playlist Position: " + str(thePlaylist.getposition()))
		
		lastEpisode = thePlaylist.getposition()
		player.mediaStarted = False
	#


	if player.scriptStopped:
		log("--------- scriptStopped")
		if addon.getSetting("UpdatePlayCount") == "false" and 'lastEpisode' in locals():
			log("-- Start ResetPlayCount Thread")
			thread = threading.Thread(target=ResetPlayCount, args=(myPlaylist[lastEpisode],))
			thread.start()
		break
#


# All Done
# Display Stopping Notification
if addon.getSetting("ShowNotifications") == "true": xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(name, "Stopping", 2000, icon))
log("Stopping")
log("-------------------------------------------------------------------------")
#xbmc.sleep(2000)
