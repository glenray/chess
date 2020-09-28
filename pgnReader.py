import chess.pgn

class pgnReader:
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
		pgn = open('pgn/Kasparovs_Games.pgn')
		while True:
			offset = pgn.tell()
			headers = chess.pgn.read_headers(pgn)
			if headers == None: break
			for search in searchParams:
				if self.isSubSet(headers, search):
					offsets.append(offset)
				else:
					continue
		return offsets			

	def getOneGame(self, offset):
		pgn = open('pgn/Kasparovs_Games.pgn')
		pgn.seek(offset)
		return chess.pgn.read_game(pgn)

	# Are all elements of subset in set?
	def isSubSet(self, set, subset):
		return all(set.get(key, None) == val for key, val in subset.items())

if __name__ == '__main__':
	search = [
		{'White' : 'Deep Blue', 'Result': '1-0'}, 
		{'Black' : 'Deep Blue', 'Result': '0-1'}
	]

	reader = pgnReader()
	offsets = reader.searchGames(search)
	for offset in offsets:
		game = reader.getOneGame(offset)
		print(game)
	