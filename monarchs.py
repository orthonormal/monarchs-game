import argparse
from collections import Counter
from hexalattice.hexalattice import *
import matplotlib.pyplot as plt
import numpy as np
import pickle
import random

class Hex:
	def __init__(self, coordinates=None, neighbors=[], 
				 allegiance=None, base=False, regiments=Counter({'r':0,'g':0,'b':0}),
				 boost = {'r':False, 'g':False, 'b':False}
				):
		self.coordinates=coordinates
		self.neighbors=neighbors
		self.allegiance=allegiance
		self.base=base
		self.regiments=regiments
		self.boost=boost

def hex_name(hextup=(0,0),radius=0):
	if 4*radius + 1 > 26:
		print("That hex is too big")
		assert 0 == 1
	return chr(ord('A') + hextup[0] + 2*radius) + str(hextup[1] + radius + 1)

def hex_coord(hexname, radius=0):
	try:
		return (ord(hexname[0]) - ord('A') - 2*radius, int(hexname[1:]) - radius - 1)
	except:
		print(f"Invalid hexname: {hexname}")
		return None      
		
def hex_distance(x, y):
	# moving up or down gets you one space closer each time
	horizontal_remainder = max(0, (abs(x[0] - y[0]) - abs(x[1] - y[1]))/2)
	return abs(x[1] - y[1]) + horizontal_remainder

def allegiance(x, y):
	nation = None
	regiments = Counter({'r':0,'g':0,'b':0})

	if x + y <= 0 and y > x:
		nation = 'r'
		if x + y == 0 or y == x + 2:
			regiments['r'] += 2
	if y > -x and y >= 0:
		nation = 'g'
		if y == 0 or y == 2 - x:
			regiments['g'] += 2
	if y < 0 and y <= x:
		nation = 'b'
		if y == -1 or y == x:
			regiments['b'] += 2
	if hex_distance((x,y),(0,0)) == 1: # extra troops adjacent to the center
		regiments[nation] += 1
	return {'nation':nation,'regiments':regiments}

# Inputs
def input_moves(nation):
	moves = {}
	print("Are you boosting any hex? Enter hex if so, otherwise type NO.")
	x = input()
	if x != 'NO':
		moves['boost'] = x
	print("Type END when there are no more moves to enter.")
	while True:
		print("Where does the move begin?")
		begin = input()
		if begin == 'END':
			break
		print("Where does the move end?")
		end = input()
		print(f"How many units are you moving from {begin} to {end}?")
		try:
			num = int(input())
		except:
			print("Not an integer")
			continue
		print(f"Please confirm with YES: is {nation} moving {num} units from {begin} to {end}?")
		if input() != 'YES':
			print("Try entering the move again.")
			continue
		moves[(begin,end)] = num
	return moves
	
def input_true_allegiances():
	allegiances = {}
	done = False
	while not done:
		done = True
		allegiances = {'r':{}, 'g':{}, 'b':{}}
		for n in ['r', 'g', 'b']:
			double_check = Counter()
			for i in range(5):
				print(f"Enter the next courtier in the {n} court, followed by their true allegiance.")
				courtier = input()
				allegiant = input()
				allegiances[n][courtier] = allegiant
				double_check[allegiant] += 1
			if set(double_check.keys()) != set(['r', 'g', 'b']) or double_check[n] != 3 or len(set(allegiances[n].keys())) != 5:
				done = False
				print(f"Invalid entries for {n}; try again")
				break
	return allegiances

def input_guesses(courtier_list, nation):
	guesses = {}
	print(f"Your courtiers are {courtier_list}.")
	for n in ['r', 'g', 'b']:
		if n == nation:
			continue
		while True:
			print(f"Who do you think is the spy for {n}?")
			spy = input()
			if spy in courtier_list:
				guesses[spy] = n
				break
			print("Please type in the name as it appears above.")
	return guesses

