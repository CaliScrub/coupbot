import sys
import random

class Deck(object):
    cardtypes = ['Duke', 'Assassin', 'Contessa', 'Captain', 'Ambassador']
    
    def __init__(self, playercount=6):
        self._playercount = playercount
        self._cards = []
        cards_per_type = 3
        if playercount >= 9:
            cards_per_type = 5
        elif playercount >= 7:
            cards_per_type = 4
        for cardtype in self.cardtypes:
            self._cards = self._cards + ([cardtype] * cards_per_type)
        random.shuffle(self._cards)
    
    def shuffle(self):
        random.shuffle(self._cards)
    
    def draw(self, numcards=1):
        drawn = []
        for i in range(numcards):
            drawn = drawn + [self._cards.pop()]
        return drawn
    
    def return_cards(self, cardlist):
        self._cards = self._cards + cardlist
    
    def return_card(self, card):
        self._cards.append(card)

