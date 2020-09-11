import chess
from PIL import Image, ImageTk
import tkinter as tk
import tkinter.ttk as ttk
from sqCanvas import sqCanvas

class GUI:
	def __init__(self):
		self.boardSize = 400
		self.lightColorSq = "yellow"
		self.darkColorSq = "brown"
		self.squares = []		# list of canvas ids for all canvas rectangles
		self.buttonOptions = {"pady":5, "padx":5, "bd":4, "overrelief":'groove'}
		self.board = chess.Board()

	def setup(self):
		self.createWidgets()
		self.createSquares()
		self.positionSquares()
		self.grabPieceImages()
		self.setStartPos()
		self.root.mainloop()

	def setStartPos(self):
		self.img = []
		self.canvas.update()
		dim = int(round(self.canvas.winfo_width()/8))
		# piece_map returns a dictionary where 
		# key is the square number and value is a piece object
		# piece.symbol() returns the letter description for the piece, eg P or p  
		# Square numbers start at 0 which is the bottom right square,
		# home to the white light squared rook.
		pm = self.board.piece_map()
		for key in pm:
			self.putImage(pm[key].symbol(), key, dim)

	def putImage(self, piece, sqNum, dim):
		row = int((63-sqNum)/8)
		col = (63-sqNum)%8
		im = self.pieceImages[piece]
		im = im.resize((int(dim), int(dim)), Image.LANCZOS)
		self.img.append(ImageTk.PhotoImage(image=im))
		self.canvas.create_image((col*dim, row*dim), image=self.img[-1], anchor='nw')

	# create dictonary containing png images of pieces
	def grabPieceImages(self):
		# map internal piece abbreviations to png file names on disk
		# The keys is the abbreviation: p=black pawn; P=white pawn, etc
		# The values are the png image file names without the extension: eg bp.png
		pieceNames = {'p':'bp', 'r':'br', 'n':'bn', 'b':'bb', 'q':'bq', 'k':'bk', 'P':'wp', 'R':'wr', 'N':'wn', 'B':'wb', 'Q':'wq', 'K':'wk'}
		self.pieceImages = {}
		for name in pieceNames:
			self.pieceImages[name] = Image.open(f'img/png/{pieceNames[name]}.png')

	def createWidgets(self):
		# The window
		self.root = tk.Tk()
		self.root.title("Glen's Chess Analysis Wizard")
		self.root.bind("<Escape>", lambda e: self.root.destroy())
		self.root.geometry(f"{self.boardSize*2}x{self.boardSize*2}")

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
		self.controlFrame = tk.Frame(self.pWindow, bg="pink")

		# Button Bar Frame
		self.buttonBarFrame = tk.Frame(self.controlFrame, bg="blue", padx=5, pady=5)
		self.buttonBarFrame.pack(anchor="n", fill='x', expand=1)

		# Button
		self.refreshButton = tk.Button(self.buttonBarFrame, self.buttonOptions, text="Refresh\nPieces", command=self.setStartPos)
		self.refreshButton.pack(anchor='nw')
		
		# Add widgets to paned window
		self.pWindow.add(self.boardFrame, weight=1)
		self.pWindow.add(self.controlFrame, weight=1)

	# create 64 rectangles to be sized and positioned later
	def createSquares(self):
		sqColor = (self.lightColorSq, self.darkColorSq)
		for row in range(8):
			for col in range(8):
				sqId = self.canvas.create_rectangle(
					1,1,10,10, 
					fill=sqColor[(col+row)%2],
					tag='square'
				)
				self.squares.append(sqId)

	# re-position squares based on current value of self.boardSize
	def positionSquares(self):
		xpos, ypos, sqIds, lblIds = 0, 0, 0, 0
		sqSize = self.boardSize/8
		for col in range(8):
			for row in range(8):
				self.canvas.coords(self.squares[sqIds], xpos, ypos, xpos+sqSize, ypos+sqSize)
				xpos += sqSize
				sqIds+=1
			ypos += sqSize
			xpos = 0

	''' Event bindings '''
	# bound to change in board frame container size, redraw board based on width of container
	def resizeBoard(self, e):
		self.boardSize = min(e.height, e.width)
		self.positionSquares()

if __name__ == '__main__':
	g=GUI()
	g.setup()