# Scoring
def nation_scores(score_dict, last_turn=False):
	nation_scores = {}
	turns = sorted(score_dict.keys())
	if last_turn:
		turns.append(turns[-1]) # last round counts double
	for n in ['r', 'g', 'b']:
		nation_scores[n] = sum([score_dict[t][n]['total'] for t in turns])
	return nation_scores

def final_scores(score_dict, monarch_guesses, true_allegiance):
	# monarch_guesses of form {'r':{'steve':'b', 'eve':'g'}, etc}
	natscores = nation_scores(score_dict, last_turn=True)
	print(f"Nation scores: {natscores}")
	
	monarch_scores = Counter({'r':natscores['r'], 'g':natscores['g'], 'b':natscores['b']})
	courtier_scores = Counter()
	turns = len(score_dict.keys())

	for n in ['r', 'g', 'b']:
		for k in monarch_guesses[n].keys():
			if monarch_guesses[n][k] == n:
				continue # only looking for traitors
			if monarch_guesses[n][k] == true_allegiance[n][k]: # monarchs need to identify traitor's true allegiance
				monarch_scores[n] += 5
	print(f"Monarch scores: {monarch_scores}")

	for n in ['r', 'g', 'b']:
		for k in true_allegiance[n].keys():
			if true_allegiance[n][k] == n:
				courtier_scores[k] = monarch_scores[n] - 18*turns
			else:
				courtier_scores[k] = 2*monarch_scores[true_allegiance[n][k]] - monarch_scores[n] - 19*turns
			if k in monarch_guesses[n][k] and monarch_guesses[n][k] != n: # if accused of treason
				courtier_scores[k] // 2

	courtier_list = list(courtier_scores.items())
	np.random.shuffle(courtier_list)
	courtier_list.sort(key=lambda x: -x[1])
	print(courtier_list)

	# (random) top scorer is a winner, all others go into a lottery
	courtiers = [i for i in courtier_list[1:]]
	tickets = [max(0,i[1])**2 for i in courtier_list[1:]]
	weights = [t/sum(tickets) for t in tickets]
	winners = np.random.choice(courtiers, size=2,replace=False, p=weights)
	return [courtier_list[0]] + list(winners)

