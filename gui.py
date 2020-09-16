import chess
import chess.pgn
from PIL import Image, ImageTk
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font

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
		# a dictionary where key is square name and values are
		# {idx: canvas index of piece on square or None}
		# {img: tk image of piece to prevent garbage collection or None}
		self.pieceImgCache = {}

	def setup(self):
		self.createWidgets()
		self.createSquares()
		self.positionSquares()
		self.grabPieceImages()
		self.loadGame('pgn/blind.pgn')
		# self.setStartPos()
		self.printCurrentBoard()
		self.root.mainloop()

	def loadGame(self, path):
		self.board = self.loadPgnFile(path)

	def setStartPos(self):
		self.board.reset()

	def printCurrentBoard(self):
		self.canvas.update()
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
		dim = int(round(self.canvas.winfo_width()/8))
		coords = self.canvas.coords(chess.square_name(square))
		piece = self.board.piece_at(square)
		im = self.pieceImg[piece.symbol()]
		im = im.resize((int(dim), int(dim)), Image.LANCZOS)
		im = ImageTk.PhotoImage(image=im)
		i=self.canvas.create_image((coords[0], coords[1]), image=im, anchor='nw', tag='piece')
		self.pieceImgCache[sqName] = {'img':im, 'idx': i}

	def deletePieceImage(self, sq):
		piece = self.pieceImgCache[chess.square_name(sq)]['idx']
		self.canvas.delete(piece)
		del self.pieceImgCache[chess.square_name(sq)]

	# populate dictonary containing png images of pieces
	def grabPieceImages(self):
		# map internal piece abbreviations to png file names on disk
		# The keys is the abbreviation: p=black pawn; P=white pawn, etc
		# The values are the png image file names without the extension: eg bp.png
		pieceNames = {'p':'bp', 'r':'br', 'n':'bn', 'b':'bb', 'q':'bq', 'k':'bk', 'P':'wp', 'R':'wr', 'N':'wn', 'B':'wb', 'Q':'wq', 'K':'wk'}
		for name in pieceNames:
			self.pieceImg[name] = Image.open(f'img/png/{pieceNames[name]}.png')

	def createWidgets(self):
		# The window
		self.root = tk.Tk()
		self.root.title("Glen's Chess Analysis Wizard")
		self.root.bind("<Escape>", lambda e: self.root.destroy())
		self.root.geometry(f"{self.boardSize*2}x{self.boardSize*2}")
		self.root.bind('<Right>', self.moveForward)
		self.root.bind('<Left>', self.moveBack)

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
		self.canvas = sqCanvas(self.boardFrame)
		self.canvas.pack()

		# Frame for control panel
		self.controlFrame = tk.Frame(self.pWindow, bg="gray")

		# Button Bar Frame
		self.buttonBarFrame = tk.Frame(self.controlFrame, bg="blue", padx=5, pady=5)
		self.buttonBarFrame.pack(anchor="n", fill='x', expand=1)

		# New Game Button
		self.newGameButton = tk.Button(self.buttonBarFrame, buttonOptions, text="New Game", command=self.setStartPos)
		self.newGameButton.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

		# Reverse Board Button
		self.reverseBoardButton = tk.Button(self.buttonBarFrame, buttonOptions, text="Reverse Board", command=self.reverseBoard)
		self.reverseBoardButton.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
		
		# Add widgets to paned window
		self.pWindow.add(self.boardFrame, weight=1)
		self.pWindow.add(self.controlFrame, weight=1)

	# Return coordinates of a canvas rectangle object
	# @ sq obj a chess.square object
	# @ return a 4 element tuple containing the 
	# x,y locations of the upper left and lower right points of the square
	def getSqCoords(self, sq):
		sqName = chess.square_name(sq)
		return self.canvas.coords(sqName)

	'''
	Move a piece from on sq to another
	@ fromSq obj chess.square object with piece on it
	@ toSq obj chess.square object to relocate piece
	'''
	def moveCanvasPiece(self, fromSq, toSq):
		fromSqName = chess.square_name(fromSq)
		toSqName = chess.square_name(toSq)
		fromSqCoords = self.getSqCoords(fromSq)
		toSqCoords = self.getSqCoords(toSq)
		obj = self.pieceImgCache[chess.square_name(fromSq)]['idx']
		# find the distance between the from and to coordinates
		dx = toSqCoords[0]-fromSqCoords[0]
		dy = toSqCoords[1]-fromSqCoords[1]
		self.canvas.move(obj, dx, dy)

		self.pieceImgCache[toSqName] = self.pieceImgCache[fromSqName]
		self.pieceImgCache.pop(fromSqName)

	def moveBack(self, e):
		if len(self.board.move_stack) == 0 : return
		previousMove = self.board.pop()
		isCaptureMove = self.board.is_capture(previousMove)
		isCastling = self.board.is_castling(previousMove)
		isKingSideCastling = self.board.is_kingside_castling(previousMove)
		isEnPassant = self.board.is_en_passant(previousMove)
		self.moveHistory.append(previousMove)
		self.moveCanvasPiece(previousMove.to_square, previousMove.from_square)
		
		# moving backward, the move to square is the location of the piece and the from is where it needs to be returned to.
		if isCaptureMove:
			if isEnPassant:
				print("En Passant")
				# restore taken pawn
				file = chess.square_file(previousMove.to_square)
				rank = chess.square_rank(previousMove.from_square)
				self.putImage(chess.square(file,rank))
			else:
				self.putImage(previousMove.to_square)

		# Pawn promotion
		lastChar = self.board.uci(previousMove)[-1]
		if lastChar in ('q', 'b', 'n', 'r'):
			self.deletePieceImage(previousMove.from_square)
			self.putImage(previousMove.from_square)

		if isCastling:
			rookToSq = previousMove.to_square if e.keysym == 'Left' else previousMove.from_square
			rank = chess.square_rank(rookToSq)
			# set castled rook files depending which side of the board
			fromFile, toFile  = (5,7) if isKingSideCastling else (3,0)
			fromSq = chess.square(fromFile,rank)
			toSq = chess.square(toFile,rank)
			self.moveCanvasPiece(fromSq, toSq) # uncastle rook
			
		self.debugPrint(previousMove)

	def moveForward(self, e):
		if len(self.moveHistory) == 0 : return
		previousMove = self.moveHistory.pop()
		# These tests must be done before the move is pushed onto the board
		# These test return true only for valid moves
		# The moves are valid only before the board position is updated
		isCastling = self.board.is_castling(previousMove)
		isKingSideCastling = self.board.is_kingside_castling(previousMove)
		isCaptureMove = self.board.is_capture(previousMove)
		isEnPassant = self.board.is_en_passant(previousMove)
		captureSquare, captureFunction = previousMove.to_square, self.deletePieceImage
		self.board.push(previousMove)
		self.moveCanvasPiece(previousMove.from_square, previousMove.to_square)

		# Pawn promotion
		lastChar = self.board.uci(previousMove)[-1]
		if lastChar in ('q', 'b', 'n', 'r'):
			self.deletePieceImage(previousMove.to_square)
			self.putImage(previousMove.to_square)

		if isCaptureMove:
			if isEnPassant:
				print("En Passant")
				# remove taken pawn
				file = chess.square_file(previousMove.to_square)
				rank = chess.square_rank(previousMove.from_square)
				self.deletePieceImage(chess.square(file, rank))
			# On forward move, the act of moving the from piece to the to location removes the to piece from the image cache although the canvas image object is still there, so we should delete it here, but am not sure how
			# else:
				# 	self.deletePieceImage(previousMove.from_square)


		if isCastling:
			rookToSq = previousMove.to_square if e.keysym == 'Left' else previousMove.from_square
			rank = chess.square_rank(rookToSq)
			# set castled rook files depending which side of the board
			fromFile, toFile  = (5,7) if isKingSideCastling else (3,0)
			fromSq = chess.square(fromFile,rank)
			toSq = chess.square(toFile,rank)

			self.moveCanvasPiece(toSq, fromSq) # castle rook

		self.debugPrint(previousMove)

	def debugPrint(self, prevMove):
		print(
			self.board.uci(prevMove)+'\n',
			len(self.pieceImgCache),
			len(self.canvas.find_all()),
			'\n'+str(self.board)
		)

	# create 64 rectangles to be sized and positioned later
	def createSquares(self):
		rank = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')
		file = ('8', '7', '6', '5', '4', '3', '2', '1')
		sqColor = (self.lightColorSq, self.darkColorSq)
		for row in range(8):
			for col in range(8):
				sqName = rank[col]+str(file[row])
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
			board.push(move)
		return board

	''' Event bindings '''
	# bound to change in board frame container size, redraw board based on width of container
	def resizeBoard(self, e):
		self.boardSize = min(e.height, e.width)
		self.positionSquares()
		self.printCurrentBoard()

	def reverseBoard(self):
		self.whiteSouth = not self.whiteSouth
		self.positionSquares()
		self.printCurrentBoard()

if __name__ == '__main__':
	g=GUI()
	g.setup()
