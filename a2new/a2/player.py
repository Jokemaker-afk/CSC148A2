"""CSC148 Assignment 2

CSC148 Winter 2024
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
Jaisie Sin, and Joonho Kim

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, Jaisie Sin, and Joonho Kim

Module Description:

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import (
    Action,
    KEY_ACTION,
    ROTATE_CLOCKWISE,
    ROTATE_COUNTER_CLOCKWISE,
    SWAP_HORIZONTAL,
    SWAP_VERTICAL,
    SMASH,
    PASS,
    PAINT,
    COMBINE,
)


def create_players(num_human: int, num_random: int, smart_players: list[int]) \
        -> list[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.

    Player ids are given in the order that the players are created, starting
    at id 0.

    Each player is assigned a random goal.
    """
    final = []
    h = num_human
    hr = num_human + num_random
    hrs = num_human + num_random + len(smart_players)
    goals = generate_goals(hrs)
    for i in range(h):
        final.append(HumanPlayer(i, goals[i]))
    for j in range(h, hr):
        final.append(RandomPlayer(j, goals[j]))
    for k in range(hr, hrs):
        final.append(SmartPlayer(k, goals[k], smart_players[k - hr]))
    # k - hr 从0开始计算，对应smart里面的list
    # 将 player 和 goal对应
    return final


