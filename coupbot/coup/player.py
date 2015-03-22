import sys
import deck

class Player(object):
    
    def __init__(self, name):
        self.name = name
        self.wins = 0
        self.clear_for_start()

    def clear_for_start(self):
        self._cards = []
        self._dead_cards = []
        self._ambass_cards = []
        self._money = 2

    def status_check(self):
        livecardlist = str.join(', ', self._cards)
        deadcardlist = str.join(', ', self._dead_cards)
        return 'Your live cards are: %s; your dead cards are: %s, you have %s coin(s)' % (livecardlist, deadcardlist, self._money)

    def public_status_check(self, shortform=True):
        deadcardlist = str.join(', ', self._dead_cards)
        if self.is_dead():
            if shortform:
                deadtext = str.join(' ', [deck.cardtype_shorthand[card] for card in self._dead_cards])
                status = '%s (DEAD): %s' % (self.name, deadtext)
            else:
                status = '%s is dead with dead cards: %s' % (self.name, deadcardlist)
        else:
            if shortform:
                livelist = ['??' for card in self._cards]
                deadlist = [deck.cardtype_shorthand[card] for card in self._dead_cards]
                cardlist = livelist + deadlist
                cardtext = str.join(' ', cardlist)
                status = '%s: %s, $%s' % (self.name, cardtext, self._money)
            else:
                status = '%s is alive with dead cards: %s; and %s coin(s)' % (self.name, deadcardlist, self._money)
        return status

    def has_card_type(self, cardtype):
        return cardtype in self._cards

    def kill_card(self, cardtype):
        if self.has_card_type(cardtype):
            self._cards.remove(cardtype)
            self._dead_cards.append(cardtype)
            return True
        else:
            return False

    def live_card_count(self):
        return len(self._cards)

    def return_cardindex(self, index):
        return self.return_cardtype(self._cards[index])
    
    def return_cardtype(self, cardtype):
        self._cards.remove(cardtype)
        return cardtype
    
    def is_dead(self):
        return len(self._dead_cards) >= 2

    def add_win(self):
        self.wins = self.wins + 1

    def get_score(self):
        return '%s: %s win(s)' % [self.name, self.wins]

    def get_money(self):
        return self._money

    def add_money(self, money):
        self._money = self._money + money
        return self._money
    
    def take_money(self, money):
        if money > self._money:
            money = self._money
        self._money = self._money - money
        return money

    def pay_money(self, money):
        if money > self._money:
            return -1 # indicates cannot pay
        else:
            self._money = self._money - money
            return money

