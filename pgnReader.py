import chess.pgn

class pgnReader:
	def __init__(self, pgnPath):
		self.pgnPath = pgnPath
		self.fileObj = open(self.pgnPath, encoding='utf8')

	def getGameList(self, searchParams=None):
		gameList = []
		offsets = self.searchGames(searchParams)
		for offset in offsets:
			gameList.append(self.getOneGame(offset))
		return gameList


	# find games in pgn file based on search parameters
	# @searchParams array of dictionaries
	# @returns array of offsets in pgn file where games are located
	# The dictionary keys must be game header tags and value is the data
	# All key:value pairs mush exist in the header to match (AND)
	# Any dictionary in the array that matches will cause a match (OR)
	# so,
	# searchParams = [
	# 	{'White' : 'Deep Blue', 'Result': '1-0'}, 
	# 	{'Black' : 'Deep Blue', 'Result': '0-1'}
	# ]
	# will show games where Deep Blue won with either color
	def searchGames(self, searchParams):
		offsets = []
		self.fileObj.seek(0)
		while True:
			offset = self.fileObj.tell()
			headers = chess.pgn.read_headers(self.fileObj)
			if headers == None: break
			if searchParams == None:
				offsets.append(offset)
			else:
				for search in searchParams:
					if self.isSubSet(headers, search):
						offsets.append(offset)
		return offsets			

	# get game at offset
	def getOneGame(self, offset):
		self.fileObj.seek(offset)
		return chess.pgn.read_game(self.fileObj)

	# Are all elements of subset in set?
	def isSubSet(self, headers, subset):
		# value in subset must exactly equal set
		# return all(set.get(key, None) == val for key, val in subset.items())
		# value in subset must be somewhere in set
		return all(val in headers.get(key) for key, val in subset.items())

if __name__ == '__main__':
	gamefile = [
		'pgn/Kasparovs_Games.pgn',
		'pgn/Adams.pgn',
		'pgn/millionbase-rev.pgn'
	]
	dbWins = [
		{'White' : 'Deep Blue', 'Result': '1-0'}, 
		{'Black' : 'Deep Blue', 'Result': '0-1'}
	]
	dbWhiteTies = [
		{'White' : 'Deep Blue', 'Result': '1/2'} 
	]
	dbGames = [
		{'White':'Deep Blue'},
		{'Black':'Deep Blue'}
	]
	tal = [
		{'White':'Tal'},
		{'Black':'Tal'}
	]
	linares = [
		{'Site':'Spain'},
		{'Site':'Linares'}
	]
	reader = pgnReader(gamefile[2])
	games = reader.getGameList(tal)
	for game in games:
		print(f"{game.headers['Site']} {game.headers['White']} v. {game.headers['Black']} {game.headers['Result']}")
	print(len(games))