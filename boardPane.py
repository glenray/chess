import threading, random, string
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
from tkinter import filedialog
import chess
import chess.engine
import chess.pgn
from variations import Variations
from analysis import Analysis_text, infiniteAnalysis
from sqCanvas import sqCanvas
from gamescore import Gamescore
from gameScoreVisitor import gameScoreVisitor
from blunderCheck import blunderCheck

class boardPane(tk.PanedWindow):
	def __init__(self, parent, pgnFile=None):
		tk.PanedWindow.__init__(self, parent.notebook)
		self.config(orient="horizontal", sashwidth=10, sashrelief='raised')
		self.gui = parent
		# randomly generated name of active engine thread
		self.activeEngine = None
		# list of nodes in mainline and all variations
		# populated by gameScoreVisitor class
		self.nodes = []
		self.curNode = None
		# index of node.variations[index] selected in the variations popup
		self.varIdx = None
		# The randomly generated name of any active blundercheck thread
		self.activeBlunderCheck = None
		self.pgnFile = pgnFile
		if type(self.pgnFile) is str:
			file = open(self.pgnFile)
			self.game = chess.pgn.read_game(file)
		elif isinstance(self.pgnFile, chess.pgn.Game):
			self.game = self.pgnFile
		self.setup()

	def setup(self):
		self.createWidgets()
		# sets the game score text, populates the self.nodes list
		# and sets self.currNode = self.nodes[0], i.e. begin of game
		self.game.accept(gameScoreVisitor(self))
		self.canvas.createSquares()
		self.canvas.positionSquares()
		self.canvas.resizePieceImages()
		self.canvas.printCurrentBoard()
		self.variations.printVariations()

	def loadGameFile(self, e):
		self.pgnFile = filedialog.askopenfilename()
		file = open(self.pgnFile)
		self.game = chess.pgn.read_game(file)
		self.game.accept(gameScoreVisitor(self))
		self.canvas.printCurrentBoard()
		self.variations.printVariations()

	def createWidgets(self):
		'''create all tkinter widgets and event bindings'''
		# Fonts and Styling
		# print(font.families())	prints available font families
		buttonFont = font.Font(family="Tahoma", size=16)
		buttonOptions = {"pady":5, "padx":5, "overrelief":'groove', "font":buttonFont}
		# Create child widgets
		self.boardFrame = tk.Frame(self, bg="gray75")
		self.controlFrame = tk.Frame(self)
		self.analysisFrame = tk.Frame(self.controlFrame, bg="blue")
		self.canvas = sqCanvas(self.boardFrame, boardPane=self)
		self.variations = Variations(self.analysisFrame, boardPane=self)
		self.analysis = Analysis_text(self.analysisFrame, boardPane=self)
		self.gameScore = Gamescore(self.controlFrame, boardPane=self)
		# Events 
		self.bind('<Right>', lambda e: self.move(e, 'forward'))
		self.bind('<Left>', lambda e: self.move(e, 'backward'))
		self.bind('<Alt-Left>', lambda e: self.jumpTo(e, 'upVar'))
		self.bind('<Home>', lambda e: self.jumpTo(e, 'home'))
		self.bind('<End>', lambda e: self.jumpTo(e, 'endVar'))
		self.bind('<Next>', lambda e: self.jumpTo(e, 'pgDown'))
		self.bind('<Prior>', lambda e: self.jumpTo(e, 'pgUp'))
		self.bind('<Control-r>', self.canvas.reverseBoard)
		self.bind('<Control-e>', self.toggleEngine)
		self.bind('<Control-b>', lambda e: blunderCheck(self))
		self.bind("<Down>", self.variations.selectVariation)
		self.bind("<Up>", self.variations.selectVariation)
		self.bind("<Control-o>", self.loadGameFile)
		self.bind("<Control-w>", self.removeTab)
		self.bind("<Control-s>", lambda e: self.savePGN(self.game, self.nodes))
		self.bind("<F12>", self.redrawGS)
		self.bind("<F11>", self.eraseGS)

		self.boardFrame.bind("<Configure>", self.canvas.resizeBoard)
		# Insert pane into the parent notebook
		self.gui.notebook.insert('end', self, text="1 Board")
		self.gui.notebook.select(self.gui.notebook.index('end')-1)
		# Pack
		self.analysisFrame.pack(anchor='n', fill='x')
		self.variations.pack(side=tk.LEFT)
		self.gameScore.pack(anchor='n', expand=True, fill='both')
		self.analysis.pack(anchor='n', expand=True, fill='both')
		self.canvas.pack()
		# Add frames to paned window
		self.add(self.boardFrame, stretch='always')
		self.add(self.controlFrame, stretch='always')

	def jumpTo(self, e, location):
		'''
		Jump to various nodes in the game
		'''
		'''jump to the parent node of the start of this variation 
		if not in the mainline'''
		if location == 'upVar':
			node = self.curNode
			while node.parent:
				if node.starts_variation():
					self.curNode = node.parent
					break
				node = node.parent
		# jump to the opening position
		elif location == 'home':
			self.curNode = self.nodes[0]
			self.gameScore.see('1.0')
		# jump to the end of the current variation
		elif location == 'endVar':
			self.curNode = self.curNode.end()
		# jump down 5 moves
		elif location == 'pgDown':
			for x in range(10):
				if self.curNode.next():
					self.curNode = self.curNode.next()
				else:
					break
		elif location == 'pgUp':
			for x in range(10):
				if self.curNode.parent:
					self.curNode = self.curNode.parent
				else:
					break
		else:
			return False
		self._updatePane()

	def eraseGS(self, e):
		self.gameScore.config(state='normal')
		self.gameScore.delete('1.0', 'end')

	def _updatePane(self):
		'''
		Helper function to use after curNode has been updated.
		'''
		self.canvas.printCurrentBoard()
		self.variations.printVariations()
		self.gameScore.updateGameScore()
		if self.activeEngine != None:
			infiniteAnalysis(self)

	def removeTab(self, e):
		'''Ctrl-w removes the tab; sets focuses on new current tab'''
		nb = self.gui.notebook
		nb.forget('current')
		tabs = nb.tabs()
		self.destroy()
		# if there are other tabs, set focus to the one active
		if tabs: 
			activeTabIdx = nb.index('current')
			# the name of the panedwindow in the active tab
			panedWindowName = tabs[activeTabIdx]
			# put focus on that paned window
			self.gui.root.nametowidget(panedWindowName).focus()

	def move(self, e, direction):
		'''Updates GUI after moving though game nodes both directions
		bound to left and right arrow keys at root'''
		if direction == 'forward':
			if self.curNode.is_end(): return
			# gets variation index from variation list box
			varIdx = self.variations.curselection()[0]
			self.curNode = self.curNode.variations[varIdx]
			self.canvas.makeMoveOnCanvas(self.curNode.move, direction)
		else:
			if self.curNode == self.curNode.game(): return
			self.canvas.makeMoveOnCanvas(self.curNode.move, direction)
			self.curNode=self.curNode.parent

		self.gameScore.updateGameScore()
		self.variations.printVariations()
		if self.activeEngine != None:
			infiniteAnalysis(self)

	def toggleEngine(self, e):
		# toggles an engine to analyze the current board position
		if self.activeEngine == None:
			infiniteAnalysis(self)
		else:
			self.activeEngine = None

	def savePGN(self, game, nodes):
		file = open("pgn/saved.pgn", 'w+')
		print(game, file=file, end="\n\n")
		print(nodes, file=file)
		file.close()

	def redrawGS(self, e=None):
		self.game.accept(gameScoreVisitor(self))
		self.canvas.printCurrentBoard()
		self.variations.printVariations()

def main():
	from gui import GUI
	GUI()

if __name__ == '__main__':
	main()