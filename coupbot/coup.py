import sys
import random
from abc import abstractproperty, abstractmethod, ABCMeta # abstract base class
from collections import OrderedDict

#TODO: !pass, coup status should show list of waiters

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

    def public_status_check(self):
        deadcardlist = str.join(', ', self._dead_cards)
        if self.is_dead():
            status = '%s is dead with dead cards: %s' % (self.name, deadcardlist)
        else:
            status = '%s is alive with dead cards: %s; and %s coin(s)' % (self.name, deadcardlist, self._money)
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

    def kill_a_card(self):
        if len(self._cards) > 1:
            deadcard = self._cards.pop()
            self._dead_cards.append(deadcard)
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

class Action(object):
    __metaclass__ = ABCMeta
    def __init__(self, player):
        self.is_resolved = False
        if isinstance(player, Player):
            self.actor = player
        else:
            raise TypeError()
        self.target = None
        self.challenger = None
        self.only_target_can_block = True
        self.blocker = None
        self.was_blocked = False
        self.was_challenged = False
        self.waiting_for_kill = None
        self.state = 'START'
        self.name = 'BaseAction'
        self.status_message = 'Unresolved action'
    
    @abstractmethod
    def perform(self, victim=None):
        raise NotImplementedError()
    
    @abstractmethod
    def rollback(self):
        raise NotImplementedError()

    @abstractproperty
    def is_challengeable(self):
        raise NotImplementedError()
    
    @abstractproperty
    def is_blockable(self):
        raise NotImplementedError()
    
    @abstractproperty
    def card_needed(self):
        raise NotImplementedError()
    
    def challenge(self, challenger):
        """Challenges action. Returns None if can't be challenged, otherwise returns challenge success"""
        if isinstance(challenger, Player):
            self.challenger = challenger
        else:
            raise TypeError()
        if self.is_challengeable and not self.was_challenged and self.card_needed is not None:
            self.was_challenged = True
            if self.actor.has_card_type(self.card_needed):
                self.waiting_for_kill = self.challenger
                self.status_message = self.status_message + ' Challenged by %s, challenge was rebuffed.' % self.challenger.name
                return False
            else:
                self.waiting_for_kill = self.actor
                self.rollback() # roll back the action
                self.status_message = self.status_message + ' Challenged by %s, challenge was successful.' % self.challenger.name
                return True
        else:
            return None

    def get_status(self):
        params = {'name': self.name, 'stat_msg': self.status_message, 'state': self.state}
        statustext = 'Action: %(name)s -- State: %(state)s -- Note: %(stat_msg)s' % params
        return statustext

class Income(Action):
    def __init__(self, player):
        super(Income, self).__init__(player)
        self.name = 'Income'
        self.status_message = 'Unresolved income action.'

    def perform(self, victim=None):
        if not self.is_resolved:
            self.actor.add_money(1)
            self.is_resolved = True
            self.state = 'RESOLVED'
            self.status_message = 'Income gave 1 coin to %s who now has %s coins.' % (self.actor.name, self.actor.get_money())
            return True
        else:
            return False
    
    def rollback(self):
        return False
    
    @property
    def is_challengeable(self):
        return False
    
    @property
    def is_blockable(self):
        return False

    @property
    def card_needed(self):
        return None
    
class BlockForeignAid(Action):
    def __init__(self, player, target, blockedaction):
        super(BlockForeignAid, self).__init__(player)
        self.target = target
        self.name = 'Block foreign aid'
        self.blockedaction = blockedaction
        self.status_message = 'Foreign aid request by %(requestor)s was blocked by %(blocker)s\'s Duke' % { 'requestor': self.target.name, 'blocker': self.actor.name } 
        self.is_resolved = True

    def perform(self):
        raise NotImplementedError()

    def rollback(self):
        self.target.add_money(2) # readding the foreign aid
        self.blockedaction.was_blocked = False
        return True

    @property
    def is_challengeable(self):
        return True
    
    @property
    def is_blockable(self):
        return False

    @property
    def card_needed(self):
        return 'Duke'

class ForeignAid(Action):
    def __init__(self, player):
        super(ForeignAid, self).__init__(player)
        self.name = 'Foreign Aid'
        self.only_target_can_block = False
        self.status_message = 'Unresolved foreign aid action.'

    def perform(self, victim=None):
        if not self.is_resolved:
            self.actor.add_money(2)
            self.is_resolved = True
            self.state = 'RESOLVED'
            self.status_message = 'Foreign aid gave 2 coins to %s for a total of %s coins.' % (self.actor.name, self.actor.get_money())
            return True
        else:
            return False
    
    def rollback(self):
        self.actor.take_money(2)
        return True

    def block(self, blocker, cardtype=None):
        if not self.was_blocked:
            self.rollback()
            self.was_blocked = True
            return BlockForeignAid(blocker, self.actor, self)
        else:
            return None

    @property
    def is_challengeable(self):
        return False
    
    @property
    def is_blockable(self):
        return True

    @property
    def card_needed(self):
        return None
    

