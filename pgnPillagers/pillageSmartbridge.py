from pgnPillager import pgnPillager
from pathlib import Path

class pillageSmartBridge(pgnPillager):
	'''
	https://www.angelfire.com/games3/smartbridge/
	A rather anonomous collection of annotated games in a large number of zip files.
	'''
	def __init__(self):
		super().__init__()
		self.main()

	def main(self):
		self.soup = self.getSoup("https://www.angelfire.com/games3/smartbridge/")
		zips = self.soup.find_all(href=self.re.compile('.*\\.zip'))
		for zip in zips:
			filename = Path(zip['href']).name
			file = self.dlFile(f"https://www.angelfire.com/games3/smartbridge/{filename}")
			self.saveFile(file, filename, '.')


if __name__ == '__main__':
	a = pillageSmartBridge()
	a.main()
