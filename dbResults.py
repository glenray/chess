import chess
import chess.pgn
import io
import threading
import tkinter as tk
import tkinter.ttk as ttk

from boardPane import boardPane
from dbHelper import DBHelper
import strings as sql

class  dbResults(ttk.Treeview):
	def __init__(self, parent, dbPane):
		ttk.Treeview.__init__(self, parent)
		self.dbPane = dbPane
		self.games = []
		self.setStyle()
		self.bind('<<TreeviewSelect>>', self.printHeadings)
		self.setup()

	def printHeadings(self, e):
		'''
		When user selects a row in the treeview, display the game headers
		in the messages widget.
		'''
		m = self.dbPane.messages
		m.delete("0.1", "end")
		headers = self.games[int(self.selection()[0])].headers
		for h in headers:
			m.insert('end', f'{h}:\t\t{headers[h]}\n')

	def setStyle(self):
		'''
		style the treeview
		''' 
		self.style = ttk.Style()
		self.style.theme_use('clam')
		self.style.configure("Treeview",
			# background='silver',
			# foreground='black',
			rowheight=50,
			fieldbackground='silver',
			font = ('Helvetica', 12)
		)
		self.style.map("Treeview", 
			background=[('selected', 'green')]
		)

		self.style.configure("Treeview.Heading",
			relief = 'raised',
			font = ('Helvetica', 16)
		)

		self.style.configure("Treeview.Cell",
			padding = 10
		)

	def setup(self):
		columns = ("Date", "White", "Black", "Event", "Round", "Result")
		self.config(show='headings', columns=columns)
		# set heading text
		for col in columns:
			sort_method = lambda _col=col: self.treeview_sort_column(self, _col, False)
			self.heading(col, text=col, anchor='w', command=sort_method)
		# bind double click to open game
		self.bind('<Double-1>', self.loadGame)

	def loadGame(self, e):
		item = int(self.selection()[0])
		game = self.games[item]
		self.dbPane.gui.addBoardPane(game)

	def resetTree(self):
		self.games = []
		for row in self.get_children():
			self.delete(row)

	def getResults(self, db, sql, data):
		self.dbPane.messages.delete('1.0', 'end')
		self.dbPane.messages.insert('end', 'Starting Search...')
		self.resetTree()
		threading.Thread(
			target=self.spawnDBTask,
			args = (db, sql, data),
			daemon= True).start()

	def spawnDBTask(self, db, sql, data):
		dbh = DBHelper(db)
		returnedData = dbh.query(sql, data)
		self.dbPane.messages.insert('end', f'Done! Found {len(returnedData)} games.')
		self.after(0, self.populateTree, returnedData)

	def insertTreeRow(self, headers, iid):
		self.insert(
				parent='',
				index = 'end', 
				iid=iid,
				text = '',
				values=(
					headers['Date'],
					headers['White'],
					headers['Black'],
					headers['Event'],
					headers['Round'],
					headers['Result']
				)
			)

	def populateTree(self, data):
		iid = 0
		for row in data:
			game = self.getGameFromStr(row['pgnString'])
			headers = dict(game.headers)
			self.insertTreeRow(headers, iid)
			iid+=1
			self.games.append(game)

	def pgn2Tree(self, filename):
		'''
		Insert games from pgn file into treeview
		'''
		messages = self.dbPane.messages
		if filename:
			messages.insert('end', 'Importing Now...')
			# regading update_idletasks, see 
			# https://www.tcl.tk/man/tcl8.7/TclCmd/update.htm
			self.update_idletasks()
		else:
			messages.insert('end', "Error: no .pgn file selected.")
			return
		iid = 0
		file = open(filename, encoding="Latin-1")
		while True:
			game = chess.pgn.read_game(file)
			if game == None: break
			if game.errors:
				messages.insert('end', f'\n{game.errors}')
				return
			headers = dict(game.headers)
			self.insertTreeRow(headers, iid)
			self.games.append(game)
			iid+=1
			if iid%100 == 0:
				messages.insert('end', f"\nImported {iid} games.")
				messages.see('end')
				self.update_idletasks()
		messages.insert('end', f"\n{iid+1} games displayed.")
		messages.see('end')

	def getGameFromStr(self, pgnString):
		pgn = io.StringIO(pgnString)
		game = chess.pgn.read_game(pgn)
		return game

	def treeview_sort_column(self, tv, col, reverse):
		'''
		Sorting tree view table by click on heading from:
		https://tekrecipes.com/2019/04/20/tkinter-treeview-enable-sorting-upon-clicking-column-headings/
		'''
		l = [(tv.set(k, col), k) for k in tv.get_children('')]
		l.sort(reverse=reverse)

		# rearrange items in sorted positions
		for index, (val, k) in enumerate(l):
			tv.move(k, '', index)

		# reverse sort next time
		tv.heading(col, command=lambda _col=col: self.treeview_sort_column(tv, _col, not reverse))
