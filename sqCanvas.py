from PIL import Image, ImageTk
from tkinter import Canvas
import chess

class sqCanvas(Canvas):
	'''
	Subclass of tkinter Canvas widget that maintains square aspect ratio
	6/7/2020: Glen Pritchard

	Sets the height and width of the canvas to its parent window/frame's shortest dimension.
	4/24/2021 Update: refactored boardPane module to move all canvas related code here (not just the code to mainain a square aspect ratio)
	'''
	def __init__(self, parent, boardPane):
		self.boardPane = boardPane
		self.boardSize = 400
		self.squares = []		# list of canvas ids for all canvas rectangles
		self.settings = {
			'lightColorSq' : "yellow",
			'darkColorSq' : "brown",
			'hlSqColor'	: 'black'
		}
		# a dictonary of tkImage objects for each piece resized for current board
		self.tkPieceImg = {}
		# a dictionary where key is square name and value is
		# the canvas index corresponding to the piece on the square
		self.pieceImgCache = {}
		# If a human move is in progress
		# a list of tuples (x, y, z) where
		# x: the canvas square id of the from piece with valid move
		# y: the canvas square id of the to square where piece can go
		# z: chess.move from x to y
		self.MiP = []
		Canvas.__init__(self, parent)
		self.whiteSouth = True	# True: white pieces on south side of board; False reverse
		cWidth = int(self.boardPane.gui.screenW/2)
		self.configure(highlightthickness=0, width=cWidth)
		self.bind("<Configure>", self.on_resize)
		self.bind("<Button-1>", self.canvasTouch)

	def on_resize(self, e):
		# resize the canvas as a square based on shortest dimension of master widget
		side = min(self.master.winfo_width(), self.master.winfo_height())
		self.config(width=side, height=side)

	def printCurrentBoard(self):
		board = self.boardPane.curNode.board()
		self.delete('piece')
		# piece_map returns a dictionary where 
		# key is the square number and value is a piece object
		# Square numbers start at 0 which is the bottom right square,
		# home to the white light squared rook.
		pm = board.piece_map()
		for key in pm:
			self.putImage(key)

	def putImage(self, square, direction='forward'):
		'''Put a new piece on the board
		In a regular game, this may be because a piece has been promoted or 
		a backward move puts a taken piece back on the board
		A board is created to represent the current state of the board that 
		needs to be mimiced in the GUI. In the event of a backward move, 
		that the the parent of the current node.'''
		board = self.boardPane.curNode.board() if direction == 'forward' else self.boardPane.curNode.parent.board()
		sqName = chess.square_name(square)
		coords = self.coords(sqName)
		piece = board.piece_at(square) 
		# piece.symbol() returns the letter description for the piece, eg P or p  
		pieceName = piece.symbol()
		i=self.create_image((coords[0], coords[1]), image=self.tkPieceImg[pieceName], anchor='nw', tag='piece')
		self.pieceImgCache[sqName] = i

	def createSquares(self):
		# create 64 rectangles to be sized and positioned later
		file = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
		rank = ('8', '7', '6', '5', '4', '3', '2', '1')
		sqColor = (self.settings['lightColorSq'], self.settings['darkColorSq'])
		for row in range(8):
			for col in range(8):
				sqName = str(file[col])+rank[row]
				sqId = self.create_rectangle(
					1,1,10,10, 
					fill=sqColor[(col+row)%2],
					tag=('square', sqName)
				)
				self.squares.append(sqId)

	def canvasTouch(self, e):
		# get id of canvas item closest to click point
		# if that item is tagged with 'piece', get the next item
		# under that, i.e. the square
		sqId = self.find_closest(e.x, e.y, 0, 'piece')[0]
		# The 2nd tag of a square is always its name, i.e. 'e4'
		sqName = self.gettags(sqId)[1]
		# if is the second touch
		if self.MiP:
			# is this the same square clicked the last time?
			# if so, we'll unhighlight everything and return
			isSameSq = sqId == self.MiP[0][0]
			# unhighlight the from square
			self.itemconfigure(self.MiP[0][0], width=0)
			# unhighlight each to square
			for m in self.MiP:
				# if this finishes one of the legal moves, make it!
				if self.gettags(m[1])[1] == sqName:
					self.makeHumanMove(m[2])
				self.itemconfigure(m[1], width=0)
			self.MiP = []
			return
		# To make it here, this is first touch.
		# Iterate all the legal moves in the position, 
		# and highlight the potential landing squares
		board=self.boardPane.curNode.board()
		for move in board.legal_moves:
			if chess.square_name(move.from_square) == sqName:
				fSqId = self.find_withtag(sqName)[0]
				self.itemconfigure(fSqId, outline=self.settings['hlSqColor'], width=4)

				tSqId = self.find_withtag(chess.square_name(move.to_square))[0]
				self.itemconfigure(tSqId, outline=self.settings['hlSqColor'], width=4)

				self.MiP.append((fSqId, tSqId, move))

	def makeHumanMove(self, move):
		self.boardPane.gameScore.humanMovetoGameScore(move)
		self.makeMoveOnCanvas(move, 'forward')	
		self.boardPane.variations.printVariations()
		if self.boardPane.activeEngine != None:
			infiniteAnalysis(self)

	def makeMoveOnCanvas(self, move, direction):
		# Internally, this move has been made already, so we need to look at the parent
		# node to evaluate what kind of move it was.
		board = self.boardPane.curNode.parent.board()
		(
			isCastling, 
			isKingSideCastling, 
			isCaptureMove, 
			isEnPassant, 
			isPromotion) = (
			board.is_castling(move),
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

	def enPassant(self, move, direction):
		'''Update GUI for en passant move
		@ move obj move object
		@ direction str either 'forward' or 'backward', 
		depending on direction through move stack'''
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

	def capturing(self, move, direction):
		ts,fs = move.to_square, move.from_square
		if direction == 'forward':
			self.deletePieceImage(ts)
			self.moveCanvasPiece(fs, ts)
		else:
			self.moveCanvasPiece(ts, fs)
			self.putImage(ts, direction)

	def promotion(self, move, direction):
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
		2. replace it with a pawn'''
		targetSq = move.to_square if direction == 'forward' else move.from_square
		self.deletePieceImage(targetSq)
		self.putImage(targetSq, direction)

	def movePiece(self, move, direction):
		ts,fs = move.to_square, move.from_square
		sqs = (fs, ts) if direction == 'forward' else (ts, fs)
		self.moveCanvasPiece(*sqs)

	def positionSquares(self):
		'''position squares in canvas based on current square size
		can build board with either color on bottom depending on
		value of self.whiteSouth'''
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
				self.coords(self.squares[sqIds], xpos, ypos, xpos+sqSize, ypos+sqSize)
				xpos += direction
				sqIds+=1
			ypos += direction
			xpos = xreset

	def resizePieceImage(self, im):
		'''when board is resized, resize the piece images so as not to lose resolution'''
		dim = int(round(self.boardSize/8))
		if int(dim)  <= 0: return
		img = im.resize((int(dim), int(dim)), Image.LANCZOS)
		return ImageTk.PhotoImage(image=img)

	def resizePieceImages(self):
		for name in self.boardPane.gui.pieceImg:
			self.tkPieceImg[name] = self.resizePieceImage(self.boardPane.gui.pieceImg[name])

	def reverseBoard(self, e=None):
		'''toggles white on north or south side of the board
		bound to Reverse Button'''
		self.whiteSouth = not self.whiteSouth
		self.positionSquares()
		self.printCurrentBoard()

	def resizeBoard(self, e):
		# bound to change in board frame container size, redraw board based on width of container
		self.boardSize = min(e.height, e.width)
		self.positionSquares()
		self.resizePieceImages()
		self.printCurrentBoard()

	def moveCanvasPiece(self, fromSq, toSq):
		'''
		Move a piece from on sq to another
		@ fromSq obj chess.square object with piece on it
		@ toSq obj chess.square object to relocate piece
		'''
		csn, cc, pic = chess.square_name, self.coords, self.pieceImgCache
		fromSqName, toSqName = csn(fromSq), csn(toSq)
		fromSqCoords, toSqCoords = cc(fromSqName), cc(toSqName)
		obj = pic[fromSqName]
		# find the distance between the from and to coordinates
		dx = toSqCoords[0]-fromSqCoords[0]
		dy = toSqCoords[1]-fromSqCoords[1]
		self.move(obj, dx, dy)
		# update image cache to add piece at toSq and remove piece at fromSq
		pic[toSqName] = pic[fromSqName]
		pic.pop(fromSqName)

	def deletePieceImage(self, sq):
		canvasIdx = self.pieceImgCache[chess.square_name(sq)]
		self.delete(canvasIdx)
		del self.pieceImgCache[chess.square_name(sq)]
