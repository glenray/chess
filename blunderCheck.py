import asyncio
import chess.pgn
import chess.engine
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font
from tkinter import scrolledtext
# import pdb
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
		def blunderOff(e):
			self.gui.isBlunderCheck = False
			varPop.destroy()
		varPop = tk.Toplevel(self.gui.root)
		varPop.title("Blunder Check")
		varPop.bind("<Escape>", blunderOff)
		varPop.focus_force()

		label = tk.Label(varPop, text="Blunder Check", pady=10)
		label.pack()

	def blunderChk(self, begMove=1, endMove=None, blunderThresh=50, depth=23):
		self.blunderWin()
		node = self.game.variation(0)
		saveInfo = False
		while True:
			# check if blundercheck toogled off
			if self.gui.isBlunderCheck == False: 
				print("Blunder Check Terminated")
				break

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

			if isBestMate and not isActualMate:
				isBlunder = True
				blunderWarning = f"{moveTxt} was a blunder: {txtOnMove} missed mate in {bestScore.mate()}"
			elif not isBestMate and isActualMate:
				isBlunder = True
				blunderWarning = f"{moveTxt} was a blunder: {txtOnMove} allows mate in {abs(actualScore.mate())}. Better is {parentBoard.san(saveInfo['pv'][0])} ({bestScore.score()})"
			elif blunderMargin and (abs(blunderMargin) > blunderThresh):
				isBlunder = True
				blunderWarning = f"{moveTxt} ({actualScore.score()/100}) was a blunder: {blunderMargin/100} pawns. Better is {parentBoard.san(saveInfo['pv'][0])} ({bestScore.score()/100})"
			else:
				isBlunder = False
				blunderWarning = ''

			# Regardless of score, it's not a blunder if the best move and the actual move are the same.
			if saveInfo['pv'][1] == info['pv'][0]:
				isBlunder = False

			if isBlunder:
				print(blunderWarning)
			else:
				print(moveTxt)

			if node.is_end(): break
			saveInfo = info
			node = node.variation(0)
