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
		self.root.mainloop()

	# create Window
	def createWindow(self):
		self.root = tk.Tk()
		self.root.title("Glen's Chess Analysis Wizard")
		self.root.bind("<Escape>", lambda e: self.root.destroy())
		self.root.geometry("800x800")
		self.notebook = ttk.Notebook(self.root)
		self.notebook.bind("<<NotebookTabChanged>>", self.test)

	def test(self, e):
		# pass
		# pdb.set_trace()
		index = self.notebook.index(self.notebook.select())
		activeBoard = self.boardPanes[index]
		activeBoard.pWindow.focus()
		activeBoard.variations.selection_set(0)


	# Cache png image file for each piece
	def loadPieceImages(self):
		# map internal piece abbreviations to png file names on disk
		# key: the piece abbreviation: p=black pawn; P=white pawn, etc
		# The values are the png image file names without the extension: eg bp.png
		pieceNames = {'p':'bp', 'r':'br', 'n':'bn', 'b':'bb', 'q':'bq', 'k':'bk', 'P':'wp', 'R':'wr', 'N':'wn', 'B':'wb', 'Q':'wq', 'K':'wk'}
		for name in pieceNames:
			self.pieceImg[name] = Image.open(f'img/png/{pieceNames[name]}.png')

	def addBoardPane(self):
		self.boardPanes.append(boardPane(self))
		self.boardPanes.append(boardPane(self))

def main():
	gui = GUI()

if __name__ == '__main__':
	main()