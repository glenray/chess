from pgnPillager import pgnPillager
import requests
import html
import pickle

# scrape the chess opening names and lines from 
# various pages at www.chessarch.com
class pillageOpenings(pgnPillager):
	def __init__(self):
		super().__init__()
		self.reqHeaders={
			'user-agent': 'Mozilla/5.0(Windows NT 10.0;Win64;x64;rv:81.0)Gecko/20100101 Firefox/81.0'
		}
		self.namedOpenings = {}

	# process a low level page
	def main(self):
		retDict = {}
		for url in self.lowLevelURLs:
		# for url in testURLs:
			print(f"Getting {url}.")
			soup = self.getSoup(url)
			tables = soup.find("body").find_all("table")
			numbTables = len(tables)
			# each low level pages consists of nested tables
			# the relevant data starts on the 5th table through the last
			# most pages have a table for more than one eco. 
			# For those, the eco is in the table under the caption.
			# a few pages are devoted to a single eco.
			# for those, the eco is in the previous table.
			for table in tables[4:numbTables]:
				# get the eco number for the table; this will be the dictionary key
				eco = table.find('caption').text if numbTables>5 else tables[3].text.strip()
				retDict[eco] = []
				for row in table.find_all('tr'):
					# some rows in A0 page are blank. Skip those
					if row.text.strip() == '' : continue
					temp = []
					for cell in row.find_all('td'):
						# The elipsis is byte \x85. I can't figure out the encoding.
						# We'll replace those with 3 periods.
						temp.append(cell.text.replace('\x85', '...').replace('\r\n', " "))
					retDict[eco].append(temp)
		self.namedOpenings = retDict
		
	# There are links to 5 pages for each eco letter at baseURL+mainPage
	# assign those links to self.topLevelECO
	def getTopLevelURLs(self):
		self.topLevelECO = []
		baseURL = 'http://www.chessarch.com/library/0000_eco/'
		mainPage = 'index.shtml'
		soup = self.getSoup(baseURL+mainPage)
		tables = soup.find_all("table")
		hrefs = tables[2].select("a")
		for href in hrefs:
			self.topLevelECO.append(baseURL+href['href'])
			print(f"Got top Level: {baseURL+href['href']}")

	# On each top level page, there are links to sub pages for that eco letter
	# assign those links to self.lowLevelURLs
	def getLowLevelURLs(self):
		self.lowLevelURLs=[]
		baseURL = "http://www.chessarch.com/library/0000_eco/"
		for url in self.topLevelECO:
			soup = self.getSoup(url)
			tables = soup.find_all("table")
			hrefs = tables[2].select("a")
			for href in hrefs:
				self.lowLevelURLs.append(baseURL+href['href'])
				print(f"Got low Level: {baseURL+href['href']}")

	def printOpenings(self):
		for key in self.namedOpenings:
			print(key)
			for opening in self.namedOpenings[key]:
				# In Sokolsky: Tⁿbingen 1...Nh6
				# the n char should be Latin Small Letter U With Diaeresis
				# see https://www.codetable.net/hex/fc
				# These are correct characters but displays wrong in powershell
				# and sublime text
				# for power shell, this answer was helpful:
				# https://stackoverflow.com/a/57134096
				# I implemented the region setting trick, ie.intl.cpl
				# foreign chars now appear correctly!
				# or we could try to search and replace them like so:
				# name = opening[1].replace('\xFC', 'u')
				name = opening[1]
				print(f'\t{name} {opening[0]}')

	def saveOpenings(self, obj=None, name='openings.pkl'):
		if obj==None:
			obj = self.namedOpenings
		with open(name, 'wb') as f:
			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

	def loadOpenings(self, name='openings.pkl'):
		with open(name, 'rb') as f:
			self.namedOpenings = pickle.load(f)

	# generate full move list for each opening variation
	# substituting ... with the beginning moves
	def fullMoveList(self):
		for key in self.namedOpenings:
			if key == 'A00':
				self.A00()
			else:
				beginner = self.namedOpenings[key][0][0]
				for opening in self.namedOpenings[key]:
					if opening[0] == beginner:
						moveList = beginner
					else:
						i = opening[0].find('...')
						if i>-1:
							moveList = beginner+' '+opening[0][i+3:]
						else:
							moveList = beginner+" "+opening[0]
					print(f"{opening[1]}\n{moveList}\n")

	def A00(self):
		A00 = self.namedOpenings['A00']
		beginner = ""
		for opening in A00:
			i = opening[0].find('...')
			if i == -1:
				beginner = opening[0]
				moveList = opening[0]
			else:
				moveList = beginner + ' ' + opening[0][i+3:]
			print(f"{opening[1]}\n{moveList}\n")

if __name__ == '__main__':
	# import pickle
	# from pgnPillager import pgnPillager
	from pillageOpenings import pillageOpenings

	a=pillageOpenings()
	# a.getTopLevelURLs()
	# a.getLowLevelURLs()
	# a.main()
	# a.saveOpenings()
	a.loadOpenings()
	# a.printOpenings()
	a.fullMoveList()
