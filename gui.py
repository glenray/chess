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

import pdb

class GUI:
	def __init__(self):
		self.boardSize = 400
		self.lightColorSq = "yellow"
		self.darkColorSq = "brown"
		self.squares = []		# list of canvas ids for all canvas rectangles
		self.whiteSouth = True	# True: white pieces on south side of board; False reverse
		# a dictonary of pillow image objects for each piece png file
		self.pieceImg = {}
		# a dictonary of tkImage objects for each piece resized for current board
		self.tkPieceImg = {}
		# a dictionary where key is square name and value is
		# the canvas index corresponding to the piece on the square
		self.pieceImgCache = {}
		# randomly generated name of active engine thread
		self.activeEngine = None
		# list of nodes in mainline and all variations
		self.nodes = []
		self.curNode = None
		self.pgnFile = 'pgn/blind-warrior vs AnwarQ.pgn'
		# self.pgnFile = 'pgn/Annotated_Games.pgn'
		# self.pgnFile = 'pgn/testC.pgn'
		self.game = chess.pgn.read_game(open(self.pgnFile))
		# index of node.variations[index] selected in the variations popup
		self.varIdx = None

	def setup(self):
		self.createWidgets()
		# sets the game score and populate the self.nodes list
		self.nodes = self.game.accept(gameScoreVisitor(self))
		# current node set before the first move.
		self.curNode = self.nodes[0]
		self.createSquares()
		self.positionSquares()
		self.grabPieceImages()
		self.printCurrentBoard()
		self.root.mainloop()

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

	# Cache png image file for each piece
	def loadPieceImages(self):
		# map internal piece abbreviations to png file names on disk
		# key: the piece abbreviation: p=black pawn; P=white pawn, etc
		# The values are the png image file names without the extension: eg bp.png
		pieceNames = {'p':'bp', 'r':'br', 'n':'bn', 'b':'bb', 'q':'bq', 'k':'bk', 'P':'wp', 'R':'wr', 'N':'wn', 'B':'wb', 'Q':'wq', 'K':'wk'}
		for name in pieceNames:
			self.pieceImg[name] = Image.open(f'img/png/{pieceNames[name]}.png')

	# populate dictonary containing tk compatible piece images
	def grabPieceImages(self):
		if not self.pieceImg:
			self.loadPieceImages()
		for name in self.pieceImg:
			self.tkPieceImg[name] = self.resizePieceImage(self.pieceImg[name])

	# when board is resized, resize the piece images so as not to lose resolution
	def resizePieceImage(self, im):
		dim = int(round(self.boardSize/8))
		if int(dim)  <= 0: return
		img = im.resize((int(dim), int(dim)), Image.LANCZOS)
		return ImageTk.PhotoImage(image=img)

	# create all tkinter widgets and event bindings
	def createWidgets(self):
		# The window
		self.root = tk.Tk()
		self.root.title("Glen's Chess Analysis Wizard")
		self.root.bind("<Escape>", lambda e: self.root.destroy())
		self.root.geometry(f"{self.boardSize*2}x{self.boardSize*2}")
		self.root.bind('<Right>', lambda e: self.move(e, 'forward'))
		self.root.bind('<Left>', lambda e: self.move(e, 'backward'))
		self.root.bind('<Control-r>', self.reverseBoard)
		self.root.bind('<Control-e>', self.toggleEngine)

		# Fonts and Styling
		# print(font.families())	prints available font families
		buttonFont = font.Font(family="Tahoma", size=16)
		buttonOptions = {"pady":5, "padx":5, "overrelief":'groove', "font":buttonFont}

		# Paned Window
		self.pWindow = ttk.PanedWindow(self.root, orient="horizontal")
		self.pWindow.pack(fill="both", expand=1)

		# Frame container for board canvas
		self.boardFrame = tk.Frame(self.pWindow, bg="gray75")
		self.boardFrame.bind("<Configure>", self.resizeBoard)

		# Board Canvas
		self.canvas = sqCanvas(self.boardFrame, highlightthickness=0)
		self.canvas.pack()

		# Frame for control panel
		self.controlFrame = tk.Frame(self.pWindow, bg="green")

		# Button Bar Frame
		self.buttonBarFrame = tk.Frame(self.controlFrame, bg="blue", padx=5, pady=5)
		self.buttonBarFrame.pack(anchor='n', fill='x')

		# New Game Button
		self.newGameButton = tk.Button(self.buttonBarFrame, buttonOptions, text="New Game", command=self.setStartPos)
		self.newGameButton.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

		# Reverse Board Button
		self.reverseBoardButton = tk.Button(self.buttonBarFrame, buttonOptions, text="Reverse Board", command=self.reverseBoard)
		self.reverseBoardButton.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

		# game score
		self.gameScore = tk.scrolledtext.ScrolledText(self.controlFrame, width=10, font=("Tahoma", 14))
		self.gameScore.config(wrap=tk.WORD, padx=10, pady=10, state='disabled')
		self.gameScore.pack(anchor='n', expand=True, fill='both')
		self.gameScore.tag_bind('move', '<Button-1>', self.gameScoreClick)
		self.gameScore.tag_bind('move', '<Enter>', lambda e: self.cursorMove('enter'))
		self.gameScore.tag_bind('move', '<Leave>', lambda e: self.cursorMove('leave'))
		self.gameScore.tag_configure('curMove', foreground="white", background="red")

		# analysis pane
		self.analysis = tk.Text(self.controlFrame, height=10)
		self.analysis.config(wrap=tk.WORD, padx=10, pady=10)
		self.analysis.pack(anchor='n', expand=True, fill='both')

		# Add widgets to paned window
		self.pWindow.add(self.boardFrame, weight=1)
		self.pWindow.add(self.controlFrame, weight=1)

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
			self.spawnEngine()

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

	# pop up window when variations are encountered
	def varPopUp(self):
		def returnVar(e, lb):
			self.varIdx = lb.curselection()[0]
			varPop.destroy()
		# prevent right arrow event on root from advancing to next move
		# in self.gameScore
		self.root.unbind('<Right>')
		# popup Window
		varPop = tk.Toplevel(self.root)
		varPop.title("Variations")
		varPop.bind("<Escape>", lambda e: returnVar(e, lb))
		varPop.bind("<Right>", lambda e: returnVar(e, lb))
		# Label
		label = tk.Label(varPop, text="Variations", pady=10)
		label.pack()
		# variations list box
		lb = tk.Listbox(varPop)
		for var in self.curNode.variations:
			b=var.parent.board()
			moveNo = b.fullmove_number if b.turn==True else f'{b.fullmove_number}...'
			lb.insert(self.nodes.index(var), f"{moveNo} {var.san()}")
		lb.pack()
		lb.focus_force()
		lb.selection_set(0)
		# pause main_loop until varPop finishes
		self.root.wait_window(varPop)
		# Re-bind right arrow key to root for move navigation
		self.root.bind('<Right>', lambda e: self.move(e, 'forward'))

	# If mainline has alternative variations, popup a variation window
	# to select the desired variation.
	def varWindow(self):
		if len(self.curNode.variations)>1:
			varIdx = self.varPopUp()
			return self.curNode.variations[self.varIdx]
		else:
			return self.curNode.variations[0]

	''' Event bindings '''
	# Updates GUI after moving though game nodes both directions
	# bound to left and right arrow keys at root
	def move(self, e, direction):
		if direction == 'forward':
			if self.curNode.is_end(): return
			self.curNode = self.varWindow()
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
		if self.activeEngine != None:
			self.spawnEngine()

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

	def cursorMove(self, status):
		if status == 'leave':
			self.gameScore.config(cursor='')
		elif status == 'enter':
			self.gameScore.config(cursor='hand2')

	# Engine analyzing the current board
	# This is always run in a separate thread by self.spawnEngine()
	# tName str name of the thread
	# The thread running this engine will quit if it is no longer named
	# as the active engine in self.activeEngine
	def __engine(self, tName):
		print(f"Engine {tName} On.")
		engine = chess.engine.SimpleEngine.popen_uci("C:/Users/Glen/Documents/python/stockfish/bin/stockfish_20090216_x64_bmi2.exe")
		with engine.analysis(self.board) as analysis:
			for info in analysis:
				# if this is no longer the active engine, quit thread
				if self.activeEngine != tName:
					print(f"Engine {tName} Off.")
					break

				pv = info.get('pv')
				if pv != None and (len(pv) > 5 or info.get("score").is_mate()):
					output = strings['permAnalysis'].format(
						score = info.get("score").white(),
						depth = info.get('depth'),
						nps = info.get('nps'),
						nodes = info.get('nodes'),
						time = info.get('time'),
						pvString = self.board.variation_san(pv)	
					)
					self.analysis.delete('0.0', 'end')
					self.analysis.insert("0.1", output)
		engine.quit()

	# spawn a new engine thread when self.board changes 
	def spawnEngine(self):
		# generate random thread name
		threadName = "".join(random.choice(string.ascii_letters) for _ in range(10))
		self.activeEngine = threadName
		threading.Thread(target=self.__engine, args=(threadName,), daemon=True).start()

	# toggles an engine to analyze the current board position
	def toggleEngine(self, e):
		if self.activeEngine == None:
			self.spawnEngine()
		else:
			self.activeEngine = None

if __name__ == '__main__':
	g=GUI()
	g.setup()
