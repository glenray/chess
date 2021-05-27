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
		self['columns'] = ("Id", "White", "Black", "Event", "Round", "Result")
		self.column("#0", width=0, stretch='no')
		self.column("Id", anchor='center', width=50, minwidth=25)
		self.column("White", anchor='w', width=120, minwidth=25)
		self.column("Black", anchor='w', width=120, minwidth=25)
		self.column("Event", anchor='w', width=300, minwidth=25)
		self.column("Round", anchor='w')
		self.column("Result", anchor='w')

		self.heading('#0', text='')
		self.heading('Id', text='Id', anchor='center')
		self.heading('White', text='White', anchor='w')
		self.heading('Black', text='Black', anchor='w')
		self.heading('Event', text='Event', anchor='w')
		self.heading('Round', text='Round', anchor='w')
		self.heading('Result', text='Round', anchor='w')

		self.bind('<Double-1>', self.loadGame)

	def loadGame(self, e):
		item = int(self.selection()[0])
		game = self.games[item]
		self.gui.gui.addBoardPane(game)

	def getData(self, p1, p2):
		# reset games
		self.games=[]
		for row in self.get_children():
		    self.delete(row)
		dbh = DBHelper('databases/chessLib.db')
		params = {'p1' : f'{p1}*', 'p2' : f'{p2}*'}
		data = dbh.query(sql.getGamesBtwPlayers, params)
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
