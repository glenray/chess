from pgnPillagers.pgnPillager import pgnPillager
from urllib.parse import urlparse
from pathlib import Path
import strings as sql

class pillageTWIC(pgnPillager):
	'''
	Download, decompress, and save zipped pgn files from The Week in Chess
	https://theweekinchess.com/twic
	'''
	def __init__(self):
		super().__init__()
		# TWIC responds with 406 error unless a user-agent is provided
		self.reqHeaders={
			'user-agent': 'Mozilla/5.0(Windows NT 10.0;Win64;x64;rv:81.0)Gecko/20100101 Firefox/81.0'
		}
		self.twicZipPaths = {}	# Dict of available pgn zip files at TWIC
		self.dbTwicSources = [] # List of souces already in DB

	def main(self):
		zips = self.getZipPaths()
		for zip in zips:
			filename = Path(zip['href']).name
			# strip non-digits from the file name, leaving only the volume number
			digits = ''.join(i for i in filename if i.isdigit())
			if int(digits) > firstVol or firstVol == None:
				file = self.dlFile(zip['href'], headers=self.reqHeaders)
				self.unzipFile(file, 'TWIC/')

	def getNewPaths(self):
		newPaths = list(set(self.twicZipPaths.keys()) - set(self.dbTwicSources))
		return newPaths

	def setTwicZipPaths(self):
		'''
		TWIC keeps links to pgn zip archives at https://theweekinchess.com/twic
		The files are formatted: 'twic<D>g.zip' where <D> is a digit corresponding
		to the weekly edition.
		'''
		soup = self.getSoup("https://theweekinchess.com/twic", headers=self.reqHeaders)
		zipAnchors = soup.find_all(href=self.re.compile('zips/.*g\\.zip'))
		self.twicZipPaths = {Path(el['href']).name : el['href'] for el in zipAnchors}

if __name__ == '__main__':
	pass
	# from pgn_importer import pgn_importer
	# a=pillageTWIC()
	# a.setTwicZipPaths()
	# a.getNewPaths()
	# zipfile = a.dlFile(a.twicZipPaths['twic920g.zip'], a.reqHeaders)
	# unzipper = a.unzipFile(zipfile)
	# for zipfile in unzipper:
	# 	breakpoint()
	# 	b=pgn_importer(zipfile, 'test', freshStart=True, dbName='temp')
	# 	b.testGameFile()
