__author__ = 'steven synan'

import random
from itertools import groupby
from abc import ABCMeta, abstractmethod
import sqlite3 as sql


#######################################################################################################################
# Alright, time for a little CMA (cover my ass), since this code will likely find it's way online and there are some
# known issues currently. Namely, the algorithms used are very brute-force and not geared toward things like
# performance, so I wouldn't be trying to run millions of monte carlo simulations through this. This is my first Python
# project ever, and I'm just trying to have fun with the language and learn the syntax.
#
# Worse yet, there are assumptions made all over the place as I write this, and I haven't been implementing things like
# exception handling and all the peas and carrots stuff. This is not production level code! I just wanted to build a
# new toy and play with it. As of this writing, this is basically a cheap video poker 'engine' which will likely evolve
# as I tinker with it more and more. Or it will die on the vine, because there are TONS of poker apps out there.
#######################################################################################################################

# TODO: Consider breaking this out into more files, though there are perks to keeping everything wrapped together
# in a nice package. Heh. Package.


class Rank:
    two, three, four, five, six, seven, eight, nine, ten, jack, queen, king, ace = range(2, 15)


class Suit:
    spades, diamonds, clubs, hearts = range(1, 5)


class CardVisibility:
    not_visible, player, all_players = range(0, 3)


class Card(object):
    def __init__(self, rank, suit, visibility=CardVisibility.not_visible):
        self.rank = self.__resolve_rank__(rank)
        self.suit = self.__resolve_suit__(suit)
        self.visibility = visibility

    def rank_str(self, shorthand=False):
        if self.rank < Rank.two or self.rank > Rank.ace:
            return None
        if self.rank is Rank.ten:
            return 'T' if shorthand else '10'
        elif self.rank == Rank.jack:
            return 'J' if shorthand else 'Jack'
        elif self.rank == Rank.queen:
            return 'Q' if shorthand else 'Queen'
        elif self.rank == Rank.king:
            return 'K' if shorthand else 'King'
        if self.rank == Rank.ace:
            return 'A' if shorthand else 'Ace'
        else:
            return str(self.rank)

    def suit_str(self, shorthand=False):
        if self.suit == 1:
            return 'S' if shorthand else 'Spades'
        elif self.suit == 2:
            return 'D' if shorthand else'Diamonds'
        elif self.suit == 3:
            return 'C' if shorthand else 'Clubs'
        elif self.suit == 4:
            return 'H' if shorthand else 'Hearts'
        else:
            return None

    def shorthand_str(self):
        return str.format('{}{}', self.rank_str(True), self.suit_str(True))

    def glyph(self):
        if self.suit is Suit.spades:
            return str.format('{}♤', self.rank_str(True))
        elif self.suit is Suit.diamonds:
            return str.format('{}♢', self.rank_str(True))
        elif self.suit is Suit.clubs:
            return str.format('{}♧', self.rank_str(True))
        elif self.suit is Suit.hearts:
            return str.format('{}♡', self.rank_str(True))
        else:
            return None

    def __str__(self):
        return str.format('{} of {}', self.rank_str(), self.suit_str())

    @staticmethod
    def __resolve_rank__(rank):
        rank_string = str(rank).lower().strip()
        if rank_string.startswith('j') or rank_string == '11':
            return Rank.jack
        elif rank_string.startswith('q') or rank_string == '12':
            return Rank.queen
        elif rank_string.startswith('k') or rank_string == '13':
            return Rank.king
        elif rank_string.startswith('a') or rank_string == '14':
            return Rank.ace
        elif rank_string.isdigit() and int(rank_string) in range(2, 11):
            return int(rank_string)
        else:
            return None

    @staticmethod
    def __resolve_suit__(suit):
        suit_string = str(suit).lower().strip()
        if suit_string.startswith('s') or suit_string == '1':
            return Suit.spades
        if suit_string.startswith('d') or suit_string == '2':
            return Suit.diamonds
        if suit_string.startswith('c') or suit_string == '3':
            return Suit.clubs
        if suit_string.startswith('h') or suit_string == '4':
            return Suit.hearts
        return None


class Deck(object):
    @staticmethod
    def build():
        cards = []
        for rank in range(2, 15):
            for suit in range(1, 5):
                cards.append(Card(rank, suit))
        random.shuffle(cards)
        return cards

    @staticmethod
    def deal(card_deck, num_cards):
        hand = []
        for x in range(num_cards):
            hand.append(card_deck.pop())
        return hand

    @staticmethod
    def grab_card(card_deck, rank, suit):
        rank = Card.__resolve_rank__(rank)
        suit = Card.__resolve_suit__(suit)
        match = next(c for c in card_deck if c.rank is rank and c.suit == suit)
        card_deck.remove(match)
        return match

    @staticmethod
    def grab_cards(card_deck, *args):
        cards = []
        for x in args:
            match = next(c for c in card_deck if c.shorthand_str() == x.upper())
            cards.append(match)
            card_deck.remove(match)
        return cards


