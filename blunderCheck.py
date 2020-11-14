import asyncio
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

	async def analyzePosition(self, board, depth):
		asyncio.set_event_loop_policy(chess.engine.EventLoopPolicy())
		transport, engine = await chess.engine.popen_uci(self.engines['Stockfish'])
		info = await engine.analyse(board, chess.engine.Limit(depth=depth))
		await engine.quit()
		return info

	def blunderWin(self):
		# Cancel button
		def blunderOff(e=None):
			self.gui.isBlunderCheck = False
			# if the blunder checker is not running, then destroy to window
			# returning contol to root
			# otherwise, the blunderChk method will destroy the window after terminating the thread.
			threadNames = [thread.name for thread in threading.enumerate()]
			if ("Blunder Checker" in threadNames) == False:
				self.blWindow.destroy()

		labelFont = font.Font(family="Tahoma", size=16)
		buttonFont = font.Font(family="Tahoma", size=12)
		textFont = font.Font(family="Courier", size=14)

		buttonOptions = {"pady":5, "padx":5, "overrelief":'sunken', "font":buttonFont}
		labelOptions = {"pady": 10, "font": labelFont}

		self.blWindow = tk.Toplevel(self.gui.root)
		self.blWindow.title("Blunder Check")
		self.blWindow.bind("<Escape>", blunderOff)
		self.blWindow.focus_force()
		# make window modal
		self.blWindow.grab_set()
		self.blWindow.grid_columnconfigure(0, weight=1)
		self.blWindow.grid_columnconfigure(1, weight=0)

		self.label = tk.Label(self.blWindow, text="Blunder Check")
		self.label.configure(labelOptions)
		self.label.grid(row=0, column=0)

		self.blText = tk.Text(self.blWindow, width=80, font=textFont, padx=10, pady=5)
		self.blText.grid(row=1, column=0, sticky='nsew', padx=10)

		self.buttonFrame = tk.Frame(self.blWindow)
		self.buttonFrame.grid(row=2, column=0)

		self.cancelButton = tk.Button(self.buttonFrame, text="Cancel", command=blunderOff)
		self.cancelButton.configure(buttonOptions)
		self.cancelButton.grid(row=0, column=1, padx=5, pady=5)

		self.runButton = tk.Button(self.buttonFrame, text="Run", command=self.start)
		self.runButton.configure(buttonOptions)
		self.runButton.grid(row=0, column=0, padx=5, pady=5)

	def start(self):
		threading.Thread(
			target=self.blunderChk, 
			kwargs=dict(depth=5, blunderThresh=50),
			name="Blunder Checker",
			daemon=True).start()

	def blunderChk(self, begMove=1, endMove=None, blunderThresh=50, depth=5):
		node = copy.deepcopy(self.game.variation(0))
		saveInfo = False
		while True:
			# check if blundercheck toogled off
			if self.gui.isBlunderCheck == False: 
				print("Blunder Check Terminated")
				self.blWindow.destroy()
				return

			moveNo = node.parent.board().fullmove_number
			if moveNo<begMove: 
				node = node.variation(0)
				continue
			if endMove != None and moveNo>endMove: break

			board = node.board()
			info = asyncio.run(self.analyzePosition(board, depth))

			# on first move, analyze the move before to get bestScore for the move
			if saveInfo == False:
				saveInfo = asyncio.run(self.analyzePosition(node.parent.board(), depth))

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
				line = node.parent.add_line(saveInfo['pv'], starting_comment=blunderWarning)
				self.blText.insert('end', f"{moveTxt} {blunderWarning}\n")
			else:
				self.blText.insert('end', moveTxt+"\n")
			self.blText.see('end')

			# update the GUI with the new game and quit
			if node.is_end(): 
				break
			else:
				saveInfo = info
				node = node.variation(0)
		# after breaking ot of loop, 
		self.blWindow.destroy()
		self.gui.blunderUpdate(node.game())