class Tax(Action):
    def __init__(self, player):
        super(Tax, self).__init__(player)
        self.name = 'Tax'
        self.status_message = 'Unresolved tax.'

    def perform(self, victim=None):
        if not self.is_resolved:
            self.actor.add_money(3)
            self.is_resolved = True
            self.state = 'RESOLVED'
            self.status_message = '%s taxed the people for 3 coins with their Duke, so they now have %s coins.' % (self.actor.name, self.actor.get_money())
            return True
        else:
            return False
    
    def rollback(self):
        self.actor.take_money(3)
        return True
    
    @property
    def is_challengeable(self):
        return True
    
    @property
    def is_blockable(self):
        return False

    @property
    def card_needed(self):
        return 'Duke'
    
class BlockSteal(Action):
    def __init__(self, player, target, blockedaction, blockcard):
        super(BlockSteal, self).__init__(player)
        self.target = target
        self.name = 'Block steal'
        self.blockcard = blockcard
        self.blockedaction = blockedaction
        self.status_message = 'Steal by %(thief)s was foiled by %(blocker)s\'s %(blockcard)s' % { 'thief': self.target.name, 'blocker': self.actor.name, 'blockcard': blockcard } 
        self.is_resolved = True

    def perform(self):
        raise NotImplementedError()

    def rollback(self):
        stolencoins = self.blockedaction.stolencoins
        self.actor.take_money(stolencoins)
        self.target.add_money(stolencoins)
        self.blockedaction.was_blocked = False
        return True

    @property
    def is_challengeable(self):
        return True
    
    @property
    def is_blockable(self):
        return False

    @property
    def card_needed(self):
        return self.blockcard 

class Steal(Action):
    def __init__(self, player):
        super(Steal, self).__init__(player)
        self.name = 'Steal'
        self.status_message = 'Unresolved steal.'

    def perform(self, victim):
        if not self.is_resolved:
            self.target = victim
            self.stolencoins = victim.take_money(2)
            self.actor.add_money(self.stolencoins)
            self.is_resolved = True
            self.state = 'RESOLVED'
            statusparams = {'thief': self.actor.name, 'thiefcoins': self.actor.get_money(), 'amt': self.stolencoins, 'victim': victim.name, 'victimcoins': victim.get_money()}
            self.status_message = '%(thief)s stole %(amt)s coins from %(victim)s with their Captain, so %(thief)s now has %(thiefcoins)s coins while %(victim)s is left with %(victimcoins)s coins.' % statusparams
            return True
        else:
            return False
    
    def rollback(self):
        self.actor.take_money(self.stolencoins)
        self.target.add_money(self.stolencoins)
        return True

    def block(self, blocker, cardtype):
        if not self.was_blocked:
            self.rollback()
            self.was_blocked = True
            return BlockSteal(blocker, self.actor, self, cardtype)
        else:
            return None
    
    @property
    def is_challengeable(self):
        return True
    
    @property
    def is_blockable(self):
        return True

    @property
    def card_needed(self):
        return 'Captain'

