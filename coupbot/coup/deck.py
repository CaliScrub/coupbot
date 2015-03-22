import sys
import random

cardtype_shorthand = {
    'Duke': 'DU',
    'Assassin': 'AS',
    'Contessa': 'CO',
    'Captain': 'CA',
    'Ambassador': 'AM',
}

cardtypes = ['Duke', 'Assassin', 'Contessa', 'Captain', 'Ambassador']

def find_card_type(search_for_card):
    if search_for_card in cardtypes:
        return search_for_card
    else:
        matched_card = None
        for card in cardtypes:
            if search_for_card.lower() in card.lower():
                if matched_card is None:
                    matched_card = card
                # more than 1 card type that lazily matches
                elif matched_card != card:
                    return None
        return matched_card

class Deck(object):
    def __init__(self, playercount=6):
        self._playercount = playercount
        self._cards = []
        cards_per_type = 3
        if playercount >= 9:
            cards_per_type = 5
        elif playercount >= 7:
            cards_per_type = 4
        for cardtype in cardtypes:
            self._cards = self._cards + ([cardtype] * cards_per_type)
        random.shuffle(self._cards)
    
    def shuffle(self):
        random.shuffle(self._cards)
    
    def draw(self, numcards=1):
        drawn = []
        for i in range(numcards):
            drawn = drawn + [self._cards.pop()]
        return drawn
    
    def return_cards(self, cards):
        if isinstance(cards, tuple) or isinstance(cards, list):
            self._cards = self._cards + list(cards)
        else:
            self._cards.append(cards)

