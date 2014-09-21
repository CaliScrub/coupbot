from abc import abstractproperty, abstractmethod, ABCMeta # abstract base class
from player import Player

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

