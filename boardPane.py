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

class boardPane:
	def __init__(self, gui, pgnFile=None):
		self.gui = gui
		self.boardSize = 400
		self.settings = {
			'lightColorSq' : "yellow",
			'darkColorSq' : "brown",
			'hlSqColor'	: 'black'
		}
		self.squares = []		# list of canvas ids for all canvas rectangles
		self.whiteSouth = True	# True: white pieces on south side of board; False reverse
		# a dictonary of tkImage objects for each piece resized for current board
		self.tkPieceImg = {}
		# a dictionary where key is square name and value is
		# the canvas index corresponding to the piece on the square
		self.pieceImgCache = {}
		# randomly generated name of active engine thread
		self.activeEngine = None
		# list of nodes in mainline and all variations
		# populated by gameScoreVisitor class
		self.nodes = []
		self.curNode = None
		self.pgnFile = pgnFile
		file = open(self.pgnFile)
		self.game = chess.pgn.read_game(file)
		# index of node.variations[index] selected in the variations popup
		self.varIdx = None
		# The randomly generated name of any active blundercheck thread
		self.activeBlunderCheck = None
		# If a human move is in progress
		# a list of tuples (x, y, z) where
		# x: the canvas square id of the from piece with valid move
		# y: the canvas square id of the to square where piece can go
		# z: chess.move from x to y
		self.MiP = []

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

	# create all tkinter widgets and event bindings
	def createWidgets(self):
		# Fonts and Styling
		# print(font.families())	prints available font families
		buttonFont = font.Font(family="Tahoma", size=16)
		buttonOptions = {"pady":5, "padx":5, "overrelief":'groove', "font":buttonFont}
		# Create all Widgets
		self.pWindow = tk.PanedWindow(self.gui.notebook, orient="horizontal", sashwidth=10, sashrelief='raised') 
		self.boardFrame = tk.Frame(self.pWindow, bg="gray75")
		self.canvas = sqCanvas(self.boardFrame, boardPane=self)
		self.controlFrame = tk.Frame(self.pWindow)
		self.analysisFrame = tk.Frame(self.controlFrame, bg="blue")
		self.variations = Variations(self.analysisFrame, boardPane=self)
		self.analysis = Analysis_text(self.analysisFrame, boardPane=self)
		self.gameScore = Gamescore(self.controlFrame, boardPane=self)
		# Events 
		self.pWindow.bind('<Right>', lambda e: self.move(e, 'forward'))
		self.pWindow.bind('<Left>', lambda e: self.move(e, 'backward'))
		self.pWindow.bind('<Control-r>', self.canvas.reverseBoard)
		self.pWindow.bind('<Control-e>', self.toggleEngine)
		self.pWindow.bind('<Control-b>', lambda e: blunderCheck(self))
		self.pWindow.bind("<Down>", self.variations.selectVariation)
		self.pWindow.bind("<Up>", self.variations.selectVariation)
		self.pWindow.bind("<Control-o>", self.loadGameFile)
		self.pWindow.bind("<Control-w>", self.removeTab)
		self.boardFrame.bind("<Configure>", self.canvas.resizeBoard)
		# Insert pane into the parent notebook
		self.gui.notebook.insert('end', self.pWindow, text="1 Board")
		self.gui.notebook.select(self.gui.notebook.index('end')-1)
		# Pack
		self.analysisFrame.pack(anchor='n', fill='x')
		self.variations.pack(side=tk.LEFT)
		self.gameScore.pack(anchor='n', expand=True, fill='both')
		self.analysis.pack(anchor='n', expand=True, fill='both')
		# Add widgets to paned window
		self.pWindow.add(self.boardFrame, stretch='always')
		self.pWindow.add(self.controlFrame, stretch='always')

		self.gui.root.bind("<Control-s>", lambda e: self.gui.savePGN(self.game, self.nodes))

	def makeMoveOnCanvas(self, move, direction):
		# Internally, this move has been made already, so we need to look at the parent
		# node to evaluate what kind of move it was.
		board = self.curNode.parent.board()
		(isCastling, isKingSideCastling, isCaptureMove, isEnPassant, isPromotion) = (board.is_castling(move),
			board.is_kingside_castling(move),
			board.is_capture(move),
			board.is_en_passant(move),
			move.promotion)

		if isCaptureMove:
			if isEnPassant:
				self.enPassant(move, direction)
			else:
				self.capturing(move, direction)
		elif isCastling:
			self.castling(move, direction, isKingSideCastling)
		else:
			self.movePiece(move, direction)	# this is a normal move
		if isPromotion:
			self.promotion(move, direction) # promotion can either be by capture or normal move

	def makeHumanMove(self, move):
		self.gameScore.humanMovetoGameScore(move)
		self.makeMoveOnCanvas(move, 'forward')	
		self.variations.printVariations()
		# self.board=self.curNode.board()
		if self.activeEngine != None:
			infiniteAnalysis(self)

	# Ctrl-w removes the tab; sets focuses on new current tab
	def removeTab(self, e):
		nb = self.gui.notebook
		nb.forget('current')
		tabs = nb.tabs()
		self.pWindow.destroy()
		# if there are other tabs, set focus to the one active
		if tabs: 
			activeTabIdx = nb.index('current')
			# the name of the panedwindow in the active tab
			panedWindowName = tabs[activeTabIdx]
			# put focus on that paned window
			self.gui.root.nametowidget(panedWindowName).focus()

	def movePiece(self, move, direction):
		ts,fs = move.to_square, move.from_square
		sqs = (fs, ts) if direction == 'forward' else (ts, fs)
		self.canvas.moveCanvasPiece(*sqs)

	''' Promote a piece on the back rank
	Forward: the pawn has already been moved to the queening square
	and any captured piece has been removed.
	On the self.curNode.board(), We need to 
	1. delete the pawn on the queening square
	2. put the appropriate piece in it's place

	Backward: the promoted piece has already been moved back to the pawn's
	pre-promotion position, and any taken piece returned to the queening square. 
	On self.curNode.parent.board(), we need to
	1. remove the promoted piece graphic on the 7th rank
	2. replace it with a pawn
	'''
	def promotion(self, move, direction):
		targetSq = move.to_square if direction == 'forward' else move.from_square
		# if direction == 'forward' else move.from_square
		self.canvas.deletePieceImage(targetSq)
		self.canvas.putImage(targetSq, direction)

	def capturing(self, move, direction):
		ts,fs = move.to_square, move.from_square
		if direction == 'forward':
			self.canvas.deletePieceImage(ts)
			self.canvas.moveCanvasPiece(fs, ts)
		else:
			self.canvas.moveCanvasPiece(ts, fs)
			self.canvas.putImage(ts, direction)

	def castling(self, move, direction, isKingSideCastling):
		# locate rook rank and file (0 based)
		fromFile, toFile  = (5,7) if isKingSideCastling else (3,0)
		rank = chess.square_rank(move.to_square)
		
		if direction == 'forward':
			kingFromSq, kingToSq = move.from_square, move.to_square
			rookFromSq, rookToSq = chess.square(toFile, rank), chess.square(fromFile, rank)
		else:
			kingFromSq, kingToSq = move.to_square, move.from_square
			rookFromSq, rookToSq = chess.square(fromFile, rank), chess.square(toFile, rank)
		self.canvas.moveCanvasPiece(kingFromSq, kingToSq)	# move king
		self.canvas.moveCanvasPiece(rookFromSq, rookToSq)	# move rook
	
	# Update GUI for en passant move
	# @ move obj move object
	# @ direction str either 'forward' or 'backward', 
	# 	depending on direction through move stack
	def enPassant(self, move, direction):
		ts,fs = move.to_square, move.from_square
		if direction == 'forward':
			squares = (fs, ts)
			self.canvas.moveCanvasPiece(*squares)
			file = chess.square_file(ts)
			rank = chess.square_rank(fs)
			self.canvas.deletePieceImage(chess.square(file,rank))
		else:
			squares = (ts, fs)
			self.canvas.moveCanvasPiece(*squares)
			file = chess.square_file(ts)
			rank = chess.square_rank(fs)
			self.canvas.putImage(chess.square(file, rank), direction)

	''' Event bindings '''
	# Updates GUI after moving though game nodes both directions
	# bound to left and right arrow keys at root
	def move(self, e, direction):
		if direction == 'forward':
			if self.curNode.is_end(): return
			# gets variation index from variation list box
			varIdx = self.variations.curselection()[0]
			self.curNode = self.curNode.variations[varIdx]
			move = self.curNode.move
			self.makeMoveOnCanvas(move, direction)
		else:
			if self.curNode == self.curNode.game(): return
			move = self.curNode.move
			self.makeMoveOnCanvas(move, direction)
			self.curNode=self.curNode.parent

		self.gameScore.updateGameScore()
		self.variations.printVariations()
		if self.activeEngine != None:
			infiniteAnalysis(self)

	# changes the cursor when hovering over a move in the game score
	def cursorMove(self, status):
		if status == 'leave':
			self.gameScore.config(cursor='')
		elif status == 'enter':
			self.gameScore.config(cursor='hand2')

	# toggles an engine to analyze the current board position
	def toggleEngine(self, e):
		if self.activeEngine == None:
			infiniteAnalysis(self)
		else:
			self.activeEngine = None

def main():
	from gui import GUI
	GUI()

if __name__ == '__main__':
	main()