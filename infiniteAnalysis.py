import threading, random, string
import chess
import chess.engine
import chess.pgn
from sqCanvas import strings

class infiniteAnalysis:
	def __init__(self, gui):
		self.gui = gui
		self.spawnEngine()

	# spawn a new engine thread when self.board changes 
	def spawnEngine(self):
		# generate random thread name
		threadName = "".join(random.choice(string.ascii_letters) for _ in range(10))
		self.gui.activeEngine = threadName
		threading.Thread(
			target=self.__engine, 
			args=(threadName,), 
			daemon=True).start()

	# Engine analyzing the current board
	# This is always run in a separate thread by self.spawnEngine()
	# tName str name of the thread
	# The thread running this engine will quit if it is no longer named
	# as the active engine in self.gui.activeEngine
	def __engine(self, tName):
		print(f"Engine {tName} On.")
		engine = chess.engine.SimpleEngine.popen_uci("C:/Users/Glen/Documents/python/stockfish/bin/stockfish_20090216_x64_bmi2.exe")
		with engine.analysis(self.gui.board) as analysis:
			for info in analysis:
				# if this is no longer the active engine, quit thread
				if self.gui.activeEngine != tName:
					print(f"Engine {tName} Off.")
					break

				pv = info.get('pv')
				if pv != None and (len(pv) > 5 or info.get("score").is_mate()):
					output = strings['permAnalysis'].format(
						score = info.get("score").white(),
						depth = info.get('depth'),
						nps = info.get('nps'),
						nodes = info.get('nodes'),
						time = info.get('time'),
						pvString = self.gui.board.variation_san(pv)	
					)
					self.gui.analysis.delete('0.0', 'end')
					self.gui.analysis.insert("0.1", output)
		engine.quit()
