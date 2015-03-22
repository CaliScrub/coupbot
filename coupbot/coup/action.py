from enum import Enum
from copy import deepcopy, copy
from abc import abstractproperty, abstractmethod, ABCMeta # abstract base class
from player import Player
from deck import find_card_type


class State(Enum):
    START = 1,
    PENDING_CHALLENGE = 2,
    CHALLENGED = 3,
    CHALLENGE_UPHELD_AWAITING_KILL = 4,
    CHALLENGE_DENIED_AWAITING_KILL = 5,
    PENDING_BLOCKERS = 6,
    BLOCK_PENDING_CHALLENGE = 7,
    BLOCK_CHALLENGED = 8,
    BLOCK_CHALLENGE_UPHELD_AWAITING_KILL = 9,
    BLOCK_CHALLENGE_DENIED_AWAITING_KILL = 10,
    AWAITING_FINAL_RESOLUTION = 11,
    RESOLVED = 12


class StateAction(Enum):
    AUTO = 1,
    CHALLENGE = 2,
    BLOCK = 3,
    PASS = 4,
    HAS_CARD = 5,
    NO_CARD = 6,
    KILL = 7,
    RESOLVE = 8

STATEMAPS = {
    'General': {
        State.START: {
                StateAction.AUTO: State.RESOLVED,
        },
    },
    'Special': {
        State.START: {
            StateAction.AUTO: State.PENDING_CHALLENGE,
        },
        State.PENDING_CHALLENGE: {
            StateAction.CHALLENGE: State.CHALLENGED,
            StateAction.PASS: State.PENDING_BLOCKERS,
        },
        State.CHALLENGED: {
            StateAction.NO_CARD: State.CHALLENGE_UPHELD_AWAITING_KILL,
            StateAction.HAS_CARD: State.CHALLENGE_DENIED_AWAITING_KILL,
        },
        State.CHALLENGE_UPHELD_AWAITING_KILL: {
            StateAction.KILL: State.RESOLVED,
        },
        State.CHALLENGE_DENIED_AWAITING_KILL: {
            StateAction.KILL: State.PENDING_BLOCKERS,
        },
        State.PENDING_BLOCKERS: {
            StateAction.BLOCK: State.BLOCK_PENDING_CHALLENGE,
            StateAction.PASS: State.AWAITING_FINAL_RESOLUTION,
        },
        State.BLOCK_PENDING_CHALLENGE: {
            StateAction.CHALLENGE: State.BLOCK_CHALLENGED,
            StateAction.PASS: State.RESOLVED,
        },
        State.BLOCK_CHALLENGED: {
            StateAction.NO_CARD: State.BLOCK_CHALLENGE_UPHELD_AWAITING_KILL,
            StateAction.HAS_CARD: State.BLOCK_CHALLENGE_DENIED_AWAITING_KILL,
        },
        State.BLOCK_CHALLENGE_DENIED_AWAITING_KILL: {
            StateAction.KILL: State.RESOLVED,
        },
        State.BLOCK_CHALLENGE_UPHELD_AWAITING_KILL: {
            StateAction.KILL: State.AWAITING_FINAL_RESOLUTION,
        },
        State.AWAITING_FINAL_RESOLUTION: {
            StateAction.RESOLVE: State.RESOLVED,
        },
    }
}


