import sys
import random
from collections import OrderedDict

class Deck(object):
    _cardtypes = ['Duke', 'Assassin', 'Contessa', 'Captain', 'Ambassador']
    _cards = []

    def __init__(self, playercount=6):
        self._playercount = playercount
        cards_per_type = 3
        if playercount >= 9:
            cards_per_type = 5
        elif playercount >= 7:
            cards_per_type = 4
        for cardtype in self._cardtypes:
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

class Player(object):
    _cards = []
    _dead_cards = []
    _ambass_cards = []
    _money = 0
    _wins = 0
    def __init__(self, name):
        self._name = name

    def clear_for_start(self):
        self._cards = []
        self._dead_cards = []
        self._ambass_cards = []
        self._money = 2

    def status_check(self):
        livecardlist = str.join(', ', self._cards)
        deadcardlist = str.join(', ', self._dead_cards)
        return 'Your live cards are: %s; your dead cards are: %s, you have %s money' % (livecardlist, deadcardlist, self._money)

    def public_status_check(self):
        deadcardlist = str.join(', ', self._dead_cards)
        if self.is_dead():
            status = '%s is dead with dead cards: %s' % (self._name, deadcardlist)
        else:
            status = '%s is alive with dead cards: %s; and %s money' % (self._name, deadcardlist, self._money)
        return status

    def has_card_type(self, cardtype):
        for heldtype in self._cards:
            if heldtype == cardtype:
                return True
        return False

    def kill_card(self, cardtype):
        if self.has_card_type(cardtype):
            self._cards.remove(cardtype)
            self._dead_cards.append(cardtype)
            return True
        else:
            return False

    def return_cardindex(self, index):
        return self.return_cardtype(self._cards[index])
    
    def return_cardtype(self, cardtype):
        self._cards.remove(cardtype)
        return cardtype
    
    def is_dead(self):
        return len(self._dead_cards) >= 2

    def add_win(self):
        self._wins = self._wins + 1

    def get_score(self):
        return '%s: %s win(s)' % [self._name, self._wins]

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