def _get_block(block: Block, location: tuple[int, int], level: int) \
        -> Block | None:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - block.level <= level <= block.max_depth
    """
    lx, ly = location
    px, py = block.position
    size = block.size
    if lx < px or ly < py or lx >= px + size or ly >= py + size:
        return None
    else:
        final = []
        if block.children and block.level + 1 <= level:  # 有children且目标点在里面
            for i in block.children:
                final.append(_get_block(i, location, level))
            get = [x for x in final if x is not None]
            # 4个里面只有可能有1块有那个点，其他的都是None
            return get[0]
        else:
            return block
    # 按住左键后按w，s等键进行操作


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    Instance Attributes:
    - id: This player's number.
    - goal: This player's assigned goal for the game.
    - penalty: The penalty accumulated by this player through their actions.
    """

    id: int
    goal: Goal
    penalty: int

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player."""
        self.goal = goal
        self.id = player_id
        self.penalty = 0

    def get_selected_block(self, board: Block) -> Block | None:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event."""
        raise NotImplementedError

    def generate_move(self, board: Block) -> tuple[Action, Block] | None:
        """Return a potential move to make on the <board>.

        The move is a tuple consisting of an action and
        the block the action will be applied to.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError


class HumanPlayer(Player):
    """A human player.

    Instance Attributes:
    - _level: The level of the Block that the user selected most recently.
    - _desired_action: The most recent action that the user is attempting to do.

    Representation Invariants:
    - self._level >= 0
    """

    _level: int
    _desired_action: Action | None

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Block | None:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, self._level)

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYUP:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level -= 1
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> tuple[Action, Block] | None:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.

        This player's desired action gets reset after this method is called.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            self._correct_level(board)
            self._desired_action = None
            return None
        else:
            move = self._desired_action, block

            self._desired_action = None
            return move

    def _correct_level(self, board: Block) -> None:
        """Correct the level of the block that the player is currently
        selecting, if necessary.
        """
        self._level = max(0, min(self._level, board.max_depth))


class ComputerPlayer(Player):
    """A computer player. This class is still abstract,
    as how it generates moves is still to be defined
    in a subclass.

    Instance Attributes:
    - _proceed: True when the player should make a move, False when the
                player should wait.
    """

    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        Player.__init__(self, player_id, goal)

        self._proceed = False

    def get_selected_block(self, board: Block) -> Block | None:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == pygame.BUTTON_LEFT):
            self._proceed = True

    # Note: this is included just to make pyTA happy; as it thinks
    #       we forgot to implement this abstract method otherwise :)
    def generate_move(self, board: Block) -> tuple[Action, Block] | None:
        raise NotImplementedError


class RandomPlayer(ComputerPlayer):
    """A computer player who chooses completely random moves."""

    def generate_move(self, board: Block) -> tuple[Action, Block] | None:
        """Return a valid, randomly generated move only during the player's
        turn.  Return None if the player should not make a move yet.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """
        if self._proceed:
            action = [
                pygame.K_d,
                pygame.K_a,
                pygame.K_q,
                pygame.K_e,
                pygame.K_SPACE,
                pygame.K_c,
                pygame.K_r,
            ]
            new_board = board.create_copy()
            size = new_board.size
            # 随机新的location
            location = random.randint(0, size - 1), random.randint(0, size - 1)
            # 随机新的level
            level = random.randint(0, new_board.max_depth)
            # 随机新的一个block
            ran_block = _get_block(new_board, location, level)
            # 随机上述的一个action
            ran_action = random.choice(action)
            # 只有apply返回True了才跳出，否则一直随机
            while not KEY_ACTION[ran_action].apply(
                    ran_block, {'colour': self.goal.colour}):
                new_board = board.create_copy()
                location = (random.randint(0, size - 1),
                            random.randint(0, size - 1))
                level = random.randint(0, new_board.max_depth)
                ran_block = _get_block(new_board, location, level)
                ran_action = random.choice(action)
            # 跳出循环时 new_board, location, level 都固定了，且返回True,对这块board操作
            real_board = _get_block(board, location, level)
            self._proceed = False
            return KEY_ACTION[ran_action], real_board
        else:
            return None


class SmartPlayer(ComputerPlayer):
    """A computer player who chooses moves by assessing a series of random
    moves and choosing the one that yields the best score.

    Private Instance Attributes:
    - _num_test: The number of moves this SmartPlayer will test out before
                 choosing a move.
    """

    _num_test: int

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        """Initialize this SmartPlayer with a <player_id> and <goal>.

        Use <difficulty> to determine and record how many moves this SmartPlayer
        will assess before choosing a move. The higher the value for
        <difficulty>, the more moves this SmartPlayer will assess, and hence the
        more difficult an opponent this SmartPlayer will be.

        Preconditions:
        - difficulty >= 0
        """
        ComputerPlayer.__init__(self, player_id, goal)
        self._proceed = False
        self._num_test = difficulty

    def generate_move(self, board: Block) -> tuple[Action, Block] | None:
        """Return a valid move only during the player's turn by assessing
        multiple valid moves and choosing the move that results in the highest
        score for this player's goal.  This score should also account for the
        penalty of the move.  Return None if the player should not make a move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This method does not mutate <board>.
        """
        # Action 为smash时，返回smash的动作，与对应操作的block，但新的smash不一定
        # 和尝试时的一样
        if self._proceed:
            action = [
                ROTATE_CLOCKWISE,
                ROTATE_COUNTER_CLOCKWISE,
                SWAP_HORIZONTAL,
                SWAP_VERTICAL,
                SMASH,
                PASS,
                PAINT,
                COMBINE,
            ]
            all_actions = []
            final_action = {}
            for _ in range(self._num_test):
                new_board = board.create_copy()
                # 随机新的location
                location = (random.randint(0, new_board.size - 1),
                            random.randint(0, new_board.size - 1))
                # 随机新的level
                level = random.randint(0, new_board.max_depth)
                # 随机新的一个block
                ran_block = _get_block(new_board, location, level)
                # 随机上述的一个action
                ran_action = random.choice(action)
                # 只有apply返回True了才跳出，否则一直随机
                while not ran_action.apply(
                        ran_block, {'colour': self.goal.colour}):
                    new_board = board.create_copy()
                    location = (random.randint(0, new_board.size - 1),
                                random.randint(0, new_board.size - 1))
                    level = random.randint(0, new_board.max_depth)
                    ran_block = _get_block(new_board, location, level)
                    ran_action = random.choice(action)
                # 跳出循环时 new_board, location, level 都固定了，且返回True,对这块board操作
                all_actions.append((ran_action, location, level))
            for j in all_actions:
                new_board = board.create_copy()
                test_board = _get_block(new_board, j[1], j[2])
                # 运行一次,此时new_board 被更新
                j[0].apply(test_board, {'colour': self.goal.colour})
                if j[0] in {PAINT, COMBINE}:
                    minus = 1
                elif (j[0] == SMASH
                      and test_board.max_depth - test_board.level > 1):
                    # 用作smash的风险
                    minus = 2
                elif j[0] == SMASH:
                    minus = 2 + (0 if random.random() < 0.25 else 1)
                else:
                    minus = 0
                #  test_mark - 原分数 - 操作得分
                delta_mark = self.goal.score(new_board) - self.goal.score(
                    board) - minus
                final_action[j] = delta_mark
            max_key = max(final_action, key=final_action.get)
            if final_action[max_key] <= 0:
                # real_board 改变原来的board
                self._proceed = False
                return PASS, _get_block(board, max_key[1], max_key[2])
            self._proceed = False
            return max_key[0], _get_block(board, max_key[1], max_key[2])
        else:
            return None


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(
        config={
            'allowed-io': ['process_event'],
            'allowed-import-modules': [
                'doctest',
                'python_ta',
                'random',
                'typing',
                'actions',
                'block',
                'goal',
                'pygame',
                '__future__',
            ],
            'max-attributes': 10,
            'generated-members': 'pygame.*',
        }
    )
