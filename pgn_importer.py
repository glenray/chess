import chess
import chess.pgn
import io
import logging
import sqlite3
from time import perf_counter

from pgnPillagers.pillageTWIC import pillageTWIC
from pgnPillagers.pgnPillager import pgnPillager
import strings as sql

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
file_handler = logging.FileHandler('logs/import.log')	
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class pgn_importer():
	'''
	Import chess games from pgn file to sqlite database
	@ pgnFile: the path to the pgn file
	@ source: the description of the source of the games for display in the DB
	@ freshStart bool If true, all tables are dropped and the db is vacuumed
	@ dbName str path to the sqlite database file
	'''
	def __init__(self):
		self.sources = {}	
		self.headers = {}

	def setup(self, dbName, freshStart=False):
		self.conn = sqlite3.connect(dbName)
		self.cursor = self.conn.cursor()
		if freshStart:
			self.cursor.executescript(sql.dropAllTables)
		self.verifyDB()		#verify that the tables exist and create them of not
		self.setListData()	#self.sources and self.headers

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

	def verifyDB(self):
		'''Check if the db tables exist, if not, create them'''
		self.cursor.execute(sql.dbExists)
		if self.cursor.fetchone()[0] == 0:
			self.cursor.executescript(sql.createDB)

	def verifySources(self):
		# prevent the same source from being used again.
		if self.source in self.sources.keys():
			logger.info(f"{self.source} is already in the database. Skipping this file.")
			return False
		else:
			idx = self.query(sql.insertSources, [self.source])
			self.sources[self.source] = idx
			return True

	def iterateGameFile(self, pgnFile, source, encoding='latin-1'):
		'''
		Iterate games in PGN file and insert to database
		pgnFile: string (a file path) or bytes
		'''
		self.pgnFile = pgnFile
		self.source = source
		# If the source is already in the DB, skip this file.
		if self.verifySources() == False:
			return
		logger.info(f"Starting import from {self.source}.")
		# pgnFile can be either 1) a string signifying a file path, or 2) a byte object signifying a file that needs to be turned into a string and io object.
		if type(pgnFile) is bytes:
			pgn = io.StringIO(self.pgnFile.decode(encoding))
		elif type(pgnFile) is str:
			pgn = open(pgnFile, encoding=encoding)
		i = 0
		while True:
			if i % 200 == 0:
				print(f'{self.source}: {i} committed')
				self.conn.commit()
			game=chess.pgn.read_game(pgn)
			if game == None: break
			if game.errors:
				logger.error(f'Skipping game {i} due to errors.')
				for error in game.errors:
					logger.error(error)
				logger.error(game)
			else:
				self.insertGame(game)
			i+=1
		self.conn.commit()
		logger.info(f'Saved {i} games from {self.source}.')

	def insertGame(self, game):
		'''
		Insert the game score and source idx to games table
		'''
		data = [str(game)+'\n', self.sources[self.source]]
		idx = self.query(sql.insertGame, data, False)
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

def updateTWIC():
	obj = pgn_importer()
	obj.setup('test.db', True)
	a=pillageTWIC()
	a.setTwicZipPaths()
	newPaths = a.getNewPaths()
	i=1
	for newZip in newPaths:
		if i == 5: break
		zipfile = a.dlFile(a.twicZipPaths[newZip], a.reqHeaders)
		unzipper = a.unzipFile(zipfile)
		for name, pgn in unzipper:
			obj.iterateGameFile(pgn, newZip)
		i+=1

def insertZip():
	obj = pgn_importer()
	obj.setup('databases/openings.db', True)
	a = pgnPillager()
	zipfile = open('C:/Users/Glen/OneDrive/Chess Game Downloads/openings.zip', 'rb')
	zipfileData = zipfile.read()
	zipfile.close()
	unzipper = a.unzipFile(zipfileData)
	for name, pgn in unzipper:
		obj.iterateGameFile(pgn, f"openings - {name}")

def main():
	insertZip()
	# obj = pgn_importer()
	# obj.setup('test.db', True)
	# obj.iterateGameFile('pgn/Annotated_Games.pgn', 'Annotated_Games.pgn')
	# obj.iterateGameFile('pgn/Adams.pgn', 'Adams.pgn')
	# obj.iterateGameFile('pgn/Kasparovs_Games.pgn', 'Kasparovs_Games.pgn')
	# obj.iterateGameFile('pgn/errors.pgn', 'errors.pgn')
	# obj.iterateGameFile('pgn/fenfile.pgn', 'fenfile.pgn')


if __name__ == '__main__':
	main()
