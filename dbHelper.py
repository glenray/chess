import sqlite3

class DBHelper():
	def __init__(self, dbPath):
		self.conn = sqlite3.connect(dbPath)
		self.cursor = self.conn.cursor()

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
