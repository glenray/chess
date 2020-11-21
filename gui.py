from PIL import Image, ImageTk
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
from tkinter import scrolledtext
from boardPane import boardPane
import pdb

class GUI:
	def __init__(self):
		# a dictonary of pillow image objects for each piece png file
		self.pieceImg = {}
		# list of board panes in notebook
		self.boardPanes = []
		self.setup()

	def setup(self):
		self.createWindow()
		self.loadPieceImages()
		self.addBoardPane()
		# bring focus to the active notebook
		# self.notebook.index("current")
		self.root.nametowidget(self.notebook.select()).focus()
		self.root.mainloop()

	# create Window
	def createWindow(self):
		self.root = tk.Tk()
		self.root.title("Glen's Chess Analysis Wizard")
		# self.root.attributes('-fullscreen', True)
		self.root.bind("<Escape>", lambda e: self.root.destroy())
		self.root.geometry("1200x800+5+5")
		# takefocus=False prevents tab from taking the focus on tab traversal
		self.notebook = ttk.Notebook(self.root, takefocus=False)
		self.notebook.enable_traversal()
		self.notebook.pack(expand=1, fill='both')

	# Cache png image file for each piece
	def loadPieceImages(self):
		# map internal piece abbreviations to png file names on disk
		# key: the piece abbreviation: p=black pawn; P=white pawn, etc
		# The values are the png image file names without the extension: eg bp.png
		pieceNames = {'p':'bp', 'r':'br', 'n':'bn', 'b':'bb', 'q':'bq', 'k':'bk', 'P':'wp', 'R':'wr', 'N':'wn', 'B':'wb', 'Q':'wq', 'K':'wk'}
		for name in pieceNames:
			self.pieceImg[name] = Image.open(f'img/png/{pieceNames[name]}.png')

	def addBoardPane(self):
		file1 = 'pgn/blind-warrior vs AnwarQ.pgn'
		file2 = 'pgn/Annotated_Games.pgn'
		boardPane(self, file1)
		boardPane(self, file2)

def main():
	gui = GUI()

if __name__ == '__main__':
	main()