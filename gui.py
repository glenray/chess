from PIL import Image, ImageTk
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import font
from tkinter import scrolledtext

from boardPane import boardPane
from dbPane import dbPane

class GUI:
	def __init__(self):
		# a dictonary of pillow image objects for each piece png file
		self.pieceImg = {}
		self.setup()

	def setup(self):
		self.loadPieceImages()
		self.winDpiScaling()
		self.createWindow()
		self.loadPieceImages()
		self.addDBPane()
		# self.addBoardPane('pgn/carlsen.pgn')
		# self.addBoardPane('pgn/blind-warrior vs AnwarQ.pgn')
		# self.addBoardPane('pgn/subvars.pgn')
		# bring focus to the active notebook
		self.root.nametowidget(self.notebook.select()).focus()
		self.root.mainloop()

	def winDpiScaling(self):
		# activates hi res monitor support on windows
		try:
			from ctypes import windll
			windll.shcore.SetProcessDpiAwareness(1)
		except:
			pass

	def createWindow(self):
		# create Window
		self.root = tk.Tk()
		self.screenW = self.root.winfo_screenwidth()
		self.screenH = self.root.winfo_screenheight()
		# self.root.geometry(f"{int(self.screenW)}x{int(self.screenH)}")
		self.root.title("Glen's Chess Analysis Wizard")
		self.root.state('zoomed')
		# self.root.attributes('-fullscreen', True)
		self.root.bind("<Escape>", lambda e: self.root.destroy())
		self.root.bind("<Control-n>", self.openPGN)
		self.root.bind("<F2>", self.addDBPane)
		# takefocus=False prevents tab from taking the focus on tab traversal
		self.notebook = ttk.Notebook(self.root, takefocus=False)
		self.notebook.enable_traversal()
		self.notebook.pack(expand=1, fill='both')

	def openPGN(self, e):
		file = filedialog.askopenfilename()
		self.addBoardPane(file)

	def loadPieceImages(self):
		'''
		Cache png image file for each piece
		map internal piece abbreviations to png file names on disk
		key: the piece abbreviation: p=black pawn; P=white pawn, etc
		The values are the png image file names without the extension: eg bp.png
		'''
		pieceNames = {'p':'bp', 'r':'br', 'n':'bn', 'b':'bb', 'q':'bq', 'k':'bk', 'P':'wp', 'R':'wr', 'N':'wn', 'B':'wb', 'Q':'wq', 'K':'wk'}
		for name in pieceNames:
			self.pieceImg[name] = Image.open(f'img/png/{pieceNames[name]}.png')

	def addBoardPane(self, fileName=None):
		boardPane(self, fileName)

	def addDBPane(self, e=None):
		dbPane(self)

def main():
	gui = GUI()

if __name__ == '__main__':
	main()