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
		# a dictonary of pillow image objects for each piece png file
		self.pieceImg = {}
		# a list of tkinter formatted and resized images generated from the png files
		# They are stored here only to protect them from garbage collection.
		self.pieceTkImg = []
		self.whiteSouth = True	# True: white pieces on south side of board; False reverse
		self.moveHistory = []	# populate with newer moves when going back in the move stack

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
		self.pieceTkImg = []
		self.canvas.update()
		dim = int(round(self.canvas.winfo_width()/8))
		self.canvas.delete('piece')
		# piece_map returns a dictionary where 
		# key is the square number and value is a piece object
		# piece.symbol() returns the letter description for the piece, eg P or p  
		# Square numbers start at 0 which is the bottom right square,
		# home to the white light squared rook.
		pm = self.board.piece_map()
		for key in pm:
			self.putImage(key, dim)

	def putImage(self, square, dim):
		coords = self.canvas.coords(chess.square_name(square))
		piece = self.board.piece_at(square) 
		im = self.pieceImg[piece.symbol()]
		im = im.resize((int(dim), int(dim)), Image.LANCZOS)
		self.pieceTkImg.append(ImageTk.PhotoImage(image=im))
		self.canvas.create_image((coords[0], coords[1]), image=self.pieceTkImg[-1], anchor='nw', tag='piece')

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
		self.root.bind('<Right>', self.moveForw)
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

	def moveForw(self, e):
		print("right key pressed")

	def moveCanvasPiece(self, fromSq, toSq):
		# get the from and to squares of the move
		fromSqName = chess.square_name(fromSq)
		toSqName = chess.square_name(toSq)
		fromPieceName = self.board.piece_at(fromSq)
		toPieceName = self.board.piece_at(toSq)
		fromSqCoords = self.canvas.coords(fromSqName)
		toSqCoords = self.canvas.coords(toSqName)

		# find the piece canvas object to move
		x = (fromSqCoords[0]+fromSqCoords[2])/2
		y = (fromSqCoords[1]+fromSqCoords[3])/2
		obj = self.canvas.find_closest(x, y)

		# find the distance between the from and to coordinates
		dx = toSqCoords[0]-fromSqCoords[0]
		dy = toSqCoords[1]-fromSqCoords[1]

		self.canvas.move(obj, dx, dy)		

	def moveBack(self, e):
		if len(self.board.move_stack) == 0 : return
		previousMove = self.board.pop()
		self.moveHistory.append(previousMove)

		# moving backward, the move to square is the location of the piece and the from is where it needs to be returned to.
		self.moveCanvasPiece(previousMove.to_square, previousMove.from_square)

		# For capture moves, replace the taken piece on the board
		# Moving foward in move history, this will need to be remove piece from board
		isCaptureMove = self.board.san(previousMove).count('x')
		if isCaptureMove:
			dim = int(round(self.canvas.winfo_width()/8))
			self.putImage(previousMove.to_square, dim)

		# For castling, put rook back to original location
		if self.board.is_castling(previousMove):
			rank = chess.square_rank(previousMove.to_square) # int
			if self.board.is_kingside_castling(previousMove):
				fromFile, toFile  = 5,7
			else:
				fromFile, toFile  = 3,0

			fromSq = chess.square(fromFile,rank)
			toSq = chess.square(toFile,rank)
			self.moveCanvasPiece(fromSq, toSq)

		# For En Passant Capture
		if self.board.is_en_passant(previousMove):
			print("En Passant")

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