class Action(object):
    __metaclass__ = ABCMeta
    def __init__(self, player):
        if isinstance(player, Player):
            self.actor = player
        else:
            raise TypeError()
        self.target = None
        self.challenger = None
        self.only_target_can_block = True
        self.blocker = None
        self.blockcard = None
        self.default_blockcard = None
        self.required_blockcards = None
        self.block_challenger = None
        self.state = State.START
        self.name = 'BaseAction'
        self.deck = None
        self.status_message = 'Unresolved action'
        self.status_history = 'Unresolved action'

    @property
    def is_resolved(self):
        return self.state == State.RESOLVED
    
    @abstractmethod
    def perform(self, victim=None):
        raise NotImplementedError()

    @abstractproperty
    def statemap(self):
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

    def auto_actions(self, new_state):
        return

    def force_resolve(self):
        """For admin use only!!!"""
        self.state = State.RESOLVED

    def can_advance_state(self, state_action):
        return self.state in self.statemap and state_action in self.statemap[self.state]

    def advance_state(self, state_action):
        if self.can_advance_state(state_action):
            old_state = self.state
            self.state = self.statemap[self.state][state_action]
            self.auto_actions(self.state)
            if state_action != StateAction.AUTO:
                self.status_message += '- Advanced via %s from state %s to state %s -' % (state_action.name, old_state.name, self.state.name)
            return True
        else:
            return False

    def pass_advance(self):
        return self.advance_state(StateAction.PASS)

    def resolve_advance(self):
        return self.advance_state(StateAction.RESOLVE)

    def auto_advance(self, advances=0):
        if self.can_advance_state(StateAction.AUTO):
            self.advance_state(StateAction.AUTO)
            # recursion
            advances += 1
            return self.auto_advance(advances)
        if advances > 0:
            return True
        else:
            return False

    def block(self, blocker, blockcard=None):
        """Blocks action. Returns None if can't be blocked."""
        if not isinstance(blocker, Player):
            raise TypeError()
        if (self.is_blockable and self.can_advance_state(StateAction.BLOCK)
                and not self.only_target_can_block or blocker == self.target):
            if ((blockcard is not None and blockcard not in self.required_blockcards)
                    or (blockcard is None and self.default_blockcard is None)):
                return False
            else:
                self.blocker = blocker
                if blockcard is None:
                    self.blockcard = self.default_blockcard
                else:
                    self.blockcard = blockcard
                self.status_message += '; Blocked by %s with a %s' % (self.blocker.name, self.blockcard)
                self.advance_state(StateAction.BLOCK)
                return True
        else:
            return None
    
    def challenge(self, challenger):
        """Challenges action. Returns None if can't be challenged, otherwise returns challenge success"""
        if not isinstance(challenger, Player):
            raise TypeError()
        if self.is_challengeable and self.can_advance_state(StateAction.CHALLENGE):
            if self.state == State.PENDING_CHALLENGE:
                self.challenger = challenger
                card_to_check = self.card_needed
                player_to_check = self.actor
            elif self.state == State.BLOCK_PENDING_CHALLENGE:
                self.block_challenger = challenger
                card_to_check = self.blockcard
                player_to_check = self.blocker
            self.advance_state(StateAction.CHALLENGE)
            if player_to_check.has_card_type(card_to_check):
                self.advance_state(StateAction.HAS_CARD)
                self.status_message = self.status_message + '; Challenged by %s, challenge was rebuffed.' % self.challenger.name
                return False
            else:
                self.advance_state(StateAction.NO_CARD)
                self.status_message = self.status_message + '; Challenged by %s, challenge was successful.' % self.challenger.name
                return True
        else:
            return None

    def sacrifice(self, sacrificer, sacced_card):
        if not isinstance(sacrificer, Player):
            raise TypeError()
        if self.can_advance_state(StateAction.KILL):
            # Check if sacrificer is correct
            desired_sacrifice = None
            sac_dict = {
                State.BLOCK_CHALLENGE_DENIED_AWAITING_KILL: self.block_challenger,
                State.BLOCK_CHALLENGE_UPHELD_AWAITING_KILL: self.blocker,
                State.CHALLENGE_DENIED_AWAITING_KILL: self.challenger,
                State.CHALLENGE_UPHELD_AWAITING_KILL: self.actor,
                State.AWAITING_FINAL_RESOLUTION: self.target,
            }
            if self.state in sac_dict:
                desired_sacrifice = sac_dict[self.state]
            if sacrificer == desired_sacrifice:
                true_cardtype = find_card_type(sacced_card)
                if sacrificer.kill_card(true_cardtype):
                    self.status_message += '; %s sacrificed a %s' % (sacrificer.name, true_cardtype)
                    self.advance_state(StateAction.KILL)
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def get_status(self, shortform=False):
        params = {'name': self.name, 'stat_msg': self.status_message, 'state': self.state.name, 'actor': self.actor.name}
        if self.target is not None:
            params['target'] = self.target.name
        if shortform:
            if 'target' in params:
                statustext = 'Action %(name)s by %(actor)s on %(target)s, status %(state)s' % params
            else:
                statustext = 'Action %(name)s by %(actor)s, status %(state)s' % params
        else:
            statustext = 'Action: %(name)s -- State: %(state)s -- Note: %(stat_msg)s' % params
        return statustext


class Income(Action):
    def __init__(self, player):
        super(Income, self).__init__(player)
        self.name = 'Income'
        self.status_message = 'Unresolved income action.'

    def perform(self, victim=None):
        self.actor.add_money(1)
        self.status_message = 'Income gave 1 coin to %s who now has %s coins.' % (self.actor.name, self.actor.get_money())
        return True

    @property
    def statemap(self):
        return STATEMAPS['General']
    
    @property
    def is_challengeable(self):
        return False
    
    @property
    def is_blockable(self):
        return False

    @property
    def card_needed(self):
        return None