# from card_games import Deck, Card, Suit, Rank, PokerRules as PR, VideoPokerConsoleRenderer as VR, VideoPoker as VP


class Player(object):
    @property
    def player_id(self):
        return self.__player_id

    @property
    def name(self):
        return self.__name

    @property
    def gil(self):
        return self.__gil

    @gil.setter
    def gil(self, value):
        self.__gil = value

    def __init__(self, player_id, name, gil):
        self.__player_id = player_id
        self.__name = name
        self.__gil = gil  # gil is the currency of choice!


class CardPlayer(Player):
    def __init__(self, player_id, name, gil):
        super().__init__(player_id, name, gil)
        self.hand = []

    def give_cards(self, cards):
        self.hand = self.hand + cards


########################################################################################################################
# POKER ONLY STUFF
########################################################################################################################


class HandEvaluation:
    high_card, pair, two_pair, three_of_a_kind, straight, flush, full_house, four_of_a_kind, straight_flush, \
    royal_flush = range(0, 10)


# Here we go... at the moment I'm piecing this whole thing together and not sure which direction I want to head and
# how far down the rabbit hole I want to go. Right now I'm making it suitable for video poker because that is easy
# and I'm feeling lazy at this particular moment. Ideally this would be a rock solid general purpose poker rules
# class with all kinds of awesome high performance code and the ability to resolve the best hand in any particular
# case, no matter how many cards or what variation of poker we're playing - well, instead we're stuck with a dreaded
#
# TODO: Make PokerRules suck less and offer cooler features.


class PokerRules:
    @staticmethod
    def evaluate_hand(hand):
        if PokerRules.__is_royal_flush__(hand):
            return HandEvaluation.royal_flush, 'royal flush'
        elif PokerRules.__is_straight_flush__(hand):
            return HandEvaluation.straight_flush, 'straight flush'
        elif PokerRules.__is_four_of_a_kind__(hand):
            return HandEvaluation.four_of_a_kind, 'four of a kind'
        elif PokerRules.__is_full_house__(hand):
            return HandEvaluation.full_house, 'full house'
        elif PokerRules.__is_flush__(hand):
            return HandEvaluation.flush, 'flush'
        elif PokerRules.__is_straight__(hand):
            return HandEvaluation.straight, 'straight'
        elif PokerRules.__is_three_of_a_kind__(hand):
            return HandEvaluation.three_of_a_kind, 'three of a kind'
        elif PokerRules.__is_two_pair__(hand):
            return HandEvaluation.two_pair, 'two pair'
        elif PokerRules.__is_pair__(hand):
            return HandEvaluation.pair, 'pair'
        else:
            high_card = PokerRules.__get_high_card__(hand)
            output = str.format('high card ({})', str(high_card))
            return HandEvaluation.high_card, output, high_card

    @staticmethod
    def __is_flush__(cards):
        suits = []
        for x in cards:
            suits.append(x.suit)
        matches = suits[1:] == suits[:-1]
        return matches

    @staticmethod  # LOOK AWAY!
    def __is_straight__(cards, ace_wrap_around=True):
        sorted_cards = sorted(cards, key=lambda x: x.rank, reverse=True)
        for index, card in enumerate(sorted_cards):
            if ace_wrap_around:
                if index == 0 and sorted_cards[index].rank is Rank.ace and sorted_cards[len(cards) - 1].rank is \
                        Rank.two:
                    continue
            if index + 1 < len(cards):
                if card.rank - sorted_cards[index + 1].rank is not 1:
                    return False
        return True

    @staticmethod
    def __is_straight_flush__(cards):
        return PokerRules.__is_flush__(cards) and PokerRules.__is_straight__(cards)

    @staticmethod
    def __is_royal_flush__(cards):
        high_card = PokerRules.__get_high_card__(cards)
        return high_card.rank == Rank.ace and PokerRules.__is_straight_flush__(cards)

    @staticmethod
    def __is_four_of_a_kind__(cards):
        rank_groups = PokerRules.__get_sorted_rank_groups__(cards)
        if rank_groups and rank_groups[0] is 4:
            return True
        return False

    @staticmethod
    def __is_full_house__(cards):
        rank_groups = PokerRules.__get_sorted_rank_groups__(cards)
        if len(rank_groups) is 2 and rank_groups[0] is 3:
            return True
        return False

    @staticmethod
    def __is_three_of_a_kind__(cards):
        rank_groups = PokerRules.__get_sorted_rank_groups__(cards)
        if rank_groups and rank_groups[0] is 3:
            return True
        return False

    @staticmethod
    def __is_two_pair__(cards):
        rank_groups = PokerRules.__get_sorted_rank_groups__(cards)
        if len(rank_groups) >= 2 and rank_groups[0] is 2 and rank_groups[1] is 2:
            return True
        return False

    @staticmethod
    def __is_pair__(cards):
        rank_groups = PokerRules.__get_sorted_rank_groups__(cards)
        if rank_groups and rank_groups[0] is 2:
            return True
        return False

    @staticmethod
    def __get_high_card__(cards):
        if cards:
            sorted_cards = sorted(cards, key=lambda x: x.rank, reverse=True)
            return sorted_cards[0]

    @staticmethod
    def __get_sorted_rank_groups__(cards):
        ranks = [x.rank for x in cards]
        sorted_ranks = sorted(ranks, reverse=True)
        rank_groups = [len(list(group)) for key, group in groupby(sorted_ranks)]
        sorted_rank_groups = sorted(rank_groups, reverse=True)
        return sorted_rank_groups


