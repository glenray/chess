import threading, random, string
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
from tkinter import scrolledtext
import chess
import chess.engine
import chess.pgn
from PIL import Image, ImageTk
from sqCanvas import sqCanvas
from sqCanvas import strings
from gameScoreVisitor import gameScoreVisitor
from blunderCheck import blunderCheck
from infiniteAnalysis import infiniteAnalysis

import pdb

class boardPane:
	def __init__(self, boardPane):
		self.gui = boardPane
		self.boardSize = 400
		self.lightColorSq = "yellow"
		self.darkColorSq = "brown"
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
		self.pgnFile = 'pgn/blind-warrior vs AnwarQ.pgn'
		# self.pgnFile = 'output.pgn'
		# self.pgnFile = 'pgn/Annotated_Games.pgn'
		# self.pgnFile = 'pgn/testC.pgn'
		file = open(self.pgnFile, encoding='latin-1')
		self.game = chess.pgn.read_game(file)
		# index of node.variations[index] selected in the variations popup
		self.varIdx = None
		# The randomly generated name of any active blundercheck thread
		self.activeBlunderCheck = None

		self.setup()

	def setup(self):
		self.createWidgets()
		# sets the game score text, populates the self.nodes list
		# and sets self.currNode = self.nodes[0], i.e. begin of game
		self.game.accept(gameScoreVisitor(self))
		self.createSquares()
		self.positionSquares()
		self.grabPieceImages()
		self.printCurrentBoard()
		self.printVariations()

	# insert current variations into the variation list box
	def printVariations(self):
		self.variations.delete(0, tk.END)
		for var in self.curNode.variations:
			b=var.parent.board()
			moveNo = b.fullmove_number if b.turn==True else f'{b.fullmove_number}...'
			self.variations.insert(self.nodes.index(var), f"{moveNo} {var.san()}")
			self.variations.selection_set(0)

	# select a variation in the variations listbox using up/down arrows
	def selectVariation(self, e):
		variationsLength = len(self.variations.get(0, tk.END))
		# quit if there are no variations, i.e. the end of a variation
		if variationsLength == 0: return
		curIdx = self.variations.curselection()[0]
		isBottom = curIdx == variationsLength-1
		isTop = curIdx == 0
		# Down arrow
		if e.keycode == 40:
			if isBottom: return
			self.variations.selection_clear(0, tk.END)
			curIdx = curIdx+1
			self.variations.selection_set(curIdx)
		# Up arrow
		elif e.keycode == 38:
			if isTop: return
			self.variations.selection_clear(0, tk.END)
			curIdx = curIdx-1
			self.variations.selection_set(curIdx)

	def setStartPos(self):
		self.board.reset()
		self.printCurrentBoard()

	def printCurrentBoard(self):
		self.board = self.curNode.board()
		self.canvas.delete('piece')
		# piece_map returns a dictionary where 
		# key is the square number and value is a piece object
		# Square numbers start at 0 which is the bottom right square,
		# home to the white light squared rook.
		pm = self.board.piece_map()
		for key in pm:
			self.putImage(key)

	def putImage(self, square):
		sqName = chess.square_name(square)
		coords = self.canvas.coords(sqName)
		piece = self.board.piece_at(square)
		# piece.symbol() returns the letter description for the piece, eg P or p  
		pieceName = piece.symbol()
		i=self.canvas.create_image((coords[0], coords[1]), image=self.tkPieceImg[pieceName], anchor='nw', tag='piece')
		self.pieceImgCache[sqName] = i

	def deletePieceImage(self, sq):
		canvasIdx = self.pieceImgCache[chess.square_name(sq)]
		self.canvas.delete(canvasIdx)
		del self.pieceImgCache[chess.square_name(sq)]

	# populate dictonary containing tk compatible piece images
	def grabPieceImages(self):
		if not self.gui.pieceImg:
			self.gui.loadPieceImages()
		for name in self.gui.pieceImg:
			self.tkPieceImg[name] = self.resizePieceImage(self.gui.pieceImg[name])

	# when board is resized, resize the piece images so as not to lose resolution
	def resizePieceImage(self, im):
		dim = int(round(self.boardSize/8))
		if int(dim)  <= 0: return
		img = im.resize((int(dim), int(dim)), Image.LANCZOS)
		return ImageTk.PhotoImage(image=img)

	# create all tkinter widgets and event bindings
	def createWidgets(self):
		# Fonts and Styling
		# print(font.families())	prints available font families
		buttonFont = font.Font(family="Tahoma", size=16)
		buttonOptions = {"pady":5, "padx":5, "overrelief":'groove', "font":buttonFont}

		self.pWindow = tk.PanedWindow(self.gui.notebook, orient="horizontal", sashwidth=10, sashrelief='raised') 
		self.boardFrame = tk.Frame(self.pWindow, bg="gray75")
		self.canvas = sqCanvas(self.boardFrame, highlightthickness=0)
		self.controlFrame = tk.Frame(self.pWindow)
		self.analysisFrame = tk.Frame(self.controlFrame, bg="blue")
		# exportselection prevents selecting from the list box in one board pane from deselecting the others. https://github.com/PySimpleGUI/PySimpleGUI/issues/1158
		self.variations = tk.Listbox(self.analysisFrame, width=20, exportselection=False)
		self.analysis = tk.Text(self.analysisFrame, height=10)
		self.gameScore = tk.scrolledtext.ScrolledText(self.controlFrame, width=10, font=("Tahoma", 14))
		
		self.pWindow.bind('<Right>', lambda e: self.move(e, 'forward'))
		self.pWindow.bind('<Left>', lambda e: self.move(e, 'backward'))
		self.pWindow.bind('<Control-r>', self.reverseBoard)
		self.pWindow.bind('<Control-e>', self.toggleEngine)
		# launch a blunder check class instance
		self.pWindow.bind('<Control-b>', lambda e: blunderCheck(self))

		self.gui.notebook.add(self.pWindow, text="1 Board")

		# Frame container for board canvas
		self.boardFrame.bind("<Configure>", self.resizeBoard)

		# Board Canvas
		self.canvas.pack()

		# Analysis Frame
		self.analysisFrame.pack(anchor='n', fill='x')

		# variation list box
		self.variations.pack(side=tk.LEFT)
		self.gui.root.bind("<Down>", self.selectVariation)
		self.gui.root.bind("<Up>", self.selectVariation)

		# analysis text
		self.analysis.config(wrap=tk.WORD)
		self.analysis.pack(anchor='n', expand=True, fill='both')

		# game score
		self.gameScore.config(wrap=tk.WORD, padx=10, pady=10, state='disabled')
		self.gameScore.pack(anchor='n', expand=True, fill='both')
		self.gameScore.tag_bind('move', '<Button-1>', self.gameScoreClick)
		self.gameScore.tag_bind('move', '<Enter>', lambda e: self.cursorMove('enter'))
		self.gameScore.tag_bind('move', '<Leave>', lambda e: self.cursorMove('leave'))
		self.gameScore.tag_configure('curMove', foreground="white", background="red")

		# Add widgets to paned window
		self.pWindow.add(self.boardFrame)
		self.pWindow.add(self.controlFrame)

	# click on move in gamescore updates board to that move
	def gameScoreClick(self, e):
		moveIndices = []
		# get text indicies of click location
		location = f"@{e.x},{e.y}+1 chars"
		# find the indices of the clicked move tag
		moveTagRange = self.gameScore.tag_prevrange('move', location)
		# tuple of begin and end indices for all move tags
		ranges = self.gameScore.tag_ranges('move')
		# convert range to pairs of tuples so they can be compared with moveTagRange
		for x in range(0, len(ranges), 2):
			moveIndices.append((str(ranges[x]), str(ranges[x+1])))
		# set currentNode to the clicked move
		# we add 1 because nodes[0] is the opening position which 
		# is not represented as a move on the game score
		self.curNode = self.nodes[moveIndices.index(moveTagRange)+1]
		self.printCurrentBoard()
		self.updateGameScore()
		if self.activeEngine != None:
			infiniteAnalysis(self)

	'''
	Move a piece from on sq to another
	@ fromSq obj chess.square object with piece on it
	@ toSq obj chess.square object to relocate piece
	'''
	def moveCanvasPiece(self, fromSq, toSq):
		csn, cc = chess.square_name, self.canvas.coords
		fromSqName, toSqName = csn(fromSq), csn(toSq)
		fromSqCoords, toSqCoords = cc(fromSqName), cc(toSqName)
		obj = self.pieceImgCache[fromSqName]
		# find the distance between the from and to coordinates
		dx = toSqCoords[0]-fromSqCoords[0]
		dy = toSqCoords[1]-fromSqCoords[1]
		self.canvas.move(obj, dx, dy)
		# update image cache to add piece at toSq and remove piece at fromSq
		self.pieceImgCache[toSqName] = self.pieceImgCache[fromSqName]
		self.pieceImgCache.pop(fromSqName)

	def testMoveProperties(self, move):
		return (
			self.board.is_castling(move),
			self.board.is_kingside_castling(move),
			self.board.is_capture(move),
			self.board.is_en_passant(move),
			move.promotion		
		)

	def movePiece(self, move, direction):
		ts,fs = move.to_square, move.from_square
		sqs = (fs, ts) if direction == 'forward' else (ts, fs)
		self.moveCanvasPiece(*sqs)

	def promotion(self, move, direction):
		targetSq = move.to_square if direction == 'forward' else move.from_square
		self.deletePieceImage(targetSq)
		self.putImage(targetSq)

	def capturing(self, move, direction):
		ts,fs = move.to_square, move.from_square
		if direction == 'forward':
			self.deletePieceImage(ts)
			self.moveCanvasPiece(fs, ts)
		else:
			self.moveCanvasPiece(ts, fs)
			self.putImage(ts)

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
		self.moveCanvasPiece(kingFromSq, kingToSq)	# move king
		self.moveCanvasPiece(rookFromSq, rookToSq)	# move rook
	
	# Update GUI for en passant move
	# @ move obj move object
	# @ direction str either 'forward' or 'backward', 
	# 	depending on direction through move stack
	def enPassant(self, move, direction):
		ts,fs = move.to_square, move.from_square
		# forward: delete the taken pawn
		# backward: replace the taken pawn
		squares,func = ((fs, ts), self.deletePieceImage) if direction == 'forward' else ((ts, fs), self.putImage)
		# move capturing piece
		self.moveCanvasPiece(*squares)
		# delete captured pawn or return captured pawn to original square
		file = chess.square_file(ts)
		rank = chess.square_rank(fs)
		func(chess.square(file, rank))

	# create 64 rectangles to be sized and positioned later
	def createSquares(self):
		file = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
		rank = ('8', '7', '6', '5', '4', '3', '2', '1')
		sqColor = (self.lightColorSq, self.darkColorSq)
		for row in range(8):
			for col in range(8):
				sqName = str(file[col])+rank[row]
				sqId = self.canvas.create_rectangle(
					1,1,10,10, 
					fill=sqColor[(col+row)%2],
					tag=('square', sqName)
				)
				self.squares.append(sqId)

	# position squares in canvas based on current square size
	# can build board with either color on bottom depending on
	# value of self.whiteSouth
	def positionSquares(self):
		sqSize = self.boardSize/8
		sqIds = 0
		# set variables based on what side is on bottom of board
		if self.whiteSouth == True:
			xpos = ypos = xreset = 0
			direction = sqSize
		else:
			xpos = ypos = xreset = self.boardSize-sqSize
			direction = -sqSize
		for col in range(8):
			for row in range(8):
				self.canvas.coords(self.squares[sqIds], xpos, ypos, xpos+sqSize, ypos+sqSize)
				xpos += direction
				sqIds+=1
			ypos += direction
			xpos = xreset

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
			(isCastling, isKingSideCastling, isCaptureMove, isEnPassant,
					isPromotion) = self.testMoveProperties(move)
			self.board = self.curNode.board()
		else:
			if self.curNode == self.curNode.game(): return
			move = self.curNode.move
			self.board = self.curNode.parent.board()
			(isCastling, isKingSideCastling, isCaptureMove, isEnPassant,
				isPromotion) = self.testMoveProperties(move)
			self.curNode=self.curNode.parent

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

		self.updateGameScore()
		self.printVariations()
		if self.activeEngine != None:
			infiniteAnalysis(self)

	# emphasize current move in game score
	def updateGameScore(self):
		gs = self.gameScore
		nodeIdx = self.nodes.index(self.curNode)
		ranges = gs.tag_ranges('move')
		if gs.tag_ranges('curMove'):
			gs.tag_remove('curMove', 'curMove.first', 'curMove.last')
		if nodeIdx: 
			gs.tag_add('curMove', ranges[nodeIdx*2-2], ranges[nodeIdx*2-1])
		# keep the current move visible in the game score
		if gs.tag_ranges('curMove'):
			gs.see('curMove.first')

	# bound to change in board frame container size, redraw board based on width of container
	def resizeBoard(self, e):
		self.boardSize = min(e.height, e.width)
		self.positionSquares()
		self.grabPieceImages()
		self.printCurrentBoard()

	# toggles white on north or south side of the board
	# bound to Reverse Button
	def reverseBoard(self, e=None):
		self.whiteSouth = not self.whiteSouth
		self.positionSquares()
		self.printCurrentBoard()

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

if __name__ == '__main__':
	g=GUI()
	g.setup()