class Coup(Action):
    def __init__(self, player):
        super(Coup, self).__init__(player)
        self.name = 'Coup'
        self.status_message = 'Unresolved coup action.'
        self._statemap = {
            State.START: {
                StateAction.AUTO: State.AWAITING_FINAL_RESOLUTION,
            },
            State.AWAITING_FINAL_RESOLUTION: {
                StateAction.KILL: State.RESOLVED,
            }
        }

    def perform(self, victim):
        if isinstance(self.actor, Player) and isinstance(victim, Player) and self.actor.get_money() >= 7:
            self.actor.pay_money(7)
            self.target = victim
            self.status_message = '%s has orchestrated a coup against %s for 7 coins, now has %s coins left.' % (self.actor.name, self.target.name, self.actor.get_money())
            return True
        else:
            return False

    @property
    def statemap(self):
        return self._statemap

    @property
    def is_challengeable(self):
        return False

    @property
    def is_blockable(self):
        return False

    @property
    def card_needed(self):
        return None

class ForeignAid(Action):
    def __init__(self, player):
        super(ForeignAid, self).__init__(player)
        self.name = 'Foreign Aid'
        self.required_blockcards = ['Duke']
        self.default_blockcard = 'Duke'
        self.only_target_can_block = False
        self.status_message = 'Unresolved foreign aid action.'
        self._statemap = deepcopy(STATEMAPS['General'])
        self._statemap[State.START][StateAction.AUTO] = State.PENDING_BLOCKERS
        self._statemap[State.PENDING_BLOCKERS] = {
            StateAction.BLOCK: State.BLOCK_PENDING_CHALLENGE,
            StateAction.PASS: State.AWAITING_FINAL_RESOLUTION,
        }
        self._statemap[State.BLOCK_PENDING_CHALLENGE] = {
            StateAction.CHALLENGE: State.BLOCK_CHALLENGED,
            StateAction.PASS: State.RESOLVED,
        }
        self._statemap[State.BLOCK_CHALLENGED] = {
            StateAction.NO_CARD: State.BLOCK_CHALLENGE_UPHELD_AWAITING_KILL,
            StateAction.HAS_CARD: State.BLOCK_CHALLENGE_DENIED_AWAITING_KILL,
        }
        self._statemap[State.BLOCK_CHALLENGE_DENIED_AWAITING_KILL] = {
            StateAction.KILL: State.RESOLVED,
        }
        self._statemap[State.BLOCK_CHALLENGE_UPHELD_AWAITING_KILL] = {
            StateAction.KILL: State.AWAITING_FINAL_RESOLUTION,
        },
        self._statemap[State.AWAITING_FINAL_RESOLUTION] = {
            StateAction.AUTO: State.RESOLVED,
        },

    def perform(self, victim=None):
        if not self.is_resolved:
            self.status_message = '%s is begging for foreign aid.' % (self.actor.name)
            return True
        else:
            return False

    def auto_actions(self, new_state):
        if new_state == State.AWAITING_FINAL_RESOLUTION:
            self.actor.add_money(2)
            self.status_message += 'Foreign aid gave 2 coins to %s for a total of %s coins.' % (self.actor.name, self.actor.get_money())

    @property
    def statemap(self):
        return self._statemap

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
        self._statemap = deepcopy(STATEMAPS['Special'])
        self._statemap[State.CHALLENGE_DENIED_AWAITING_KILL][StateAction.KILL] = State.AWAITING_FINAL_RESOLUTION
        self._statemap[State.PENDING_CHALLENGE][StateAction.PASS] = State.AWAITING_FINAL_RESOLUTION
        self._statemap[State.AWAITING_FINAL_RESOLUTION][StateAction.AUTO] = State.RESOLVED

    @property
    def statemap(self):
        return self._statemap

    def perform(self, victim=None):
        if not self.is_resolved:
            self.status_message = '%s is attempting to tax with their Duke.' % (self.actor.name)
            return True
        else:
            return False

    def auto_actions(self, new_state):
        if new_state == State.AWAITING_FINAL_RESOLUTION:
            self.actor.add_money(3)
            self.status_message = '%s taxed the people for 3 coins with their Duke, so they now have %s coins.' % (self.actor.name, self.actor.get_money())

    @property
    def is_challengeable(self):
        return True
    
    @property
    def is_blockable(self):
        return False

    @property
    def card_needed(self):
        return 'Duke'