class VideoPokerBaseWinnings:
    jacks_or_better = 1
    two_pairs = 2
    three_of_a_kind = 3
    straight = 4
    flush = 6
    full_house = 9
    four_of_a_kind = 25
    straight_flush = 50
    royal_flush = 250


# Below are the various renderers for video poker. These will be responsible for formatting, colorizing,
# and doing other rendering tasks for various UI implementations. Default is just a simple console
# renderer, but maybe later on we'll have more fun and implement an HTML or GUI renderer.


class ConsoleColorScheme:
    spades = "\033[0;37m{}\033"  # default white (normally black, but many console windows are black)
    diamonds = "\033[0;34m{}\033"  # default blue
    clubs = "\033[0;32m{}\033"  # default green
    hearts = "\033[0;31m{}\033[0m"  # default red


class VideoPokerConsoleRenderer:
    @staticmethod
    def color_test():
        print(str.format(ConsoleColorScheme.spades + ConsoleColorScheme.diamonds + ConsoleColorScheme.clubs +
                         ConsoleColorScheme.hearts, "test white", "test blue", "test green", "test red"))

    @staticmethod
    def show_cards(cards):
        print(str.format('\n\n {}\t {}\t {}\t {}\t {}', cards[0].glyph(), cards[1].glyph(), cards[2].glyph(),
                         cards[3].glyph(), cards[4].glyph()))
        print('___________________')
        print('(1)\t(2)\t(3)\t(4)\t(5)')

    @staticmethod
    def show_outcome(cards):
        VideoPokerConsoleRenderer.show_cards(cards)
        result = PokerRules.evaluate_hand(cards)
        print('\n')
        print(str.format('You got a {}!', result[1]))


class Game(object):
    __metaclass__ = ABCMeta

    def __init__(self, player, min_credits, max_credits):
        self.__player = player
        self.__total_winnings = 0
        self.min_credits = min_credits
        self.max_credits = max_credits

    @property
    def player(self):
        return self.__player

    @property
    def total_winnings(self):
        return self.__total_winnings

    @abstractmethod
    def new_game(self, player_credits):
        pass

    @abstractmethod
    def next_turn(self):
        pass


# TODO: Refactor VideoPoker, it's doing too much. Right now it's just hacked enough together to do stuff.

# this is all pretty crude right now.

class VideoPoker(Game):
    def __init__(self, player, min_credits, max_credits):
        super().__init__(player, min_credits, max_credits)
        self.deck = Deck.build()
        self.current_turn = 0  # No turn numbers on init. Players get 2 turns max for each game
        self.player_credits = 0  # kinda gross here...

    def new_game(self, player_credits):
        self.current_turn = 1
        self.player_credits = player_credits
        self.deck = Deck.build()
        hand = Deck.deal(self.deck, 5)
        for card in hand:
            card.held = False
        super().player.give_cards(hand)
        VideoPokerConsoleRenderer.show_cards(super().player.hand)
        self.next_turn()

    def next_turn(self):
        if self.current_turn is not 2:
            holds = input("\nWhich cards would you like to hold?\n")
            int_holds = Parser.get_sorted_unique_numbers(holds, 5)
            for card_index in int_holds:
                super().player.hand[int(card_index) - 1].held = True
            for index, card in enumerate(super().player.hand):
                if not card.held:
                    super().player.hand[index] = Deck.deal(self.deck, 1)[0]
            VideoPokerConsoleRenderer.show_cards(super().player.hand)
            evaluation = PokerRules.evaluate_hand(super().player.hand)
            winnings = self.__calculate_winnings__(evaluation)
            if winnings > 0:
                print(str.format('\n{}\nYou win {} credits.', evaluation[1], winnings))
                super().player.gil = winnings
            else:
                super().player.gil -= self.player_credits
            self.current_turn = 2

    def __calculate_winnings__(self, evaluation):
        # more testing for hand evaluations... hmm...
        total_winnings = 0
        evaluation_val = evaluation[0]
        if evaluation_val == HandEvaluation.royal_flush:
            total_winnings += self.player_credits * VideoPokerBaseWinnings.royal_flush
        elif evaluation_val == HandEvaluation.straight_flush:
            total_winnings += self.player_credits * VideoPokerBaseWinnings.straight_flush
        elif evaluation_val == HandEvaluation.four_of_a_kind:
            total_winnings += self.player_credits * VideoPokerBaseWinnings.four_of_a_kind
        elif evaluation_val == HandEvaluation.full_house:
            total_winnings += self.player_credits * VideoPokerBaseWinnings.full_house
        elif evaluation_val == HandEvaluation.flush:
            total_winnings += self.player_credits * VideoPokerBaseWinnings.flush
        elif evaluation_val == HandEvaluation.straight:
            total_winnings += self.player_credits * VideoPokerBaseWinnings.straight
        elif evaluation_val == HandEvaluation.three_of_a_kind:
            total_winnings += self.player_credits * VideoPokerBaseWinnings.three_of_a_kind
        elif evaluation_val == HandEvaluation.two_pair:
            total_winnings += self.player_credits * VideoPokerBaseWinnings.two_pairs
        elif evaluation_val == HandEvaluation.pair:  # TODO: implement knowing 'jacks or better'.
            total_winnings += self.player_credits * VideoPokerBaseWinnings.jacks_or_better

        return total_winnings


