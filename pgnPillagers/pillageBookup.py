from pgnPillager import pgnPillager

# Download 500 pgn files hosted by my old toastmaster friend, Mike Leahy, 
# in connection with this Bookup Pro software.
# See http://www.chessopeningspgn.com/chess/Openings.html
# On cursory inspection, some of these files have many games (e.g.,A00.pgn) 
# with no moves after the headers, only the result, eg 0-1. It's possible that 
# most of the games are like that.
class pillageBookup(pgnPillager):
	def __init__(self):
		super().__init__()

	def main(self):
		pages = [
			'http://www.bookuppro.com/ecopgn/a.html',
			'http://www.bookuppro.com/ecopgn/b.html',
			'http://www.bookuppro.com/ecopgn/c.html',
			'http://www.bookuppro.com/ecopgn/d.html',
			'http://www.bookuppro.com/ecopgn/e.html'
		]

		for page in pages:
			soup = self.getSoup(page)
			links = soup.find_all(href=self.re.compile('.*\\.pgn'))
			for link in links:
				fileURL = link['href']
				file = self.dlFile(fileURL)
				fileName = fileURL.split('/')[-1]
				self.saveFile(file, fileName, 'Bookup')

if __name__ == '__main__':
	a=pillageBookup()
	a.main()