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

    def find_card_type(self, search_for_card):
        if search_for_card in self.cardtypes:
            return search_for_card
        else:
            matched_card = None
            for card in self.cardtypes:
                if search_for_card.lower() in card.lower():
                    if matched_card is None:
                        matched_card = card
                    else:
                        # more than 1 card type that lazily matches
                        if matched_card != card:
                            return None
            return matched_card
    
    def draw(self, numcards=1):
        drawn = []
        for i in range(numcards):
            drawn = drawn + [self._cards.pop()]
        return drawn
    
    def return_cards(self, cardlist):
        self._cards = self._cards + cardlist
    
    def return_card(self, card):
        self._cards.append(card)