class Game(object):
    _players = OrderedDict()
    _deck = None
    _state = 'STARTING'
    _lastwinner = None
    _turnowner = None
    
    def __init__(self):
        self._state = 'STARTING'

    def clear_players(self):
        if not self.is_running():
            self._players = OrderedDict()
            self._lastwinner = None
            return 'All players gone!'
        else:
            return 'Cannot clear players in a running game'

    def get_next_turnowner(self):
        playernames = self._players.keys()
        index = playernames.index(self._turnowner)
        newindex = index + 1
        numtimesthrough = 0
        while numtimesthrough < len(playernames) and not newindex == index:
            if newindex >= len(playernames):
                newindex = 0
            newname = playernames[newindex]
            player = self.get_player(newname)
            if player is not None and not player.is_dead() and newname != self._turnowner:
                self._turnowner = newname
                return 'It is now %s\'s turn' % newname
            else:
                newindex = newindex + 1
        return 'Cannot find a new turn owner'
    
    def new_round(self):
        if not self.is_running():
            self._deck = Deck(len(self._players)) # reshuffle, plus add/remove for more/less players
            if len(self._players) < 2:
                return 'Not enough players, waiting for more...'
            elif len(self._players) > 10:
                return 'Too many players...'
            for player in self._players.values():
                player.clear_for_start()
                self.draw(player, numdraw=2)
                player._money = 2
            self._state = 'RUNNING'
            if self._lastwinner is None:
                playernames = self._players.keys()
                random.shuffle(playernames)
                self._turnowner = playernames[0]
            else:
                self._turnowner = self._lastwinner
            return 'New round has started! It is %s\'s turn' % self._turnowner
        else:
            return 'Cannot start new round now'

    def get_player(self, name):
        if self._players.has_key(name):
            return self._players[name]
        else:
            return None

    def get_score(self):
        scorelist = []
        for player in self._players.values():
            scorelist.append(player.get_score())
        return 'Win counts -- %s' % str.join(', ', scorelist)

    def add_player(self, name):
        if not self.is_running():
            if self._players.has_key(name):
                return '%s is already in the game' % name
            else:
                newplayer = Player(name)
                self._players[name] = newplayer
                return '%s has joined the game! %s players now.' % (name, len(self._players))
        else:
            return 'Game is not in a state to add players'
    
    def remove_player(self, name, force=False):
        if (not self.is_running()) or force:
            if self._players.has_key(name):
                self._players.pop(name)
                if self._state == 'RUNNING':
                    # clean up running state
                    None
                return '%s has left the game! %s players now.' % (name, len(self._players))
            else:
                return '%s wasn\'t in the game' % name
        else:
            return 'Game is not in a state to remove players'

    def list_players(self):
        return 'Players are seated in this order: %s' % self._players.keys()

    def random_reseat(self):
        if not self.is_running():
            playerlist = self._players.items()
            random.shuffle(playerlist)
            self._players = OrderedDict(playerlist)
            return 'Players have been reseated! %s' % self.list_players()
        else:
            return 'Players cannot change seats now'

    def get_public_status(self):
        result = ''
        statuses = []
        if self.is_running():
            for player in self._players.values():
                statuses.append(player.public_status_check())
            stattext = str.join('\r\n', statuses)
            result = 'It is %s\'s turn\r\nPublic stats: %s' % (self._turnowner, stattext)
        else:
            result = 'Game is not running'
        return result

    def quit_game(self):
        if self.is_running():
            self._state = 'DONE'
            return 'Quit game early!'
        else:
            return 'Game is not running'

    def draw(self, player, numdraw=1, amba_power=False):
        if (len(player._cards) + len(player._dead_cards)) >= 2:
            return
        else:
            drawn_cards = self._deck.draw(numdraw)
            player._cards = player._cards + drawn_cards

    def reveal(self, playername, cardtype):
        if self.is_running():
            player = self.get_player(playername)
            if player is None:
                return '%s is not playing the game' % playername
            else:
                if player.has_card_type(cardtype):
                    player.return_cardtype(cardtype)
                    self._deck.return_card(cardtype)
                    self._deck.shuffle()
                    self.draw(player)
                    return '%s has a %s! It was returned to the deck, and %s drew a new card from the reshuffled deck' % (playername, cardtype, playername)
                else:
                    return '%s does not have a %s!' % (playername, cardtype)
        else:
            return 'Game is not running'
    
    def get_private_status(self, playername):
        if self.is_running():
            player = self.get_player(playername)
            if player is None:
                return '%s is not playing the game' % playername
            else:
                return player.status_check()
        else:
            return 'Game is not running'

    def kill_influence(self, playername, cardtype):
        if self.is_running():
            player = self.get_player(playername)
            if player is None:
                return '%s is not playing the game' % playername
            if player.kill_card(cardtype):
                return '%s has chosen a %s to die' % (playername, cardtype)
            else:
                return '%s does not have a %s to sacrifice' % (playername, cardtype)
        else:
            return 'Game is not running'
    
    def income(self, playername):
        if self.is_running():
            player = self.get_player(playername)
            if player is None or player.is_dead():
                return '%s is not playing the game' % playername
            else:
                funds_after = player.add_money(1)
                return '%s gets income for 1 coin, now has %s coins' % (playername, funds_after)
        else:
            return 'Game is not running'

    def foreignaid(self, playername):
        if self.is_running():
            player = self.get_player(playername)
            if player is None or player.is_dead():
                return '%s is not playing the game' % playername
            else:
                funds_after = player.add_money(2)
                return '%s gets foreign aid for 2 coins, now has %s coins' % (playername, funds_after)
        else:
            return 'Game is not running'
    
    def steal(self, thief, victim):
        if self.is_running():
            thief_player = self.get_player(thief)
            victim_player = self.get_player(victim)
            if thief_player is not None and victim_player is not None and not thief_player.is_dead() and not victim_player.is_dead():
                stolen = victim_player.take_money(2)
                funds_after = thief_player.add_money(stolen)
                victim_funds = victim_player.get_money()
                return '%s stole %s coins from %s with their Captain, %s now has %s coins, %s has %s coins' % (thief, stolen, victim, thief, funds_after, victim, victim_funds)
            else:
                return 'Thief and victim need to be valid players'
        else:
            return 'Game is not running'

    def tax(self, name):
        if self.is_running():
            player = self.get_player(name)
            if player is not None and not player.is_dead():
                funds_after = player.add_money(3)
                return '%s taxes with their Duke for 3 coins, now has %s coins' % (name, funds_after)
            else:
                return '%s is not playing the game' % name
        else:
            return 'Game is not running'

    def admin_draw(self, playername, numdraw):
        if self.is_running():
            player = self.get_player(playername)
            if player is not None and not player.is_dead():
                drawn_cards = self._deck.draw(numdraw)
                player._cards = player._cards + drawn_cards
                return 'Admin has drawn %s cards for %s' % (numdraw, playername)
            else:
                return '%s is not playing the game' % playername
        else:
            return 'Game is not running'

    def admin_return_card(self, playername, index):
        if self.is_running():
            player = self.get_player(playername)
            if player is not None and not player.is_dead():
                returncard = player.return_cardindex(index)
                self._deck.return_card(returncard)
                return 'Admin has returned a cards for %s' % playername
            else:
                return '%s is not playing the game' % playername
        else:
            return 'Game is not running'
    
    def admin_add_money(self, playername, amt):
        if self.is_running():
            player = self.get_player(playername)
            if player is not None and not player.is_dead():
                funds_after = player.add_money(amt)
                return 'Admin has changed %s\'s coffers by %s coins, now has %s coins' % (playername, amt, funds_after)
            else:
                return '%s is not playing the game' % playername
        else:
            return 'Game is not running'

    def admin_shuffle(self):
        self._deck.shuffle()
        return 'Admin has shuffled the cards'

    def admin_see_deck(self):
        cards = self._deck._cards
        return 'Admin has asked to see the deck: %s' % str.join(', ', cards)

    def admin_see_deck_stats(self):
        cards = self._deck._cards
        cardstats = {}
        for card in cards:
            if cardstats.has_key(card):
                cardstats[card] = cardstats[card] + 1
            else:
                cardstats[card] = 1
        return 'Admin has asked to see deck stats: %s' % str(cardstats.items())
    
    def is_running(self):
        return self._state == 'RUNNING'