class Game(object):
    actions = {'income': Income, 'foreignaid': ForeignAid, 'tax': Tax, 'steal': Steal}
    def __init__(self):
        self._state = 'STARTING'
        self._players = OrderedDict()
        self._deck = None
        self._state = 'STARTING'
        self._lastwinner = None
        self._lastaction = None
        self._turnowner = None
    
    def clear_players(self):
        if not self.is_running():
            self._players = OrderedDict()
            self._lastwinner = None
            return 'All players gone!'
        else:
            return 'Cannot clear players in a running game'
    
    def check_for_end_state(self):
        """Returns true if the game is in an endstate or has just reached an endstate, and sets the last winner if the game just finished."""
        if not self.is_running():
            return True
        else:
            num_alive_players = 0
            last_alive_player = None
            for player in self._players.values():
                if not player.is_dead():
                    last_alive_player = player
                    num_alive_players = num_alive_players + 1
            if num_alive_players > 1:
                return False
            elif num_alive_players == 1:
                last_alive_players.add_wins(1)
                self._lastwinner = last_alive_player.name
                self._state = 'DONE'
                return True
            else:
                return True

    def get_next_turnowner(self):
        if self.check_for_end_state():
            return 'Game is done! The last winner is %s' % self._lastwinner 
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
    
    def admin_force_turn_change(self, playername):
        if self.is_running():
            if self._lastaction is not None and not self._lastaction.is_resolved:
                self._lastaction.is_resolved = True # to let the game continue
                self._lastaction.status_message = self._lastaction.status_message + '\r\nAction resolution forced by admin'
            player = self.get_player(playername)
            if player is not None and not player.is_dead():
                self._turnowner = playername
                return 'Admin has forced turn order; it is now %s\'s turn' % playername
            else:
                return 'Cannot force turn on missing/dead player'
        else:
            return 'Game is not running'

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
            self._lastaction = None
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
                    pass
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
        player_statuses = []
        if self.is_running():
            statuses.append('Current turn: %s' % self._turnowner)
            for player in self._players.values():
                player_statuses.append(player.public_status_check())
            statuses.append(str.join('\r\n', player_statuses))
            if self._lastaction is not None:
                statuses.append('LAST ACTION was: %s' % self._lastaction.get_status())
            stattext = str.join('\r\n', statuses)
            result = 'Public stats: %s' % (stattext)
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

    def ambassador_return(self, playername, cardtype):
        if self.is_running():
            player = self.get_player(playername)
            if player is None or player.is_dead():
                return '%s is not playing the game' % playername
            if player.has_card_type(cardtype) and (len(player._cards) + len(player._dead_cards)) > 2:
                player.return_cardtype(cardtype)
                self._deck.return_card(cardtype)
                self._deck.shuffle()
                return '%s returned a card as per ambassador powers' % playername
            else:
                return 'Could not return a card'
        else:
            return 'Game not running'

    def return_and_redraw(self, player, cardtype):
        if player.has_card_type(cardtype):
            player.return_cardtype(cardtype)
            self._deck.return_card(cardtype)
            self._deck.shuffle()
            self.draw(player)
            return True
        else:
            return False

    def challenge(self, playername):
        if self.is_running():
            player = self.get_player(playername)
            if player is None or player.is_dead():
                return '%s is not playing the game' % playername
            elif self._lastaction is None:
                return 'No action to challenge!'
            elif self._lastaction.actor.name == playername:
                return 'Cannot challenge your own action!'
            else:
                result = ''
                challenge_result = self._lastaction.challenge(player)
                if challenge_result is None:
                    result = 'Action cannot be challenged'
                elif challenge_result:
                    result = 'Challenge successful! %s did not have the %s necessary for %s and must forfeit an influence.' % (self._lastaction.actor.name, self._lastaction.card_needed, self._lastaction.name)
                else:
                    result = 'Challenge denied! The %s action was good. %s must forfeit an influence.' % (self._lastaction.name, self._lastaction.challenger.name)
                    self.return_and_redraw(self._lastaction.actor, self._lastaction.card_needed)
                return result
        else:
            return 'Game is not running'
    
    def block(self, playername, cardtype=None):
        if self.is_running():
            player = self.get_player(playername)
            if player is None or player.is_dead():
                return '%s is not playing the game' % playername
            elif self._lastaction is None:
                return 'No action to block!'
            elif self._lastaction.actor.name == playername:
                return 'Cannot block your own action!'
            elif self._lastaction.only_target_can_block and self._lastaction.target.name != playername:
                return 'Only target can block that action'
            else:
                result = ''
                if cardtype is not None:
                    if cardtype.lower() in ('c', 'captain'):
                        cardtype = 'Captain'
                    elif cardtype.lower() in ('a', 'ambassador'):
                        cardtype = 'Ambassador'
                block_action = self._lastaction.block(player, cardtype)
                if block_action is None:
                    result = 'Action cannot be blocked for whatever reason'
                else:
                    self._lastaction = block_action
                    result = block_action.get_status()
                return result
        else:
            return 'Game is not running'

    def reveal(self, playername, cardtype):
        if self.is_running():
            player = self.get_player(playername)
            if player is None:
                return '%s is not playing the game' % playername
            else:
                if self.return_and_redraw(player, cardtype):
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

    def get_all_private_statuses(self):
        statuses = {}
        if self.is_running():
            for player in self._players.values():
                if not player.is_dead():
                    statuses[player.name] = player.status_check()
        return statuses

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

    def perform_initiative_action(self, actionname, playername, victimname=None):
        if self.is_running():
            player = self.get_player(playername)
            if player is None or player.is_dead():
                return '%s is not playing the game' % playername
            elif not playername == self._turnowner:
                return 'It is not %s\'s turn to take initiative actions' % playername
            elif self._lastaction is not None and not self._lastaction.is_resolved:
                return 'Last action has yet to be resolved'
            elif not self.actions.has_key(actionname):
                return '%s is not a valid initiative action' % actionname
            else:
                actiontype = self.actions[actionname]
                action = actiontype(player)
                if victimname is None:
                    victim = None
                else:
                    victim = self.get_player(victimname)
                    if victim is None or victim.is_dead():
                        return '%s chose invalid victim %s for action %s' % (playername, victimname, actionname)
                if action.perform(victim):
                    self._lastaction = action 
                    result = action.get_status()
                    if action.is_resolved:
                        result = result + '\r\n' + self.get_next_turnowner()
                    else:
                        result = result + '\r\nWaiting for action resolution'
                    return result
                else:
                    return '%s could not perform %s for some reason; investigate please' % (playername, actionname)
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


def test_stuff():
    player = Player('testplay')
    action = Income(player)
    action = ForeignAid(player)
