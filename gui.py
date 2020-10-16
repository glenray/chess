import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
import chess
import chess.pgn
from PIL import Image, ImageTk
from sqCanvas import sqCanvas

class GUI:
	def __init__(self):
		self.boardSize = 400
		self.lightColorSq = "yellow"
		self.darkColorSq = "brown"
		self.squares = []		# list of canvas ids for all canvas rectangles
		# python chess board object
		self.board = chess.Board()
		# a list of tkinter formatted and resized images generated from the png files
		# They are stored here only to protect them from garbage collection.
		self.pieceTkImg = []
		self.whiteSouth = True	# True: white pieces on south side of board; False reverse
		self.moveHistory = []	# populate with newer moves when going back in the move stack
		# a dictonary of pillow image objects for each piece png file
		self.pieceImg = {}
		# a dictonary of tkImage objects for each piece resized for current board
		self.tkPieceImg = {}
		# a dictionary where key is square name and value is
		# the canvas index corresponding to the piece on the square
		self.pieceImgCache = {}
		# List of moves in short algebreic notation
		self.moveList = []
		# list of tkinter text ranges for moves in games
		self.moveIndices = []

	def setup(self):
		self.board = self.loadPgnFile('pgn/blind-warrior vs AnwarQ.pgn')
		# self.setStartPos()
		self.createWidgets()
		self.createSquares()
		self.canvas.update()
		self.positionSquares()
		self.grabPieceImages(True)
		self.printCurrentBoard()
		self.populateGameScore()
		self.root.mainloop()

	def setStartPos(self):
		self.board.reset()
		self.printCurrentBoard()

	def printCurrentBoard(self):
		self.canvas.delete('piece')
		# piece_map returns a dictionary where 
		# key is the square number and value is a piece object
		# piece.symbol() returns the letter description for the piece, eg P or p  
		# Square numbers start at 0 which is the bottom right square,
		# home to the white light squared rook.
		pm = self.board.piece_map()
		for key in pm:
			self.putImage(key)

	def putImage(self, square):
		sqName = chess.square_name(square)
		coords = self.canvas.coords(sqName)
		piece = self.board.piece_at(square)
		pieceName = piece.symbol()
		i=self.canvas.create_image((coords[0], coords[1]), image=self.tkPieceImg[pieceName], anchor='nw', tag='piece')
		self.pieceImgCache[sqName] = i

	def deletePieceImage(self, sq):
		canvasIdx = self.pieceImgCache[chess.square_name(sq)]
		self.canvas.delete(canvasIdx)
		del self.pieceImgCache[chess.square_name(sq)]

	# populate dictonary containing png images of pieces
	def grabPieceImages(self, doFiles = False):
		# map internal piece abbreviations to png file names on disk
		# The keys is the abbreviation: p=black pawn; P=white pawn, etc
		# The values are the png image file names without the extension: eg bp.png
		pieceNames = {'p':'bp', 'r':'br', 'n':'bn', 'b':'bb', 'q':'bq', 'k':'bk', 'P':'wp', 'R':'wr', 'N':'wn', 'B':'wb', 'Q':'wq', 'K':'wk'}
		for name in pieceNames:
			if doFiles:
				self.pieceImg[name] = Image.open(f'img/png/{pieceNames[name]}.png')
			self.tkPieceImg[name] = self.resizePieceImage(self.pieceImg[name])

	def resizePieceImage(self, im):
		dim = int(round(self.canvas.winfo_width()/8))
		img = im.resize((int(dim), int(dim)), Image.LANCZOS)
		return ImageTk.PhotoImage(image=img)

	def createWidgets(self):
		# The window
		self.root = tk.Tk()
		self.root.title("Glen's Chess Analysis Wizard")
		self.root.bind("<Escape>", lambda e: self.root.destroy())
		self.root.geometry(f"{self.boardSize*2}x{self.boardSize*2}")
		self.root.bind('<Right>', lambda e: self.move(e, 'forward'))
		self.root.bind('<Left>', lambda e: self.move(e, 'backward'))
		self.root.bind('<Control-r>', self.reverseBoard)

		# Fonts and Styling
		# print(font.families())	# prints available font families
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
		self.gameScore = tk.Text(self.controlFrame, width=10, font=("helvetica", 14))
		self.gameScore.config(wrap=tk.WORD, padx=10, pady=10, state='disabled')
		self.gameScore.pack(anchor='n', expand=True, fill='both')
		self.gameScore.tag_bind('move', '<Button-1>', self.gameScoreClick)
		self.gameScore.tag_bind('move', '<Enter>', lambda e: self.cursorMove('enter'))
		self.gameScore.tag_bind('move', '<Leave>', lambda e: self.cursorMove('leave'))
		self.gameScore.tag_configure('curMove', foreground="white", background="red")

		# Add widgets to paned window
		self.pWindow.add(self.boardFrame, weight=1)
		self.pWindow.add(self.controlFrame, weight=1)

	# click on move in gamescore updates board to that move
	def gameScoreClick(self, e):
		# get text indicies of click location
		location = f"@{e.x},{e.y}+1 chars"
		# find nearest previous move tag location
		moveTagRange = self.gameScore.tag_prevrange('move', location)
		clicked = (str(moveTagRange[0]), str(moveTagRange[1]))
		# determine the half move number of the clicked move
		halfMoveNo = self.moveIndices.index(clicked)
		# determine half move number of the current move
		curMove = self.board.fullmove_number*2-self.board.turn-2
		# the distance to travel in the game score
		distance = halfMoveNo-curMove
		# quit if you clicked on the move you are already on
		if distance == 0 : return
		self.jumpToMove(distance)
		self.printCurrentBoard()
		self.updateGameScore()

	# update self.board by half moves from current position
	# distance int number of half moves to jump in game. Positive moves forward
	# Negative distance moves back
	def jumpToMove(self, distance):
		for i in range(0,abs(distance)):
			if distance>0:
				move = self.moveHistory.pop()
				self.board.push(move)
			else:
				move = self.board.pop()
				self.moveHistory.append(move)

	def populateGameScore(self):
		self.gameScore.config(state='normal')
		text = ''
		moveNo, onMove = 1, 'w'
		for move in self.moveList:
			if onMove == 'w':
				prefix, onMove, moveNo = (f"{moveNo}.", 'b', moveNo) 
			else: 
				prefix, onMove, moveNo = ('', 'w', moveNo+1)
			self.gameScore.insert('end', prefix)
			self.gameScore.insert('end', move, ('move',))
			self.gameScore.insert('end', ' ')
		self.gameScore.config(state='disabled')
		locArr = self.gameScore.tag_ranges('move')
		# highlight last move
		self.gameScore.tag_add('curMove', locArr[-2], locArr[-1])
		# list of begin-end indices of each move
		r = self.gameScore.tag_ranges('move')
		self.moveIndices = [(str(r[i]), str(r[i+1])) for i in range(0,len(r),2)]

	'''
	Move a piece from on sq to another
	@ fromSq obj chess.square object with piece on it
	@ toSq obj chess.square object to relocate piece
	'''
	def moveCanvasPiece(self, fromSq, toSq):
		fromSqName = chess.square_name(fromSq)
		toSqName = chess.square_name(toSq)
		fromSqCoords = self.canvas.coords(fromSqName)
		toSqCoords = self.canvas.coords(toSqName)
		obj = self.pieceImgCache[fromSqName]
		# find the distance between the from and to coordinates
		dx = toSqCoords[0]-fromSqCoords[0]
		dy = toSqCoords[1]-fromSqCoords[1]
		self.canvas.move(obj, dx, dy)

		self.pieceImgCache[toSqName] = self.pieceImgCache[fromSqName]
		self.pieceImgCache.pop(fromSqName)

	def testMoveProperties(self, move):
		return (
			self.board.is_castling(move),
			self.board.is_kingside_castling(move),
			self.board.is_capture(move),
			self.board.is_en_passant(move),
			self.board.uci(move)[-1] in ('q', 'b', 'n', 'r')		
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

	# returns a board object of game loaded from pgn file
	def loadPgnFile(self, path):
		pgn = open(path)
		game = chess.pgn.read_game(pgn)
		board = game.board()
		for move in game.mainline_moves():
			self.moveList.append(board.san(move))
			board.push(move)
		return board

	''' Event bindings '''
	# Updates GUI after moving though move stack in both directions
	# bound to left and right arrow keys at root
	def move(self, e, direction):
		if direction == 'forward':
			# quit if already at end of the game
			if len(self.moveHistory) == 0 : return
			move = self.moveHistory.pop()
			# Moving forward in the move list, testing must be done before the move is 
			# pushed onto the board.
			# These test return true only for valid moves
			(isCastling, isKingSideCastling, isCaptureMove, isEnPassant,
					isPromotion) = self.testMoveProperties(move)
			self.board.push(move)
		else:
			# quite if already at beginning of the game
			if len(self.board.move_stack) == 0 : return
			move = self.board.pop()
			# Moving back in move list, testing must be done after the move is
			# popped back onto the board
			(isCastling, isKingSideCastling, isCaptureMove, isEnPassant,
				isPromotion) = self.testMoveProperties(move)
			self.moveHistory.append(move)

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

	# emphasize current move in game score
	def updateGameScore(self):
		gs, bd = self.gameScore, self.board
		# 0 based half move number, ie white's first move is 0
		idx = bd.fullmove_number*2-bd.turn-2
		moves = gs.tag_ranges('move')
		# key.first will produce error when the key does not exist in text such as before the first move is made 
		try: gs.tag_remove('curMove', 'curMove.first', 'curMove.last')
		except: pass
		if idx > -1: gs.tag_add('curMove', moves[idx*2], moves[idx*2+1])

	# bound to change in board frame container size, redraw board based on width of container
	def resizeBoard(self, e):
		self.boardSize = min(e.height, e.width)
		self.positionSquares()
		self.grabPieceImages(False)
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

if __name__ == '__main__':
	g=GUI()
	g.setup()
