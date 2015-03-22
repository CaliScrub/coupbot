import random
from collections import OrderedDict

from deck import Deck
from player import Player
from action import State
import action

#TODO: !pass, coup status should show list of waiters

class Game(object):
    actions = {'income': action.Income, 'foreignaid': action.ForeignAid, 'tax': action.Tax, 'steal': action.Steal}
    def __init__(self):
        self._state = 'STARTING'
        self._players = OrderedDict()
        self._passers = ()
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
                last_alive_player.add_wins(1)
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
            player = self.get_player(newname, exact=True)
            if player is not None and not player.is_dead() and newname != self._turnowner:
                self._turnowner = newname
                return 'It is now %s\'s turn' % newname
            else:
                newindex = newindex + 1
        return 'Cannot find a new turn owner'

    def get_necessary_passers(self):
        if self.check_for_end_state() or self._lastaction is None:
            return 'Game over, no passers needed'
        if (self._lastaction.state == State.PENDING_CHALLENGE
                or (self._lastaction.state == State.PENDING_BLOCKERS
                    and isinstance(self._lastaction, self.actions['foreign_aid']))):
            return list(set(self._players) - set([self._lastaction.actor.name]))
        elif self._lastaction.state == State.BLOCK_PENDING_CHALLENGE:
            return list(set(self._players) - set([self._lastaction.blocker.name]))
        elif self._lastaction.state == State.PENDING_BLOCKERS:
            return [self._lastaction.target]
        else:
            return None

    def get_passers_left(self):
        if self.get_necessary_passers() is None:
            return None
        else:
            return list(set(self.get_necessary_passers()) - set(self._passers))

    def player_pass(self, playername):
        if self.is_running():
            player = self.get_player(playername)
            if player is None or player.is_dead():
                return '%s is not playing the game' % playername
            elif playername in self._passers:
                return '%s has already passed' % playername
            else:
                self._passers.add(playername)
                return '%s has passed'
        else:
            return 'Game is not running'
    
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

    def get_player(self, name, exact=False):
        # exact match
        if self._players.has_key(name):
            return self._players[name]
        elif len(name.lower().strip()) >= 1 and not exact:
            matched_name = ''
            for pname in self._players.iterkeys():
                if name.lower() in pname.lower():
                    if matched_name is None:
                        matched_name = pname
                    elif matched_name != pname:
                        return None
            if matched_name is None:
                return None
            else:
                return self._players[matched_name]
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

    def get_public_status(self, shortform = True):
        result = ''
        statuses = []
        player_statuses = []
        if self.is_running():
            statuses.append('Current turn: %s' % self._turnowner)
            if self._lastaction is not None:
                statuses.append('LAST ACTION was: %s' % self._lastaction.get_status(shortform=True))
            for player in self._players.values():
                player_statuses.append(player.public_status_check())
            if shortform:
                statuses.append('PLAYERS: ' + str.join('--', player_statuses))
                stattext = str.join(' - ', statuses)
            else:
                statuses.append(str.join('\r\n', player_statuses))
                stattext = str.join('\r\n', statuses)
            result = 'Public stats: %s' % (stattext)
        else:
            result = 'Game is not running'
        return result

    def get_public_player_status(self, shortform = True):
        statuses = []
        if self.is_running():
            for player in self._players.values():
                statuses.append(player.public_status_check())
            if shortform:
                stattext = str.join('--', statuses)
            else:
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
                self._deck.return_cards(cardtype)
                self._deck.shuffle()
                return '%s returned a card as per ambassador powers' % playername
            else:
                return 'Could not return a card'
        else:
            return 'Game not running'

    def return_and_redraw(self, player, cardtype):
        if player.has_card_type(cardtype):
            player.return_cardtype(cardtype)
            self._deck.return_cards(cardtype)
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
                true_cardtype = self._deck.find_card_type(cardtype)
                if true_cardtype is None:
                    return 'Cannot resolve %s to a card type' % cardtype
                if self.return_and_redraw(player, true_cardtype):
                    return '%s has a %s! It was returned to the deck, and %s drew a new card from the reshuffled deck' % (playername, true_cardtype, playername)
                else:
                    return '%s does not have a %s!' % (playername, true_cardtype)
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

    def kill_influence(self, playername, cardtype, admin=False):
        if self.is_running():
            player = self.get_player(playername)
            if player is None:
                return '%s is not playing the game' % playername
            true_cardtype = self._deck.find_card_type(cardtype)
            if true_cardtype is None:
                return 'Cannot resolve %s to a card type' % cardtype
            if player.kill_card(true_cardtype):
                return '%s has chosen a %s to die%s' % (playername, true_cardtype, ' (decreed by admin)' if admin else '')
            else:
                return '%s does not have a %s to sacrifice' % (playername, true_cardtype)
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
                self._deck.return_cards(returncard)
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