class Steal(Action):
    def __init__(self, player):
        super(Steal, self).__init__(player)
        self.name = 'Steal'
        self.required_blockcards = ['Captain', 'Ambassador']
        self.status_message = 'Unresolved steal.'
        self._statemap = STATEMAPS['Special']
        self._statemap[State.AWAITING_FINAL_RESOLUTION][StateAction.AUTO] = State.RESOLVED

    def statemap(self):
        return self._statemap

    def perform(self, victim):
        if not self.is_resolved and isinstance(self.actor, Player) and isinstance(victim, Player):
            self.target = victim
            statusparams = {'thief': self.actor.name, 'victim': victim.name}
            self.status_message = '%(thief)s is attempting to steal from %(victim)s with their Captain.' % statusparams
            return True
        else:
            return False

    def auto_actions(self, new_state):
        if new_state == State.AWAITING_FINAL_RESOLUTION:
            victim = self.target
            self.stolencoins = victim.take_money(2)
            self.actor.add_money(self.stolencoins)
            statusparams = {'thief': self.actor.name, 'thiefcoins': self.actor.get_money(), 'amt': self.stolencoins, 'victim': victim.name, 'victimcoins': victim.get_money()}
            self.status_message = '%(thief)s stole %(amt)s coins from %(victim)s with their Captain, so %(thief)s now has %(thiefcoins)s coins while %(victim)s is left with %(victimcoins)s coins.' % statusparams

    @property
    def is_challengeable(self):
        return True
    
    @property
    def is_blockable(self):
        return True

    @property
    def card_needed(self):
        return 'Captain'

class Assassinate(Action):
    def __init__(self, player):
        super(Assassinate, self).__init__(player)
        self.name = 'Assassinate'
        self.required_blockcards = ['Contessa']
        self.default_blockcard = 'Contessa'
        self.status_message = 'Unresolved assassinate.'
        self._statemap = STATEMAPS['Special']
        self._statemap[State.AWAITING_FINAL_RESOLUTION] = {StateAction.KILL: State.RESOLVED}

    def statemap(self):
        return self._statemap

    def perform(self, victim):
        if not self.is_resolved and isinstance(self.actor, Player) and isinstance(victim, Player) and self.actor.get_money() >= 3:
            self.target = victim
            statusparams = {'killer': self.actor.name, 'victim': victim.name}
            self.status_message = '%(killer)s is attempting to assassinate from %(victim)s with their Assassin.' % statusparams
            return True
        else:
            return False

    def auto_actions(self, new_state):
        if new_state == State.PENDING_BLOCKERS:
            self.actor.pay_money(3)
        if new_state == State.AWAITING_FINAL_RESOLUTION:
            victim = self.target
            statusparams = {'killer': self.actor.name, 'killercoins': self.actor.get_money(), 'victim': victim.name}
            self.status_message = '%(killer)s has assassinated %(victim)s with their Assassin, so %(killer)s now has %(killercoins)s coins.' % statusparams

    @property
    def is_challengeable(self):
        return True

    @property
    def is_blockable(self):
        return True

    @property
    def card_needed(self):
        return 'Assassin'

class Diplomacy(Action):
    def __init__(self, player):
        super(Diplomacy, self).__init__(player)
        self.name = 'Diplomacy'
        self._statemap = deepcopy(STATEMAPS['Special'])
        self._statemap[State.CHALLENGE_DENIED_AWAITING_KILL][StateAction.KILL] = State.AWAITING_FINAL_RESOLUTION
        self._statemap[State.PENDING_CHALLENGE][StateAction.PASS] = State.AWAITING_FINAL_RESOLUTION

    @property
    def statemap(self):
        return self._statemap

    def perform(self, victim=None):
        if not self.is_resolved:
            self.status_message = '%s is attempting to switch cards with an Ambassador.' % (self.actor.name)
            return True
        else:
            return False

    def exchange_draw(self):
        drawn_cards = self.deck.draw(2)
        self.actor._cards = self.actor._cards + drawn_cards

    def auto_actions(self, new_state):
        if new_state == State.AWAITING_FINAL_RESOLUTION:
            self.exchange_draw()
            self.status_message = '%s has drawn 2 cards and is looking to exchange.' % self.actor.name

    @property
    def is_challengeable(self):
        return True

    @property
    def is_blockable(self):
        return False

    @property
    def card_needed(self):
        return 'Ambassador'