from collections import ChainMap, defaultdict
from contextlib import contextmanager
from math import floor, ceil
from unittest import TestCase, main

SQS = SUBSQUARE_SIZE = 3
GRID_SIZE = SUBSQUARE_SIZE ** 2

# all the indexes in a sudoku grid
grid_indexes = [(i, j) for j in range(GRID_SIZE) for i in range(GRID_SIZE)]

# A grid representation where any value can go anywhere
blank_grid = defaultdict(lambda: set(range(1, 10)))

def subsq_range(idx):
    '''
    Return the range of other cells in the same grid on this axis. E.g. 
    for idx 0, [0, 1, 2]
    for idx 1, [0, 1, 2]
    for idx 5, [3, 4, 5]
    for idx 8, [6, 7, 8]
    
    '''
    return range(floor(idx/SQS)*SQS, ceil(idx/SQS)*SQS)

def other_cells_affected(cell):
    '''
    Given a cell, return the cells which cannot hold the same value
    (includes cell)

    '''
    affected_cells = set()
    row, col = cell

    for i in range(GRID_SIZE):
        affected_cells.add((i, col))
        affected_cells.add((row, i))

    for r in subsq_range(row):
        for c in subsq_range(col):
            affected_cells.add((r, c))

    return affected_cells


def read_grid(grid):
    '''
    Read grid values from a list of strings into pairs of (row, col) and value

    '''
    for rowidx, row in enumerate(grid):
        for colidx, cell in enumerate(row):
            if cell != ' ':
                yield ((rowidx, colidx), int(cell))


class SudokuGrid(object):
    '''
    Represent a sudoku grid for solution search

    The grid is a map of position to set of possible values. 
    Set of 1 means the value of that position is fixed
    Set of 2+ means the value could be any of those values
    Set of 0 means the grid is impossible to solve, as no value can be placed

    ChainMaps are used so search can be performed

    '''

    def __init__(self, grid):
        '''
        Place the values and positions specified in grid in a blank puzzle
        Remove possible other positions that would conflict with these places

        '''
        self.grid = ChainMap({}, blank_grid)

        for cell, value in grid:
            self.set_cell(cell, value)

    def set_cell(self, cell, value):
        '''
        Place {value} as the only possible value at position `cell`
        Update other cells in the grid so `value` can't go in the same
        row, column, or sub-cube

        '''
        for other_cell in other_cells_affected(cell):
            self.grid[other_cell] = self.grid[other_cell] - {value}

        self.grid[cell] = {value}

    @contextmanager
    def search_subgrid(self, cell, value):
        '''
        Reversibly place `value` at position `cell`.
        This method is a context manager.
        When exited, this will restore grid to how it was before.
        This is useful for backtracking

        '''
        self.grid = self.grid.new_child()
        self.set_cell(cell, value)
        yield 
        self.grid = self.grid.parents

    def solutions(self, remaining_cells=grid_indexes):
        '''
        Enumerate all the solutions to this grid by depth first search

        '''

        if not remaining_cells:
            # we made it to the last cell without backtracking - we have a solution
            yield self
            return

        cell_to_set = remaining_cells[0]

        # if there are no possible values in the cell we are considering,
        # the method will yield nothing, and the parent recursive call will
        # continue through its own possible values
        for candidate_value in self.grid[cell_to_set]:
            with self.search_subgrid(cell_to_set, candidate_value):
                yield from self.solutions(remaining_cells[1:])
        
    def display(self):
        '''
        Turn the grid back into visual form

        '''
        formatted_grid = []
        for r in range(GRID_SIZE):
            row = ''
            for c in range(GRID_SIZE):
                value = self.grid[r,c]
                row += str(next(iter(value))) if len(value) == 1 else '.'
            formatted_grid.append(row)
        return formatted_grid

def solve(grid):
    '''
    Read the grid and print the first solution, if one exists

    '''
    solution = next(SudokuGrid(read_grid(grid)).solutions(), None)
    if solution:
        return solution.display()


class SudokuTests(TestCase):
    TEST_GRID = [
        ' 3    9 6',
        '6 2943851',
        '       73',
        '3917   68',
        '    1  42',
        '4   86   ',
        '947 3    ',
        ' 16 95 3 ',
        '8   67  9'
    ]

    SOLVED_TEST_GRID = [
        '534178926',
        '672943851',
        '189652473',
        '391724568',
        '768519342',
        '425386197',
        '947231685',
        '216895734',
        '853467219'
    ]

    IMPOSSIBLE_GRID = [
        '111111111',
        '         ',
        '         ',
        '         ',
        '         ',
        '         ',
        '         ',
        '         ',
        '         '
    ]

    def test_other_cells_affected(self):
        c = other_cells_affected((4, 4))
        self.assertEqual(21, len(c))

        for i in range(9):
            self.assertIn((4, i), c)
            self.assertIn((i, 4), c)

        for i in range(3, 6):
            for j in range(3, 6):
                self.assertIn((i, j), c)

    def test_grid_indexes(self):
        self.assertEqual(GRID_SIZE**2, len(set(grid_indexes)))

    def test_read_grid(self):
        self.assertEqual([((0,1), 1)], list(read_grid([' 1'])))
        self.assertEqual([((1,1), 1)], list(read_grid(['  ', ' 1'])))

    def test_blank_grid(self):
        for idx in grid_indexes:
            self.assertEqual(set(range(1, 10)), blank_grid[idx])
            self.assertNotIn(0, blank_grid[idx])
            self.assertNotIn(10, blank_grid[idx])

    def test_grid_display(self):
        self.assertEqual(
            self.SOLVED_TEST_GRID, 
            SudokuGrid(read_grid(self.SOLVED_TEST_GRID)).display())

    def test_solve(self):
        self.assertEqual(self.SOLVED_TEST_GRID, solve(self.TEST_GRID))

        self.assertEqual(None, solve(self.IMPOSSIBLE_GRID))

if __name__ == '__main__':
    main()
