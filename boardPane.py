import threading, random, string
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
from tkinter import scrolledtext
from tkinter import filedialog
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
		self.createSquares()
		self.positionSquares()
		self.grabPieceImages()
		self.printCurrentBoard()
		self.printVariations()

	# insert current variations into the variation list box
	def printVariations(self):
		# pdb.set_trace()
		self.variations.delete(0, tk.END)
		for var in self.curNode.variations:
			b=var.parent.board()
			moveNo = b.fullmove_number if b.turn==True else f'{b.fullmove_number}...'
			# self.variations.insert(self.nodes.index(var), f"{moveNo} {var.san()}")
			self.variations.insert(self.curNode.variations.index(var), f"{moveNo} {var.san()}")
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

	def printCurrentBoard(self):
		board = self.curNode.board()
		self.canvas.delete('piece')
		# piece_map returns a dictionary where 
		# key is the square number and value is a piece object
		# Square numbers start at 0 which is the bottom right square,
		# home to the white light squared rook.
		pm = board.piece_map()
		for key in pm:
			self.putImage(key)

	# Put a new piece on the board
	# In a regular game, this may be because a piece has been promoted or 
	# a backward move puts a taken piece back on the board
	# A board is created to represent the current state of the board that 
	# needs to be mimiced in the GUI. In the event of a backward move, 
	# that the the parent of the current node.
	def putImage(self, square, direction='forward'):
		board = self.curNode.board() if direction == 'forward' else self.curNode.parent.board()
		sqName = chess.square_name(square)
		coords = self.canvas.coords(sqName)
		piece = board.piece_at(square) 
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

	def loadGameFile(self, e):
		self.pgnFile = filedialog.askopenfilename()
		file = open(self.pgnFile)
		self.game = chess.pgn.read_game(file)
		self.game.accept(gameScoreVisitor(self))
		self.printCurrentBoard()
		self.printVariations()

	# create all tkinter widgets and event bindings
	def createWidgets(self):
		# Fonts and Styling
		# print(font.families())	prints available font families
		buttonFont = font.Font(family="Tahoma", size=16)
		buttonOptions = {"pady":5, "padx":5, "overrelief":'groove', "font":buttonFont}

		self.pWindow = tk.PanedWindow(self.gui.notebook, orient="horizontal", sashwidth=10, sashrelief='raised') 
		self.boardFrame = tk.Frame(self.pWindow, bg="gray75")
		cWidth = int(self.gui.screenW/2)
		self.canvas = sqCanvas(self.boardFrame, highlightthickness=0, width=cWidth)
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
		self.pWindow.bind("<Down>", self.selectVariation)
		self.pWindow.bind("<Up>", self.selectVariation)
		self.pWindow.bind("<Control-o>", self.loadGameFile)
		self.pWindow.bind("<Control-w>", self.removeTab)

		self.gui.notebook.insert('end', self.pWindow, text="1 Board")
		self.gui.notebook.select(self.gui.notebook.index('end')-1)

		# Frame container for board canvas
		self.boardFrame.bind("<Configure>", self.resizeBoard)

		# Board Canvas
		self.canvas.bind("<Button-1>", self.canvasTouch)
		self.canvas.pack()

		# Analysis Frame
		self.analysisFrame.pack(anchor='n', fill='x')

		# variation list box
		self.variations.bind('<Right>', lambda e: self.move(e, 'forward'))
		self.variations.bind('<Left>', lambda e: self.move(e, 'backward'))
		self.variations.pack(side=tk.LEFT)

		# analysis text
		self.analysis.config(wrap=tk.WORD)
		self.analysis.bind('<FocusIn>', lambda e: self.pWindow.focus())
		self.analysis.bind("<Down>", self.selectVariation)
		self.analysis.bind("<Up>", self.selectVariation)
		self.analysis.pack(anchor='n', expand=True, fill='both')

		# game score
		self.gameScore.config(wrap=tk.WORD, padx=10, pady=10, state='disabled')
		self.gameScore.pack(anchor='n', expand=True, fill='both')
		self.gameScore.tag_bind('move', '<Button-1>', self.gameScoreClick)
		self.gameScore.tag_bind('move', '<Enter>', lambda e: self.cursorMove('enter'))
		self.gameScore.tag_bind('move', '<Leave>', lambda e: self.cursorMove('leave'))
		self.gameScore.tag_configure('curMove', foreground="white", background="red")
		self.gameScore.bind('<Control-e>', self.toggleEngine)
		self.gameScore.bind('<Control-b>', lambda e: blunderCheck(self))
		self.gameScore.bind('<Right>', lambda e: self.move(e, 'forward'))
		self.gameScore.bind('<Left>', lambda e: self.move(e, 'backward'))
		self.gameScore.bind("<Down>", self.selectVariation)
		self.gameScore.bind("<Up>", self.selectVariation)
		self.gameScore.bind("<Control-o>", self.loadGameFile)
		self.gameScore.bind("<Control-w>", self.removeTab)

		# Add widgets to paned window
		self.pWindow.add(self.boardFrame, stretch='always')
		self.pWindow.add(self.controlFrame, stretch='always')

		self.gui.root.bind("<Control-s>", lambda e: self.gui.savePGN(self.game, self.nodes))

	def canvasTouch(self, e):
		# get id of canvas item closest to click point
		# if that item is tagged with 'piece', get the next item
		# under that, i.e. the square
		sqId = self.canvas.find_closest(e.x, e.y, 0, 'piece')[0]
		# The 2nd tag of a square is always its name, i.e. 'e4'
		sqName = self.canvas.gettags(sqId)[1]
		# if is the second touch
		if self.MiP:
			# is this the same square clicked the last time?
			# if so, we'll unhighlight everything and return
			isSameSq = sqId == self.MiP[0][0]
			# unhighlight the from square
			self.canvas.itemconfigure(self.MiP[0][0], width=0)
			# unhighlight each to square
			for m in self.MiP:
				# if this finishes one of the legal moves, make it!
				if self.canvas.gettags(m[1])[1] == sqName:
					self.makeHumanMove(m[2])
				self.canvas.itemconfigure(m[1], width=0)
			self.MiP = []
			return

		# To make it here, this is first touch.
		# Iterate all the legal moves in the position, 
		# and highlight the potential landing squares
		board=self.curNode.board()
		for move in board.legal_moves:
			if chess.square_name(move.from_square) == sqName:
				fSqId = self.canvas.find_withtag(sqName)[0]
				self.canvas.itemconfigure(fSqId, outline=self.settings['hlSqColor'], width=4)

				tSqId = self.canvas.find_withtag(chess.square_name(move.to_square))[0]
				self.canvas.itemconfigure(tSqId, outline=self.settings['hlSqColor'], width=4)

				self.MiP.append((fSqId, tSqId, move))

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
		self.humanMovetoGameScore(move)
		self.makeMoveOnCanvas(move, 'forward')	
		self.printVariations()
		# self.board=self.curNode.board()
		if self.activeEngine != None:
			infiniteAnalysis(self)

	def humanMovetoGameScore(self, move):
		# if the move is already a variation, update board as usual
		if self.curNode.has_variation(move):
			self.curNode = self.curNode.variation(move)
			self.updateGameScore()
		# otherwise, we need to add the variation
		else:
			self.gameScore.config(state='normal')
			moveranges = self.gameScore.tag_ranges('move')
			curNodeIndex = self.nodes.index(self.curNode)
			board = self.curNode.board()
			self.curNode = self.curNode.add_variation(move)
			# if starting a variation, need to open paren before the next move,
			# set mark between parens, and output first move
			moveTxt = f"{self.curNode.san()}" 
			if self.curNode.starts_variation():
				insertPoint = moveranges[curNodeIndex*2+1]
				moveNo = f"{board.fullmove_number}." if board.turn else f"{board.fullmove_number}..."
				self.gameScore.tag_remove('curMove', '0.0', 'end')
				# Bug: new variation should go before the next mainline move,
				# not before the sibling variation.
				self.gameScore.insert(insertPoint, ' ()')
				# put varEnd mark between the ()
				self.gameScore.mark_set('varEnd', f"{insertPoint}+2 c")
				self.gameScore.insert('varEnd', moveNo)
				self.gameScore.insert('varEnd', moveTxt, ('move', 'curMove'))
				# add variation to node list
				self.nodes.insert(curNodeIndex+2, self.curNode)
			# if continuing a variation, need to add move at mark
			else:
				insertPoint = moveranges[curNodeIndex*2]
				self.gameScore.mark_set('varEnd', f"{insertPoint}-2 c")
				moveNo = f" {board.fullmove_number}." if board.turn else " "
				self.gameScore.tag_remove('curMove', '0.0', 'end')
				self.gameScore.insert('varEnd', moveNo)
				self.gameScore.insert('varEnd', moveTxt, ('move', 'curMove'))
				# add variation to node list
				self.nodes.insert(curNodeIndex+1, self.curNode)

			self.gameScore.config(state='disabled')

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
		self.printVariations()
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

	def movePiece(self, move, direction):
		ts,fs = move.to_square, move.from_square
		sqs = (fs, ts) if direction == 'forward' else (ts, fs)
		self.moveCanvasPiece(*sqs)

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
		# pdb.set_trace()
		targetSq = move.to_square if direction == 'forward' else move.from_square
		# if direction == 'forward' else move.from_square
		self.deletePieceImage(targetSq)
		self.putImage(targetSq, direction)

	def capturing(self, move, direction):
		ts,fs = move.to_square, move.from_square
		if direction == 'forward':
			self.deletePieceImage(ts)
			self.moveCanvasPiece(fs, ts)
		else:
			self.moveCanvasPiece(ts, fs)
			self.putImage(ts, direction)

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
		if direction == 'forward':
			squares = (fs, ts)
			self.moveCanvasPiece(*squares)
			file = chess.square_file(ts)
			rank = chess.square_rank(fs)
			self.deletePieceImage(chess.square(file,rank))
		else:
			squares = (ts, fs)
			self.moveCanvasPiece(*squares)
			file = chess.square_file(ts)
			rank = chess.square_rank(fs)
			self.putImage(chess.square(file, rank), direction)

	# create 64 rectangles to be sized and positioned later
	def createSquares(self):
		file = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
		rank = ('8', '7', '6', '5', '4', '3', '2', '1')
		sqColor = (self.settings['lightColorSq'], self.settings['darkColorSq'])
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
			self.makeMoveOnCanvas(move, direction)
		else:
			if self.curNode == self.curNode.game(): return
			move = self.curNode.move
			self.makeMoveOnCanvas(move, direction)
			self.curNode=self.curNode.parent

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


def main():
	from gui import GUI
	GUI()

if __name__ == '__main__':
	main()