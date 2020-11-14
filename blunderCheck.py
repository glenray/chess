import asyncio
import chess.pgn
import chess.engine
import copy
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
		def blunderOff(e=None):
			self.gui.isBlunderCheck = False
		self.blWindow = tk.Toplevel(self.gui.root)
		self.blWindow.title("Blunder Check")
		self.blWindow.bind("<Escape>", blunderOff)
		self.blWindow.focus_force()
		# make window modal
		self.blWindow.grab_set()

		self.label = tk.Label(self.blWindow, text="Blunder Check", pady=10)
		self.label.pack()

		self.blText = tk.Text(self.blWindow, width=80)
		self.blText.pack(anchor='n', expand=True, fill='both')

		self.buttonFrame = tk.Frame(self.blWindow)
		self.buttonFrame.pack(fill='x')

		self.cancelButton = tk.Button(self.buttonFrame, text="Cancel", command=blunderOff)
		self.cancelButton.pack(anchor='w')

	def blunderChk(self, begMove=1, endMove=None, blunderThresh=50, depth=23):
		self.blunderWin()
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
