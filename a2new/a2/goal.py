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

This file contains the hierarchy of Goal classes and related helper functions.
"""
from __future__ import annotations
import math
import random
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> list[Goal]:
    """Return a randomly generated list of goals with length <num_goals>.

    Each goal must be randomly selected from the two types of Goals provided
    and must have a different randomly generated colour from COLOUR_LIST.
    No two goals can have the same colour.

    Preconditions:
    - num_goals <= len(COLOUR_LIST)
    """
    final = []
    # 取随机颜色
    sample = random.sample(COLOUR_LIST, num_goals)
    for i in sample:
        per = random.random()
        blo = random.random()
        if per >= blo:
            final.append(PerimeterGoal(i))
        else:
            final.append(BlobGoal(i))
    return final


def flatten(block: Block) -> list[list[tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j].

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """
    # maxl = 2 ** block.max_depth
    maxl = int(math.pow(2, block.max_depth))
    min_len = block.size / (2 ** (block.max_depth - block.level))
    # max_depth的长度
    all_list = [[(1, 1, 1) for _ in range(maxl)] for _ in range(maxl)]
    if not block.children and block.colour is not None:
        x_start = round(block.position[0] / min_len)
        y_start = round(block.position[1] / min_len)
        num_index = round(block.size / min_len)  # 能横跨几个index
        for i in range(x_start, x_start + num_index):  # x 的index
            for j in range(y_start, y_start + num_index):  # y 的index
                all_list[i][j] = block.colour
        return all_list
    else:
        for child in block.children:
            new_list = flatten(child)
            all_list = [[new_list[col][ver] if all_list[col][ver] == (1, 1, 1)
                         else all_list[col][ver]
                         for ver in range(len(all_list[col]))]
                        for col in range(len(all_list))]
            # for col in range(len(all_list)):
            #    for ver in range(len(all_list[col])):  # return 回来的是部分的
            #        if all_list[col][ver] == (1, 1, 1):  # 不能等于原来的那个值
            #            all_list[col][ver] = new_list[col][ver]
            # _flatten_help(all_list, new_list)
        return all_list


# def _flatten_help(all_list: list[list[tuple[int, int, int]]],
#                  new_list: list[list[tuple[int, int, int]]]) -> None:
#    """The function to help flatten to achieve the flex loop"""
#    for col in range(len(all_list)):
#        for ver in range(len(all_list[col])):  # return 回来的是部分的
#            if all_list[col][ver] == (1, 1, 1):  # 不能等于原来的那个值
#                all_list[col][ver] = new_list[col][ver]


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    Instance Attributes:
    - colour: The target colour for this goal, that is the colour to which
              this goal applies.
    """

    colour: tuple[int, int, int]

    def __init__(self, target_colour: tuple[int, int, int]) -> None:
        """Initialize this goal to have the given <target_colour>."""
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given <board>.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal."""
        raise NotImplementedError


class PerimeterGoal(Goal):
    """A goal to maximize the presence of this goal's target colour
    on the board's perimeter.
    """

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.

        The score for a PerimeterGoal is defined to be the number of unit cells
        on the perimeter whose colour is this goal's target colour. Corner cells
        count twice toward the score.
        """
        all_lst = flatten(board)
        long = len(all_lst)
        if long == 1:
            want = [all_lst[0][0], all_lst[0][0], all_lst[0][0], all_lst[0][0]]
            # return 4 ?
        else:
            want = [
                all_lst[0][0],
                all_lst[0][0],
                all_lst[0][long - 1],
                all_lst[0][long - 1],
                all_lst[long - 1][0],
                all_lst[long - 1][0],
                all_lst[long - 1][long - 1],
                all_lst[long - 1][long - 1],
            ]
        for col in range(1, long - 1):  # col
            want.append(all_lst[col][0])
            want.append(all_lst[col][long - 1])
        for ver in range(1, long - 1):
            want.append(all_lst[0][ver])
            want.append(all_lst[long - 1][ver])
        return want.count(self.colour)

    def description(self) -> str:
        """Return a description of this goal."""
        return (
            "A goal to maximize the presence of"
            + colour_name(self.colour)
            + "on the board perimeter, double for corner"
        )


class BlobGoal(Goal):
    """A goal to create the largest connected blob of this goal's target
    colour, anywhere within the Block.
    """

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.

        The score for a BlobGoal is defined to be the total number of
        unit cells in the largest connected blob within this Block.
        """
        mark = []
        all_lst = flatten(board)
        long = len(all_lst)
        visited = [[-1 for _ in range(long)] for _ in range(long)]
        for i in range(long):  # x
            for j in range(long):  # y
                if visited[i][j] == -1:
                    mark.append(
                        self._undiscovered_blob_size((i, j), all_lst, visited))
        return max(mark)

    def _undiscovered_blob_size(
            self,
            pos: tuple[int, int],
            board: list[list[tuple[int, int, int]]],
            visited: list[list[int]],
    ) -> int:
        """Return the size of the largest connected blob in <board> that (a) is
        of this Goal's target <colour>, (b) includes the cell at <pos>, and (c)
        involves only cells that are not in <visited>.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure (to <board>) that, in each cell,
        contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.

        If <pos> is out of bounds for <board>, return 0.
        """
        x, y = pos
        long = len(board)
        if x > long - 1 or y > long - 1 or x < 0 or y < 0:
            return 0
        elif visited[x][y] == -1 and board[x][y] != self.colour:
            visited[x][y] = 0
            return 0
        elif visited[x][y] == -1 and board[x][y] == self.colour:
            visited[x][y] = 1
            mark = 1
            mark += self._undiscovered_blob_size((x + 1, y), board, visited)
            mark += self._undiscovered_blob_size((x - 1, y), board, visited)
            mark += self._undiscovered_blob_size((x, y + 1), board, visited)
            mark += self._undiscovered_blob_size((x, y - 1), board, visited)
            return mark
        else:
            return 0

    def description(self) -> str:
        """Return a description of this goal."""
        return (
            "A goal to create the largest connected blob of"
            + colour_name(self.colour)
            + ", anywhere within the Block"
        )


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(
        config={
            'allowed-import-modules': [
                'doctest',
                'python_ta',
                'random',
                'typing',
                'block',
                'settings',
                'math',
                '__future__',
            ],
            'max-attributes': 15,
        }
    )