class Monarchs:
	def make_hexes(self):
		for y in range(-self.radius, self.radius + 1):
			for x in range(-2*self.radius + abs(y), 2*self.radius - abs(y) +1, 2):
				new_neighbors = []
				for house in [(x-2,y),(x-1,y-1),(x+1,y-1)]:
					if house in self.hexes:
						new_neighbors.append(house)
						self.hexes[house].neighbors.append((x,y))
				newhex = Hex(coordinates=(x,y), boost = {'r':False, 'g':False, 'b':False},
							 neighbors=new_neighbors, allegiance=allegiance(x,y)['nation'], 
							 base=False, regiments=allegiance(x,y)['regiments'])
				self.hexes[(x,y)] = newhex
							 
		for n in ['r', 'g', 'b']:
			base = self.bases[n]
			self.hexes[base].base = True
			self.hexes[base].regiments[n] += 5 #start 5 units at home
						
	def __init__(self, radius=4, loadfile=None, savepath=''): # can load a pickled saved state
		if loadfile:
			with open(loadfile, "rb") as f:
				loadstate = pickle.load(f)
				f.close()
			self.savepath = loadstate['savepath']
			self.radius = loadstate['radius']
			assert self.radius == radius
			self.hexes = loadstate['hexes']
			self.bases = loadstate['bases']
			self.moves = loadstate['moves']
			self.turn = loadstate['turn']
			self.scores = loadstate['scores']
			self.wl = loadstate['wl']
		else:
			self.savepath = savepath
			self.radius = radius
			self.hexes = {}
			self.bases = {'r':(-2*self.radius, 0),'g':(self.radius, self.radius),'b':(self.radius, -self.radius)}
			self.moves = {}
			self.turn = 1
			self.scores = {}
			self.wl = {'r':{'w':[], 'l':[]}, 'g':{'w':[], 'l':[]}, 'b':{'w':[], 'l':[]}}

			self.make_hexes()
		
	def receive_orders(self, nation, order_dict):
		# initiate all valid moves from that nation, in wait of battle
		# format is e.g. {'boost':Q4, ('A6','B5'):2} to boost Q4 and move 2 units from A6 to B5
		self.moves[nation] = Counter()
		regs = Counter()
		for k in order_dict.keys():
			try:
				if k == 'boost':
					h = hex_coord(order_dict['boost'], self.radius)
					if not h or h not in self.hexes:
						print(f"Invalid hex for move 'boost:{order_dict['boost']}'")
						continue
					self.hexes[h].boost[nation] = True
					self.moves[nation]['boost'] = order_dict['boost']
					continue
				origin = hex_coord(k[0], self.radius)
				destination = hex_coord(k[1], self.radius)
				# check that these exist on the board
				if not origin or origin not in self.hexes:
					print(f"Invalid origin hex for move '{k}:{order_dict[k]}'")
					continue
				if not destination or destination not in self.hexes:
					print(f"Invalid destination hex for move '{k}:{order_dict[k]}'")
					continue
				# check that it's a positive integer of regiments
				if type(order_dict[k]) != int or order_dict[k] < 1:
					print(f"Invalid number of regiments moved: {order_dict[k]}")
					continue
				# check the distance of the move
				if hex_distance(origin, destination) != 1:
					print(f"Invalid move distance of {hex_distance(origin, destination)} from {k[0]} to {k[1]}")
					continue
				# make sure they're not inventing extra units            
				regs[k[0]] += order_dict[k]
				if regs[k[0]] > self.hexes[hex_coord(k[0], self.radius)].regiments[nation]: 
					print(f"Too many units leaving hex {k[0]} by move '{k}:{order_dict[k]}'")
					continue
				self.moves[nation][(k[0], k[1])] = order_dict[k]
			except:
				print(f"Unforeseen exception on input: '{k}:{order_dict[k]}'")
				raise
						
	
	def battle(self, battle_dict, battle_hex=None):
		# given the set of divisions in a location (edge or hex), decide the winner
		top_strength = -1
		top_army = None
		for n in battle_dict.keys():
			if battle_dict[n] == 0:
				continue
			strength = battle_dict[n] + random.random()
			if battle_hex:
				if battle_hex.allegiance == n:
					strength + 0.25
				if battle_hex.boost[n]:
					strength + 0.5
			if strength > top_strength:
				top_strength = strength
				top_army = n
		return top_army
		
	def border_battles(self):
		# border battle winner moves, border battle loser doesn't
		edges = {}
		for n in self.moves.keys():
			for m in self.moves[n].keys():
				if type(m) != tuple:
					continue
				e = tuple(sorted([m[0], m[1]]))
				if e not in edges:
					edges[e] = Counter()
				edges[e][n] += self.moves[n][m]


		for e in edges.keys():
			v = self.battle(edges[e])
			if len(edges[e].keys()) > 1:
				print(f"{v} wins skirmish on {e} border")
			for n in ['r','g','b']:
				if n == v:
					self.hexes[hex_coord(e[0], self.radius)].regiments[n] += self.moves[n][(e[1],e[0])] - self.moves[n][(e[0],e[1])]
					self.hexes[hex_coord(e[1], self.radius)].regiments[n] += self.moves[n][(e[0],e[1])] - self.moves[n][(e[1],e[0])]
	
	def hex_battles(self):
		self.scores[self.turn] = {'r':Counter(), 'g':Counter(), 'b':Counter()}
		for h in self.hexes.values():
			v = self.battle(h.regiments, h)
			if not h.base and v is not None: # bases always win
				h.allegiance = v
			if h.allegiance is not None:
				self.scores[self.turn][h.allegiance]['hexes'] += 1
			if len([j for j in h.regiments.keys() if h.regiments[j] > 0]) > 1:
				self.wl[h.allegiance]['w'].append(hex_name(h.coordinates, self.radius))
				print(f"{h.allegiance} wins hex battle on {hex_name(h.coordinates, self.radius)}")
	
	def retreats(self, guidance={}):
		# first, losing armies lose a division back to home base
		for h in self.hexes.values():
			for nation in ['r','g','b']:
				homebase = self.hexes[self.bases[nation]]
				if nation != h.allegiance and h.regiments[nation] > 0:
					self.wl[nation]['l'].append(hex_name(h.coordinates, self.radius))
					self.scores[self.turn][h.allegiance]['victories'] += 1
					self.scores[self.turn][nation]['defeats'] += 1
					h.regiments[nation] -= 1
					homebase.regiments[nation] += 1

					# next, failed defenders retreat randomly toward their home base
					retreat_hex = None
					retreat_value = 5*self.radius
					for neigh in h.neighbors:
						if self.hexes[neigh].allegiance != nation:
							continue
						r = hex_distance(neigh, homebase.coordinates) + random.random()
						if r < retreat_value:
							retreat_hex = neigh
							retreat_value = r
					if retreat_hex is not None:
						self.hexes[retreat_hex].regiments[nation] += h.regiments[nation]
					else:
						# lose everything if there is no safe retreat hex
						homebase.regiments[nation] += h.regiments[nation]
						self.scores[self.turn][h.allegiance]['victories'] += h.regiments[nation]
						self.scores[self.turn][nation]['defeats'] += h.regiments[nation]
					h.regiments[nation] = 0
		for nation in ['r','g','b']:
			self.scores[self.turn][nation]['total'] = (2*self.scores[self.turn][nation]['victories'] - 
													   2*self.scores[self.turn][nation]['defeats'] + 
													   self.scores[self.turn][nation]['hexes'])
	
	def check(self):
		print("Checking for errors")
		tot_regs = Counter()
		tot_boost = Counter()
		for h in self.hexes.values():
			for n in ['r', 'g', 'b']:
				if n != h.allegiance and h.regiments[n] != 0:
					print(f"Error: hex {hex_name(h.coordinates, self.radius)} has allegiance {h.allegiance} but contains regiments from {n}")
				tot_regs[n] += h.regiments[n]
			for k in h.boost.keys():
				if h.boost[k]:
					tot_boost[k] += 1
		for n in ['r', 'g', 'b']:
			if tot_regs[n] != 7 + 4 *self.radius:
				print(f"Error: nation {n} has {tot_regs[n]} total regiments; {7 + 4 *self.radius} expected")
			if tot_boost[n] > 1:
				print(f"Error: nation {n} has {tot_boost[n]} boosts")
	
	def make_maps(self, nation='all', savepath=None, show=False):
		print("Making maps")
		colors = []
		names = []
		regiments = []
		hexsort = list(self.hexes.values())
		hexsort.sort(key=lambda x: x.coordinates[0])
		hexsort.sort(key=lambda x: x.coordinates[1])
		for h in hexsort:
			names.append(hex_name(h.coordinates, self.radius))
			if nation != 'all' and h.allegiance != nation:
				if nation not in [self.hexes[neigh].allegiance for neigh in h.neighbors]:
					regiments.append(" ")
					colors.append([0.75, 0.75, 0.75])
					continue
			regs = " "
			for n in ['r','g','b']:
				if h.regiments[n] > 0:
					regs += f"{h.regiments[n]}{n} "
			regiments.append(regs)
			if h.allegiance == 'r':
				colors.append([1, 0.65, 0.65])
			elif h.allegiance == 'g':
				colors.append([0.65, 1, 0.65])
			elif h.allegiance == 'b':
				colors.append([0.65, 0.75, 1])
			else:
				colors.append([1, 1, 1])

		h_fig = plt.figure(figsize=(15, 15))
		h_ax = h_fig.add_axes([0.05, 0.05, 0.9, 0.9])
		hex_centers, _ = create_hex_grid(n=10*(self.radius**2 + 1), crop_circ=self.radius +.1, min_diam=1, 
										 face_color=np.array(colors), do_plot=True, h_ax=h_ax)
		centers_x = hex_centers[:, 0]
		centers_y = hex_centers[:, 1]

		for i in range(len(centers_x)):
			plt.text(centers_x[i], centers_y[i]+0.25, names[i], ha='center')
			plt.text(centers_x[i], centers_y[i]-0.1, str(regiments[i]), ha='center')
		
		plt.figtext(0.5, 0.85, f"Turn {self.turn}, {nation}", ha="center", fontsize=24)
		if nation != 'all':
			nvic = self.wl[nation]['w']
			nlos = self.wl[nation]['l']
			nsco = self.scores[self.turn][nation]['total']
			plt.figtext(0.5, 0.1, f"Victories on {nvic}\nDefeats on {nlos}\nScore for turn: {nsco}", ha="center", fontsize=18)

		plt.axis('off')
		if savepath is not None:
			plt.savefig(savepath+f"{nation}_{self.turn}.png", format='png')

		if show:
			plt.show()
		
	# save past states as json
	# can reload / start a new instance from file
	def save_turn(self, savepath=None):
		print("Saving game state")
		gamestate = {'savepath':self.savepath, 'radius':self.radius, 'hexes':self.hexes, 'bases':self.bases, 'moves':self.moves, 
					 'turn':self.turn, 'scores':self.scores, 'wl':self.wl}
		if savepath:
			savefile = savepath+f"turn_{self.turn}.txt"
		else:
			savefile = self.savepath+f"turn_{self.turn}.txt"
		with open(savefile, "wb") as f:
			pickle.dump(gamestate, f)
			f.close
			
	def finish_turn(self):
		print("Resetting variables")
		self.moves = {}
		for h in self.hexes.values():
			h.boost = {'r':False, 'g':False, 'b':False}
		self.wl = {'r':{'w':[], 'l':[]}, 'g':{'w':[], 'l':[]}, 'b':{'w':[], 'l':[]}}
		self.turn += 1
	
	def run_turn(self, savepath=None, show_maps=False):
		if not savepath:
			savepath = self.savepath
		self.border_battles()
		self.hex_battles()
		self.retreats()
		self.check()
		self.save_turn()
		for n in ['r', 'g', 'b', 'all']:
			self.make_maps(nation=n, savepath=savepath, show=show_maps)
		self.finish_turn()

