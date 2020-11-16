import chess.pgn
import chess.engine
import copy
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
from tkinter import scrolledtext
from gameScoreVisitor import gameScoreVisitor
import pdb
# pdb.set_trace()

'''
Implements blunder check functionality
'''
class blunderCheck():
	def __init__(self, gui):
		self.gui = gui
		self.game = gui.game
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

	def analyzePosition(self, board, limit):
		engine=chess.engine.SimpleEngine.popen_uci(self.engines['Stockfish'])
		info = engine.analyse(board, limit)
		engine.quit()
		return info

	def blunderWin(self):
		# Cancel button
		def blunderOff(e=None):
			self.gui.isBlunderCheck = False
			# if the blunder checker is not running, then destroy the window,
			# returning contol to root
			# otherwise, the blunderChk method will destroy the window after terminating the thread.
			threadNames = [t.name for t in threading.enumerate()]
			if ("Blunder Checker" in threadNames) == False:
				self.blWindow.destroy()

		labelFont = font.Font(family="Tahoma", size=16)
		buttonFont = font.Font(family="Tahoma", size=12)
		textFont = font.Font(family="Courier", size=14)

		buttonOptions = {"pady":5, "padx":5, "overrelief":'sunken', "font":buttonFont}
		titleOptions = {"pady": 10, "font": labelFont}

		self.blWindow = tk.Toplevel(self.gui.root)
		self.blWindow.title("Blunder Check")
		self.blWindow.bind("<Escape>", blunderOff)
		self.blWindow.focus_force()
		# make window modal
		self.blWindow.grab_set()
		self.blWindow.grid_columnconfigure(0, weight=1)
		self.blWindow.grid_columnconfigure(1, weight=2)
		self.blWindow.grid_columnconfigure(2, weight=3)

		self.blText = tk.Text(self.blWindow, width=80, font=textFont, padx=10, pady=5)
		self.blText.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10)

		self.label = tk.Label(self.blWindow, text="Blunder Check")
		self.label.configure(titleOptions)
		self.label.grid(row=0, column=0, columnspan=2)

		self.buttonFrame = tk.Frame(self.blWindow)
		self.buttonFrame.columnconfigure(0, weight=0)
		self.buttonFrame.grid(row=2, column=0, sticky='nsew')

		self.settingFrame = tk.Frame(self.blWindow)
		self.settingFrame.columnconfigure(1, weight=1)
		self.settingFrame.columnconfigure(2, weight=2)
		self.settingFrame.grid(row=2, column=1, sticky='nsew')


		self.runButton = tk.Button(self.buttonFrame, text="Run", command=self.openBlCheck)
		self.runButton.configure(buttonOptions)
		self.runButton.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
		self.runButton.focus()

		self.cancelButton = tk.Button(self.buttonFrame, text="Cancel", command=blunderOff)
		self.cancelButton.configure(buttonOptions)
		self.cancelButton.grid(row=1, column=0, padx=5, pady=5, sticky='ew')

		self.depthLabel = tk.Label(self.settingFrame, text="Depth")
		self.depthLabel.grid(row=0, column=1, sticky='e')
		self.depthEntry = tk.Entry(self.settingFrame)
		self.depthEntry.grid(row=0, column=2, sticky='w')
		self.depthEntry.insert('0', self.defaults['depth'])

		self.timeLabel = tk.Label(self.settingFrame, text="Time")
		self.timeLabel.grid(row=1, column=1, sticky='e')
		self.timeEntry = tk.Entry(self.settingFrame)
		self.timeEntry.grid(row=1, column=2, sticky='w')
		self.timeEntry.insert('0', self.defaults['time'])

		self.threshLabel = tk.Label(self.settingFrame, text="Threshold")
		self.threshLabel.grid(row=2, column=1, sticky='e')
		self.threshEntry = tk.Entry(self.settingFrame)
		self.threshEntry.grid(row=2, column=2, sticky='w')
		self.threshEntry.insert('0', self.defaults['threshold'])

		self.begMoveLabel = tk.Label(self.settingFrame, text="Begin Move")
		self.begMoveLabel.grid(row=3, column=1, sticky='e')
		self.begMoveEntry = tk.Entry(self.settingFrame)
		self.begMoveEntry.grid(row=3, column=2, sticky='w')
		self.begMoveEntry.insert('0', self.defaults['begMove'])

		self.endMoveLabel = tk.Label(self.settingFrame, text="End Move")
		self.endMoveLabel.grid(row=4, column=1, sticky='e')
		self.endMoveEntry = tk.Entry(self.settingFrame)
		self.endMoveEntry.grid(row=4, column=2, sticky='w')
		self.endMoveEntry.insert('0', self.defaults['endMove'])		

	def openBlCheck(self, e=None):
		self.runButton.configure(state='disabled')
		time = self.timeEntry.get()
		depth = self.depthEntry.get()
		thresh = self.threshEntry.get()
		begMove = self.begMoveEntry.get()
		endMove = self.endMoveEntry.get()

		time = int(time) if self.isInteger(time) else None
		depth = int(depth) if self.isInteger(depth) else None
		thresh = int(thresh) if self.isInteger(thresh) else None
		begMove = int(begMove) if self.isInteger(begMove) else 1
		endMove = int(endMove) if self.isInteger(endMove) else None

		threading.Thread(
			target=self.blunderChk, 
			kwargs=dict(depth=depth, time=time, blunderThresh=thresh, begMove=begMove, endMove=endMove),
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
	def blunderChk(self, begMove=1, endMove=None, blunderThresh=50, depth=5, time=None):
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
			if self.gui.isBlunderCheck == False: 
				print("Blunder Check Terminated")
				self.blWindow.destroy()
				return

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

	# after blundercheck has complete update gui and internal variables
	def updateGUI(self, game):
		self.gui.curNode = self.gui.nodes[0]
		self.gui.game = game
		# populating the text widget is wicked slow if it's visible
		self.gui.gameScore.pack_forget()
		self.gui.game.accept(gameScoreVisitor(self.gui))
		self.gui.gameScore.pack(anchor='n', expand=True, fill='both')
		self.gui.printCurrentBoard()
		self.gui.printVariations()
		self.blWindow.destroy()
