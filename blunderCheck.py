import random
import string
import chess.pgn
import chess.engine
import copy
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
from tkinter import scrolledtext
from gameScoreVisitor import gameScoreVisitor

'''
Implements blunder check functionality
'''
class blunderCheck():
	def __init__(self, boardPane):
		self.boardPane = boardPane
		self.game = boardPane.game
		self.engines = {
			'Stockfish' : "C:/Users/Glen/Documents/python/stockfish/bin/stockfish_20090216_x64_bmi2.exe"
		}
		self.defaults = {
			'threshold'	: '50',
			'depth'	: '15',
			'time'	: '15',
			'begMove'	: '1',
			'endMove'	: ''
		}
		self.blunderWin()

	def analyzePosition(self, board, limit):
		engine=chess.engine.SimpleEngine.popen_uci(self.engines['Stockfish'])
		info = engine.analyse(board, limit)
		engine.quit()
		return info

	# define and activate blunder check window
	def blunderWin(self):
		# Cancel button, Escape key, or x to close the window
		def blunderOff(e=None):
			self.boardPane.activeBlunderCheck = None
			self.blWindow.destroy()

		# tk variables
		# limit type from radio button, either depth or time
		self.limitType=tk.StringVar()
		self.limitType.set("time")
		# either number of seconds or ply depth, depending on radio button above
		self.limitValue = tk.IntVar()
		self.limitValue.set(10)

		labelFont = font.Font(family="Tahoma", size=16)
		buttonFont = font.Font(family="Tahoma", size=12)
		textFont = font.Font(family="Courier", size=14)

		buttonOptions = {"pady":5, "padx":5, "overrelief":'sunken', "font":buttonFont}

		self.blWindow = tk.Toplevel(self.boardPane.gui.root)
		# self.blWindow.attributes('-alpha', .9)
		self.blWindow.title("Blunder Check")
		self.blWindow.bind("<Escape>", blunderOff)
		self.blWindow.focus_force()
		# exit gracefully when window is closed by clicking x
		self.blWindow.protocol("WM_DELETE_WINDOW", blunderOff)
		# make window modal
		self.blWindow.grab_set()
		# Window Title
		self.label = tk.Label(self.blWindow, text="Blunder Check", pady=10, font=labelFont)
		self.label.grid(row=0, column=0, columnspan=2)
		# Text widget
		self.blText = tk.Text(self.blWindow, width=80, font=textFont, padx=10, pady=5)
		self.blText.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10)
		# Buttons
		self.buttonFrame = tk.Frame(self.blWindow)
		self.buttonFrame.grid(row=2, column=0, sticky='nsew')
		self.runButton = tk.Button(self.buttonFrame, text="Run", command=self.spawnBlunderCheck)
		self.runButton.configure(buttonOptions)
		self.runButton.pack(side='left', padx=10)
		self.runButton.focus()
		self.cancelButton = tk.Button(self.buttonFrame, text="Cancel", command=blunderOff)
		self.cancelButton.configure(buttonOptions)
		self.cancelButton.pack(side='left', padx=10)
		# End Buttons

		# container for blunder check settings
		self.settingFrame = tk.Frame(self.blWindow)
		self.settingFrame.columnconfigure(0, minsize=150)
		self.settingFrame.grid(row=2, column=1, sticky='nsew')
		# blunder threshold in cp: 
		self.threshLabel = tk.Label(self.settingFrame, text="Threshold")
		self.threshLabel.grid(row=0, column=0, sticky='w')
		self.threshEntry = tk.Entry(self.settingFrame)
		self.threshEntry.grid(row=0, column=1, sticky='w')
		self.threshEntry.insert('0', self.defaults['threshold'])
		# set the beginning move number to consider
		self.begMoveLabel = tk.Label(self.settingFrame, text="Begin Move")
		self.begMoveLabel.grid(row=1, column=0, sticky='w')
		self.begMoveEntry = tk.Entry(self.settingFrame)
		self.begMoveEntry.grid(row=1, column=1, sticky='w')
		self.begMoveEntry.insert('0', self.defaults['begMove'])
		# set the last move number to consider
		self.endMoveLabel = tk.Label(self.settingFrame, text="End Move")
		self.endMoveLabel.grid(row=2, column=0, sticky='w')
		self.endMoveEntry = tk.Entry(self.settingFrame)
		self.endMoveEntry.grid(row=2, column=1, sticky='w')
		self.endMoveEntry.insert('0', self.defaults['endMove'])		
		# Radio Buttons go inside separate frame
		self.limitFrame = tk.Frame(self.settingFrame, relief="groove", bd=3)
		self.limitFrame.grid(row=5, column=1, sticky='w')
		self.limitLabel = tk.Label(self.settingFrame, text="Limit Type")
		self.limitLabel.grid(row=5, column=0, sticky='w')
		
		# Use clam style to make radio button bigger
		# There is a funky problem with dip awareness in windows making the radio
		# buttons too small
		style=ttk.Style(self.blWindow)
		style.theme_use('clam')
		# print(style.layout('TRadiobutton'))
		# print(style.element_options('Radiobutton.border'))
		# print(style.element_options('Radiobutton.padding'))
		# print(style.element_options('Radiobutton.label'))
		# print(style.element_options('Radiobutton.focus'))
		style.configure('TRadiobutton', indicatorsize=25)

		self.depthRadio = ttk.Radiobutton(self.limitFrame, value="depth", variable=self.limitType, text="Depth", command=self.limitTypeChange)
		self.depthRadio.grid(row=0, column=1, sticky='w')
		self.timeRadio = ttk.Radiobutton(self.limitFrame, value="time", variable=self.limitType, text="Time", command=self.limitTypeChange)
		self.timeRadio.grid(row=0, column=2, sticky='e')
		# value of limit, either seconds for time or ply for depth
		self.limitValLbl = tk.Label(self.settingFrame)
		self.limitValLbl.grid(row=6, column=0, sticky='w')
		self.limitTypeChange()	# set the default
		self.limitVal = tk.Entry(self.settingFrame, textvariable=self.limitValue)
		self.limitVal.grid(row=6, column=1, sticky='w')

	# Update limit value label when limit type radio button changes
	def limitTypeChange(self, e=None):
		text = "Ply" if self.limitType.get()=="depth" else "Seconds"
		self.limitValLbl.configure(text=text)

	# Spawns blunder check thread
	def spawnBlunderCheck(self, e=None):
		self.runButton.configure(state='disabled')
		self.boardPane.activeBlunderCheck = "".join(random.choice(string.ascii_letters) for _ in range(10))
		limitVal = self.limitVal.get()
		thresh = self.threshEntry.get()
		begMove = self.begMoveEntry.get()
		endMove = self.endMoveEntry.get()

		limitVal = int(limitVal) if self.isInteger(limitVal) else None
		thresh = int(thresh) if self.isInteger(thresh) else None
		begMove = int(begMove) if self.isInteger(begMove) else 1
		endMove = int(endMove) if self.isInteger(endMove) else None

		kwargs = {
			'threadName':self.boardPane.activeBlunderCheck,
			"blunderThresh":thresh, 
			'begMove':begMove, 
			'endMove':endMove
		}
		# determine whether limit is depth or time
		if self.limitType.get()=="depth":
			kwargs['depth'] = limitVal
		else:
			kwargs['time'] = limitVal
		# spawn a thread for the blunder check
		threading.Thread(
			target=self.blunderChk, 
			kwargs=kwargs,
			name="Blunder Checker",
			daemon=True).start()

	def isInteger(self, n):
		try:
			float(n)
		except ValueError:
			return False
		else:
			return float(n).is_integer()

	# runs in a separate thread
	def blunderChk(self, threadName, begMove=1, endMove=None, blunderThresh=50, depth=5, time=None):
		# set engin limit based on time and depth
		# time takes precedence if set
		if time == None:
			assert depth, "Time or Depth must be specified"
			limit = chess.engine.Limit(depth=depth)
		else:
			assert time, "Time or Depth must be specified"
			limit = chess.engine.Limit(time=time)
		game = copy.deepcopy(self.game)
		saveInfo = False
		# loop through mainline nodes
		for node in game.mainline():
			moveNo = node.parent.board().fullmove_number
			# skip to next move if before begMove
			if moveNo<begMove: 
				node = node.variation(0)
				continue
			# terminate loop if after endMove
			if endMove != None and moveNo>endMove: break

			board = node.board()
			info = self.analyzePosition(board, limit)
			# on first move, analyze the move before to get bestScore for the move
			if saveInfo == False:
				saveInfo = self.analyzePosition(node.parent.board(), limit)

			# quit if blunder check has been turned off
			if self.boardPane.activeBlunderCheck != threadName: 
				print(f"Blunder Check {threadName} Cancelled")
				return

			parentBoard = node.parent.board()
			onMove = parentBoard.turn
			txtOnMove = "white" if onMove else "black"
			moveNo = node.parent.board().fullmove_number
			isBestMate = saveInfo['score'].pov(onMove).is_mate()
			bestScore = saveInfo["score"].pov(onMove)
			isActualMate = info['score'].pov(onMove).is_mate()
			actualScore = info["score"].pov(onMove)
			blunderMargin = None if isBestMate or isActualMate else bestScore.score()-actualScore.score()
			moveTxt = f"{moveNo}.{node.san()} " if onMove else f"{moveNo}...{node.san()}"

			# if the move made == the move predicted, it's not a blunder.
			if saveInfo['pv'][0] == node.move:
				isBlunder = False
			elif isBestMate and not isActualMate:
				isBlunder = True
				blunderWarning = f"{moveTxt} was a blunder: {txtOnMove} missed mate in {bestScore.mate()}"
			elif not isBestMate and isActualMate:
				isBlunder = True
				blunderWarning = f"{moveTxt} was a blunder: {txtOnMove} allows mate in {abs(actualScore.mate())}. Better is {parentBoard.san(saveInfo['pv'][0])} ({bestScore.score()})"
			elif blunderMargin and (abs(blunderMargin) > blunderThresh):
				isBlunder = True
				blunderWarning = f"Blunders {blunderMargin/100} pawns. Predicted move: {parentBoard.san(saveInfo['pv'][0])} ({bestScore.score()/100})"
			else:
				isBlunder = False
				blunderWarning = ''

			if isBlunder:
				moveVar = [x.move for x in node.parent.variations]
				# don't add line if the parent variation already has the same
				# variation
				if(saveInfo['pv'][0] in moveVar):
					blunderWarning = f"{moveTxt} Repeat! \n"
				else:
					line = node.parent.add_line(saveInfo['pv'], starting_comment=blunderWarning)
				self.blText.insert('end', f"{moveTxt} {blunderWarning}\n")
			else:
				self.blText.insert('end', moveTxt+"\n")
			self.blText.see('end')

			saveInfo = info
		# after breaking out of loop, 
		self.updateGUI(node.game())

	# after blundercheck completes, update gui before exit
	def updateGUI(self, game):
		# populating the text widget is wicked slow if it's visible
		self.boardPane.gameScore.pack_forget()
		self.boardPane.canvas.printCurrentBoard()
		self.boardPane.game = game
		self.boardPane.game.accept(gameScoreVisitor(self.boardPane))
		self.boardPane.gameScore.pack(anchor='n', expand=True, fill='both')
		self.boardPane.printVariations()
		self.blWindow.destroy()
