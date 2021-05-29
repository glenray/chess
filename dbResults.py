import chess
import chess.pgn
import io
import tkinter as tk
import tkinter.ttk as ttk

from boardPane import boardPane
from dbHelper import DBHelper
import strings as sql

class  dbResults(ttk.Treeview):
	def __init__(self, parent, gui):
		ttk.Treeview.__init__(self, parent)
		self.gui = gui
		self.games = []
		self.setStyle()
		self.setup()

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
		columns = ("Id", "Date", "White", "Black", "Event", "Round", "Result")
		self.config(show='headings', columns=columns)
		self.column("Id", anchor='center')
		# set heading text
		for col in columns:
			sort_method = lambda _col=col: self.treeview_sort_column(self, _col, False)
			self.heading(col, text=col, anchor='w', command=sort_method)
		# center the ID
		self.heading('Id', anchor='center')
		# bind double click to open game
		self.bind('<Double-1>', self.loadGame)

	def loadGame(self, e):
		item = int(self.selection()[0])
		game = self.games[item]
		self.gui.gui.addBoardPane(game)

	def getResults(self, db, sql, data):
		# reset games
		self.games=[]
		for row in self.get_children():
			self.delete(row)
		dbh = DBHelper(db)
		data = dbh.query(sql, data)
		self.populateTree(data)

	def populateTree(self, data):
		iid = 0
		for row in data:
			game = self.getGameFromStr(row['pgnString'])
			headers = dict(game.headers)
			self.insert(
				parent='',
				index = 'end', 
				iid=iid,
				text = '',
				values=(
					row['gameId'],
					headers['Date'],
					headers['White'],
					headers['Black'],
					headers['Event'],
					headers['Round'],
					headers['Result']
				)
			)
			iid+=1
			self.games.append(game)

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
