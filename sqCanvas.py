from PIL import Image, ImageTk
from tkinter import Canvas
import chess

'''
Subclass of tkinter Canvas widget that maintains square aspect ratio
6/7/2020: Glen Pritchard

Sets the height and width of the canvas to its parent window/frame's shortest dimension.
4/24/2021 Update: refactored boardPane module to move all canvas related code here (not just the code to mainain a square aspect ratio)
'''
class sqCanvas(Canvas):
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
		Canvas.__init__(self, parent)
		self.whiteSouth = True	# True: white pieces on south side of board; False reverse
		cWidth = int(self.boardPane.gui.screenW/2)
		self.configure(highlightthickness=0, width=cWidth)
		self.bind("<Configure>", self.on_resize)
		self.bind("<Button-1>", self.canvasTouch)
		self.pack()

	# resize the canvas as a square based on shortest dimension of master widget
	def on_resize(self, e):
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

	# Put a new piece on the board
	# In a regular game, this may be because a piece has been promoted or 
	# a backward move puts a taken piece back on the board
	# A board is created to represent the current state of the board that 
	# needs to be mimiced in the GUI. In the event of a backward move, 
	# that the the parent of the current node.
	def putImage(self, square, direction='forward'):
		board = self.boardPane.curNode.board() if direction == 'forward' else self.boardPane.curNode.parent.board()
		sqName = chess.square_name(square)
		coords = self.coords(sqName)
		piece = board.piece_at(square) 
		# piece.symbol() returns the letter description for the piece, eg P or p  
		pieceName = piece.symbol()
		i=self.create_image((coords[0], coords[1]), image=self.tkPieceImg[pieceName], anchor='nw', tag='piece')
		self.pieceImgCache[sqName] = i


	# create 64 rectangles to be sized and positioned later
	def createSquares(self):
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
		if self.boardPane.MiP:
			# is this the same square clicked the last time?
			# if so, we'll unhighlight everything and return
			isSameSq = sqId == self.boardPane.MiP[0][0]
			# unhighlight the from square
			self.itemconfigure(self.boardPane.MiP[0][0], width=0)
			# unhighlight each to square
			for m in self.boardPane.MiP:
				# if this finishes one of the legal moves, make it!
				if self.gettags(m[1])[1] == sqName:
					self.makeHumanMove(m[2])
				self.itemconfigure(m[1], width=0)
			self.boardPane.MiP = []
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

				self.boardPane.MiP.append((fSqId, tSqId, move))

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
				self.boardPane.enPassant(move, direction)
			else:
				self.boardPane.capturing(move, direction)
		elif isCastling:
			self.boardPane.castling(move, direction, isKingSideCastling)
		else:
			self.boardPane.movePiece(move, direction)	# this is a normal move
		if isPromotion:
			self.boardPane.promotion(move, direction) # promotion can either be by capture or normal move

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
				self.coords(self.squares[sqIds], xpos, ypos, xpos+sqSize, ypos+sqSize)
				xpos += direction
				sqIds+=1
			ypos += direction
			xpos = xreset

	# when board is resized, resize the piece images so as not to lose resolution
	def resizePieceImage(self, im):
		dim = int(round(self.boardSize/8))
		if int(dim)  <= 0: return
		img = im.resize((int(dim), int(dim)), Image.LANCZOS)
		return ImageTk.PhotoImage(image=img)


	def resizePieceImages(self):
		for name in self.boardPane.gui.pieceImg:
			self.tkPieceImg[name] = self.resizePieceImage(self.boardPane.gui.pieceImg[name])

	# toggles white on north or south side of the board
	# bound to Reverse Button
	def reverseBoard(self, e=None):
		self.whiteSouth = not self.whiteSouth
		self.positionSquares()
		self.printCurrentBoard()

	# bound to change in board frame container size, redraw board based on width of container
	def resizeBoard(self, e):
		self.boardSize = min(e.height, e.width)
		self.positionSquares()
		self.resizePieceImages()
		self.printCurrentBoard()

	'''
	Move a piece from on sq to another
	@ fromSq obj chess.square object with piece on it
	@ toSq obj chess.square object to relocate piece
	'''
	def moveCanvasPiece(self, fromSq, toSq):
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