# from card_games import CardPlayer Deck, Card,PokerRules as PR, VideoPokerConsoleRenderer as VR, VideoPoker as VP

########################################################################################################################
# GAME LOOPS
########################################################################################################################
# The basic idea is that we'll have a big overall loop which is pretty much an entire session looping until the user
# decides to quit, which will exit the game entirely. In this loop the user will be able to do things like access user
# settings, change the game type, etc. Inside this session loop game loops will run, which are just loops responsible
# for handling all the rules for a particular game.
########################################################################################################################


class Session(object):
    @staticmethod
    def begin():
        name = input("Welcome! What's your name? ")
        player = SQLiteDB.get_player(name)
        game = VideoPoker(player, 1, 5)
        game.new_game(5)

        # poker_loop = VideoPokerLoop(game)
        # poker_loop.initialize()

    @staticmethod
    def __execute_game_loop__(game_loop):
        raise NotImplementedError('Session.execute_game_loop not implemented.')


class GameLoop(object):
    __metaclass__ = ABCMeta

    @property
    def game(self):
        return self.__game

    def __init__(self, game):
        self.__game = game

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def process_user_input(self):
        pass


class VideoPokerLoop(GameLoop):
    def __init__(self, game):
        super().__init__(game)

    def initialize(self):
        self.__greet__()

        if self.game.player.gil < self.game.min_credits:
            print("Unfortunately you don't have enough credits to play :/")
            return False

        self.game.new_game(5)
        pass

    def process_user_input(self):
        return True

    def __greet__(self):
        print(str.format("Welcome to Video Poker, {0}!\nYou have {1} credits.", self.game.player.name,
                         self.game.player.gil))


########################################################################################################################
# HELP AND STUFF
#
# This is just a quick and dirty way to offer some sort of help for the user.
########################################################################################################################


########################################################################################################################
# THE DIRTY DAL WORK
########################################################################################################################


class SQLiteDB(object):
    @staticmethod
    def get_player(name):
        name = (name, )
        select_sql = "SELECT * FROM Players WHERE FirstName=? COLLATE NOCASE"
        player_raw = SQLiteDB.__execute_select__(select_sql, name)
        if player_raw:
            player = CardPlayer(player_raw[0], player_raw[1], player_raw[2])
            return player

    @staticmethod
    def save_player(player):
        pass

    @staticmethod
    def __execute_select__(select_sql, params, return_one_row=True):
        conn = sql.connect('DB/LootersCasino.db')
        with conn:
            cur = conn.cursor()
            cur.execute(select_sql, params)
            return cur.fetchone()
        pass


########################################################################################################################
# PARSER
########################################################################################################################


class Parser:
    @staticmethod
    def get_sorted_unique_numbers(string, max_num=9, reverse=False):
        """This method returns only unique single digit characters. For example if the input string is 'AB9019' then
        [0, 1, 9] will be returned. """
        chars = list(string)
        char_nums = [int(x) for x in chars if str.isdigit(x) and int(x) <= max_num]
        sorted_char_nums = sorted(char_nums, reverse=reverse)
        unique_char_nums = list(set(sorted_char_nums))
        return unique_char_nums


########################################################################################################################
# SANDBOX
########################################################################################################################


class CardOdds(object):
    @staticmethod
    def get_card_odds(card_deck):
        return 1 / len(card_deck)