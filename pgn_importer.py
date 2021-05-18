import chess
import chess.pgn
import io
import logging
import sqlite3
from time import perf_counter
import strings as sql

class pgn_importer():
	'''
	Import chess games from pgn file to sqlite database
	@ pgnFile: the path to the pgn file
	@ source: the description of the source of the games for display in the DB
	@ freshStart bool If true, all tables are dropped and the db is vacuumed
	@ dbName str path to the sqlite database file
	'''
	def __init__(self, pgnFile, source, freshStart=False, dbName='chessLib.db'):
		logging.basicConfig(filename='Error.log', level=logging.DEBUG)
		logging.info("Application started.")
		self.source = source
		self.pgnFile = pgnFile
		self.conn = sqlite3.connect(dbName)
		self.cursor = self.conn.cursor()
		if freshStart:
			self.cursor.executescript(sql.dropAllTables)
		self.verifyDB()		#verify that the tables exist and create them of not
		self.sources = {}	
		self.headers = {}
		self.zeroMoveGames = []
		self.setListData()	#populate above dicts from DB data

	def setListData(self):
		'''
		Set self.sources with the sources already in the DB
		Set self.headers with the header types already in the DB
		If the source does not exist in the DB, insert it
		'''
		headers = self.query(sql.getHeaders)
		sources = self.query(sql.getSources)
		self.sources = {v:k for k, v in dict(sources).items()}
		self.headers = {v:k for k, v in dict(headers).items()}
		# prevent the same source from being used again.
		assert not self.source in self.sources.keys(), f"{self.source} is already in the database."
		idx = self.query(sql.insertSources, [self.source])
		self.sources[self.source] = idx

	def verifyDB(self):
		'''Check if the db tables exist, if not, create them'''
		self.cursor.execute(sql.dbExists)
		if self.cursor.fetchone()[0] == 0:
			self.cursor.executescript(sql.createDB)

	def testGameFile(self, encoding='latin-1'):
		'''Iterate games in PGN file and break on errors'''
		# pgn = self.pgnFile
		pgn = io.StringIO(self.pgnFile.decode(encoding))
		# pgn = open(self.pgnFile, encoding=encoding)
		i, tStart = 1, perf_counter()
		while True:
			game = chess.pgn.read_game(pgn)
			breakpoint()
			print(game)
			if not game: break
			if game.errors:
				breakpoint()
			if i % 1000 == 0:
				print(i)
			i+=1

	def iterateGameFile(self, encoding='latin-1'):
		'''Iterate games in PGN file and insert to database'''
		pgn, i, tStart = open(self.pgnFile, encoding=encoding), 1, perf_counter()
		while True:
			# commit every 1000 games to save time
			if i % 1000 == 0: 
				self.conn.commit()
				message = f'{i} games added in {perf_counter()-tStart} seconds'
				print(message)
				tStart = perf_counter()
			game=chess.pgn.read_game(pgn)
			if not game: break
			# log errors and skip those games
			if game.errors:
				logging.info(f"Skipping this game where errors were found.\n{str(game)}")
				for error in game.errors:
					logging.info(str(error)+'\n')
				continue
			self.insertGame(game)
			i+=1
		# commit any remaining games.
		self.conn.commit()
		logging.info(f"These games have zero moves:")
		logging.info(self.zeroMoveGames)

	def insertGame(self, game):
		'''
		Insert the game score and source idx to games table
		'''
		data = [str(game)+'\n', self.sources[self.source]]
		idx = self.query(sql.insertGame, data, False)
		# log zero move games
		if len(game.variations) == 0:
			self.zeroMoveGames.append(idx)
			logging.info(f'Game {idx} has zero moves.')
		self.insertHeaders(game, idx)

	def insertHeaders(self, game, gameIdx):
		'''
		Insert all game headers as a batch to related table
		'''
		headerData = []
		for header in game.headers:
			# add new headers to database
			if not header in self.headers.keys():
				headidx = self.query(sql.insertHeaders, [header])
				self.headers[header] = headidx
			headerData.append((gameIdx, self.headers[header], game.headers[header]))
		self.cursor.executemany(sql.insertRelatedHeaders, headerData)

	def query(self, sql, data='', doCommit=True, rf=True):
		'''
		Helper method handling DB queries and returning results
		@ sql string a sql query string
		@ data list data for query string placeholders
		@ doCommit bool whether to commit each query after execution
		@ rf bool whether to return result as sqlite3.Row factory. 
		If result is row factory 'rows', then
			len(rows) = number of returned rows, 
			rows[0].keys() = a list of row keys, i.e. table column names,
			list(rows[0]) = list or row values, 
			rows[0][rows[0].keys()[0]] = the value of row[key]
			See https://docs.python.org/3/library/sqlite3.html#row-objects
		If rowFactory = False, a simple tuple is returned
		'''
		self.cursor.row_factory = sqlite3.Row if rf==True else None
		commands = ['SELECT', 'DELETE', 'INSERT', 'CREATE', 'VACUUM']
		firstWord = sql.split(' ')[0].upper().strip()
		assert firstWord in commands, f" Method pgn2sql.query() was expecting an sql statement starting with SELECT, DELETE or INSERT. Instead, it got {sql}."
		result = self.cursor.execute(sql, data)
		if doCommit == True: self.conn.commit()
		if firstWord == 'SELECT':
			retObj = result.fetchall()
			return retObj
		elif firstWord == 'INSERT':
			return self.cursor.lastrowid

def main():
	obj=pgn_importer('pgn/leftout.pgn', 'Rebel Millionbase', freshStart=True, dbName='test.db')
	breakpoint()
	# obj.iterateGameFile()
	# obj.testGameFile()

if __name__ == '__main__':
	main()