""" 
Usage: 
python monarchs.py --new <path_to_folder> <-- starts a new game (overwriting anything in folder!)
python monarchs.py --load <path_to_save_state>  <-- reloads game from save state
"""

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Run a game of Monarchs.')
	parser.add_argument('--new', type=str, help='The directory for a new game (this will overwrite files)')
	parser.add_argument('--load', type=str, help='This reloads a game from the designated file')
	parser.add_argument('--r', type=int, default=4, help='The radius of the game')
	args = parser.parse_args()

	if args.load:
		game = Monarchs(loadfile=args.load)
	elif args.new:
		game = Monarchs(savepath=args.new, radius=args.r)
	else:
		print("Requires either a directory for a new game or a savefile from an existing one.")
		assert False

	ongoing = True
	while ongoing:
		print(f"Beginning of turn {game.turn}")
		while True:
			print("Do you have any moves left to enter? Type in the nation or type NO.")
			nation = input()
			if nation == 'NO':
				break
			if nation in ['r', 'g', 'b']:
				game.receive_orders(nation, input_moves(nation))
			else:
				print("That is not an acceptable answer.")
		print(game.moves)
		game.run_turn()
		print(f"Nation scores: {nation_scores(game.scores)}")

		while True:
			print("Was this the final turn? Type YES or NO.")
			ongoing = False
			final = input()
			if final == 'YES':
				print("Enter true allegiances.")
				trues = input_true_allegiances()
				guesses = {}
				for n in ['r', 'g', 'b']:
					print(f"Enter guesses from the {n} monarch.")
					guesses[n] = input_guesses(list(trues[n].keys()),n)
				print(f"Winning courtiers: {final_scores(game.scores, guesses, trues)}")
				break
			if final == 'NO':
				break










