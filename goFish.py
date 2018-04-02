import random

class Player(object):
	def __init__(self, id, method):
		self.id = id
		self.score = 0
		self.hand = []
		self.matches = []

		self.method = method
		self.game_state = [0 for x in range(13)]
		self.cards_number = [7, 7, 7, 7]	# cards each player has
		self.cards_in_pile = 24	# cards remain in pile

		self.cards_max = [[0 for x in range(13)] for x in range(4)]
		self.cards_min = [[0 for x in range(13)] for x in range(4)]
		
		self.cards_unknown = 45 # cards have not been called yet

	def playTurn(self, players, deck, turn):
		another_turn = False

		# action: [requested Player, card value]
		if self.method == "Random":
			action = self.Random(players, deck, turn)
		elif self.method == "Greedy":
			action = self.Greedy(players, deck, turn) 
		elif self.method == "Search":
			action = self.Search(players, deck, turn)
		elif self.method == "Learning":
			action = self.Learning(players, deck, turn)

		# request card from player requestedPlayer
		print (self.id, "is requesting from player ", action[0].id, "the card value of", action[1])
		
		result = self.requestCard(action[0], action[1])
		if result == True:
			while result == True:
				result = self.requestCard(action[0], action[1])
		else:
			#another turn if get card it wants
			if len(deck.deck) > 0:
				self.goFish(deck)
				print (self.id, "went fish")
				if self.hand[-1].value == action[1]:
					print (self.id, "gets another turn")
					another_turn = True
			else:
				print (self.id, "passed")
		
		self.findMatches()
		return another_turn

	def Random(self, players, deck, turn):
		card = random.randrange(0, len(self.hand))	# will find a random card index from player's hand to request

		requestedPlayer = -1 # will find a random player from which to requ·est a card value
		while requestedPlayer < 0 or requestedPlayer == turn:
			requestedPlayer = random.randrange(0, 4)

		action = [players[requestedPlayer], self.hand[card].value]
		return action
	
	def Greedy(self, players, deck, turn):
		action = [players[0], 0]
		return action
	
	def Search(self, players, deck, turn):
		action = [players[0], 0]
		return action
	
	def Learning(self, players, deck, turn):
		action = [players[0], 0]
		return action

	# hand over all cards of that rank
	def requestCard(self, player2, value):
		for card in range(len(player2.hand)): 
			if player2.hand[card].value == value:
				temp = player2.hand[card]
				player2.hand[card] = player2.hand[len(player2.hand)-1]
				player2.hand.pop()
				
				self.hand.append(temp)
				print (self.id, " gets", temp.suit, temp.value)
				return True

		return False

	# draw one card from the pile
	def goFish(self, deck):
		self.hand.append(deck.deck[len(deck.deck)-1])
		deck.deck.pop()

	def drawHand(self, deck):
		for i in range(0, 7):
			self.goFish(deck)
		matches = self.findMatches()
		while matches == True:
			matches = self.findMatches()

	# collect entire suits -> discard
	def findMatches(self): # will find matches in self's hand. 
		for i in range(len(self.hand)):
			num_of_rank = 1
			pos_of_cards = [i, 0, 0, 0]
			for j in range(len(self.hand)):
				if i == j:
					continue
				elif self.hand[i].value == self.hand[j].value:
					pos_of_cards[num_of_rank] = j
					num_of_rank = num_of_rank + 1

			if num_of_rank == 4:
				print (self.id, " gets four cards at same rank: ", self.hand[i].value)
				self.score += 1
				self.discardMatch(pos_of_cards)
				return True
		return False

	def printHand(self):
		for i in range(0, len(self.hand)):
			print (self.hand[i].value + " of " + self.hand[i].suit)

	# discard four cards every time
	def discardMatch(self, pos_of_cards):
		self.printHand()

		self.matches.append(self.hand[pos_of_cards[0]])
		self.matches.append(self.hand[pos_of_cards[1]])
		self.matches.append(self.hand[pos_of_cards[2]])
		self.matches.append(self.hand[pos_of_cards[3]])
		print ("DISCARDING:", self.hand[pos_of_cards[0]].value, self.hand[pos_of_cards[0]].suit)
		print ("DISCARDING:", self.hand[pos_of_cards[1]].value, self.hand[pos_of_cards[1]].suit)
		print ("DISCARDING:", self.hand[pos_of_cards[2]].value, self.hand[pos_of_cards[2]].suit)
		print ("DISCARDING:", self.hand[pos_of_cards[3]].value, self.hand[pos_of_cards[3]].suit)

		# four cards -> tail
		self.hand.remove(self.hand[pos_of_cards[3]])
		self.hand.remove(self.hand[pos_of_cards[2]])
		self.hand.remove(self.hand[pos_of_cards[1]])
		self.hand.remove(self.hand[pos_of_cards[0]])

class Deck(object):

	def __init__(self):
		values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
		suits = ['Hearts', 'Diamonds', 'Spades', 'Clubs']
		deck = []
		for suit in range(0, 4):
			for value in range(0,13):
				deck.append(Card(values[value], suits[suit]))
		self.deck = deck

	def shuffle(self):
		for i in range(0,1000):
			idx1 = random.randrange(0, 52)
			idx2 = random.randrange(0, 52)
			while(idx1 == idx2):
				idx1 = random.randrange(0, 52)
				idx2 = random.randrange(0, 52)
			self.swap(idx1, idx2, self.deck)
		return self.deck

	def swap(self, i, j, arr):
		temp = arr[i]
		arr[i] = arr[j]
		arr[j] = temp

	def printDeck(self):
		for i in range(0, len(self.deck)):
			print (self.deck[i].value + " of " + self.deck[i].suit)

class Card(object):
	def __init__(self, value, suit):
		self.value = value
		self.suit = suit

def createPlayers(deck):
	player0 = Player(0, 'Random')
	player1 = Player(1, 'Random')
	player2 = Player(2, 'Random')
	player3 = Player(3, 'Random')
	player1.drawHand(deck)
	player2.drawHand(deck)
	player3.drawHand(deck)
	player0.drawHand(deck)
	players = [player0, player1, player2, player3]
	return players

def printResults(players):
	maxScore = players[0]
	for i in range(1, len(players)):
		if players[i].score > maxScore.score:
			maxScore = players[i]
	print (maxScore.id, " wins with a score of ", maxScore.score)
	for player in players:
		print ("player ", player.id, " currently holds:")
		player.printHand()




def playGame():
	newDeck = Deck()
	newDeck.shuffle()
	players = createPlayers(newDeck)
	turn = 0

	while len(players[0].hand) > 0 and len(players[1].hand) > 0 and len(players[2].hand) > 0 and len(players[3].hand) > 0:
			another_turn = players[turn].playTurn(players, newDeck, turn)
			if another_turn == False:
				turn = (turn + 1) % 3

	printResults(players)


playGame()
