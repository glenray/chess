from pgnPillager import pgnPillager

# The pgnmentor.com website makes available a collection of chess pgn files.
# The problem: They are broken into collections -- hundreds of them.
# There are collections for player, openings and events.
# The players and openings collections are zipped. The events collections are not.
# Events are broken down by Tournaments, Candidates and Interzonals, 
# 	and World Championships
# Let's download them all, 1425 files in all (2 gigs), unzipping when necessary.
class pillagePGNMentor(pgnPillager):
	def __init__(self):
		super().__init__()
		self.soup = self.getSoup("https://www.pgnmentor.com/files.html")

	# Event are in pgn format and do not need to be unziped
	def getEvents(self):
		events = self.soup.find_all(href=self.re.compile('events/.*\\.pgn'), class_='view')
		for event in events:
			url = f"https://www.pgnmentor.com/{event['href']}"
			file = self.dlFile(url)
			fileName = event['href'].split('/')[-1]
			self.saveFile(file, fileName, 'extracted/events/')

	def getOpenings(self):
		openings = self.soup.find_all(href=self.re.compile('openings/.*\\.zip'), class_='view')
		for opening in openings:
			url = f"https://www.pgnmentor.com/{opening['href']}"
			file = self.dlFile(url)
			self.unzipFile(file, 'extracted/openings')
		
	def getPlayers(self):
		players = self.soup.find_all(href=self.re.compile('players/.*\\.zip'), class_='view')
		for player in players:
			url = f"https://www.pgnmentor.com/{player['href']}"
			file = self.dlFile(url)
			self.unzipFile(file, 'extracted/players/')

	def getAll(self):
		self.getEvents()
		self.getOpenings()
		self.getPlayers()

if __name__ == '__main__':
	a=pillagePGNMentor()
	a.getOpenings()