from collections import defaultdict
from itertools import combinations
from math import ceil

rows = range(1, 10)
cols = range(1, 10)

boxes = [(br, bc) for bc in range(1, 4) for br in range(1, 4)]


def box_position(row, col):
    return ceil(row/3), ceil(col/3)


def box_cell_axes(box_idx):
    return range((box_idx-1)*3+1, box_idx*3+1)


def box_cells(box_position):
    box_row, box_col = box_position
    return [(row, col) for row in box_cell_axes(box_row)
                       for col in box_cell_axes(box_col)]


def affected_positions(row, col):
    for affected_row in range(1,10):
        if affected_row == row:
            continue

        yield (affected_row, col)

    for affected_col in range(1,10):
        if affected_col == col:
            continue

        yield (row, affected_col)

    for affected_position in box_cells(box_position(row, col)):
        affected_row, affected_col = affected_position
        if affected_row == row:
            continue

        if affected_col == col:
            continue

        yield affected_position


class Place(object):

    def __init__(self, row, col, value):
        self.row = row
        self.col = col
        self.value = value

    def __repr__(self):
        return f'Place{self.row, self.col, self.value}'

    def perform(self, grid):
        grid.place(self.row, self.col, self.value)


class Remove(object):

    def __init__(self, row, col, value):
        self.row = row
        self.col = col
        self.value = value

    def __repr__(self):
        return f'Remove{self.row, self.col, self.value}'

    def perform(self, grid):
        grid.remove(self.row, self.col, self.value)


class SudokuGrid(object):

    def __init__(self):
        self.placed_grid = {}
        self.grid = { (row, col): set(range(1, 10)) 
                      for row in rows for col in cols }
        self.strategies = [
            self.find_only_one_digit_in_cell,
            self.find_only_one_place_in_row,
            self.find_only_one_place_in_col,
            self.find_only_one_place_in_box,
            self.find_digits_in_one_box_row,
            self.find_digits_in_one_box_col,
            self.find_subsets_in_row,
            self.find_subsets_in_col,
            self.find_subsets_in_box,
        ]

    def place(self, row, col, value):
        self.placed_grid[(row, col)] = value
        self.grid[(row, col)] = set()

        for aff_pos in affected_positions(row, col):
            if value == self.placed_grid.get(aff_pos):
                print(self.formatted_grid())
                raise ValueError(f'want to put {value} at {row, col} but already at {aff_pos}')
            if set([value]) == self.grid[aff_pos]:
                print(self.formatted_grid())
                raise ValueError(f'want to put {value} at {row, col} but its the only option for {aff_pos}')

            self.grid[aff_pos].discard(value)

    def remove(self, row, col, value):
        self.grid[(row, col)].remove(value)

    def row(self, row):
        for col in cols:
            yield row, col, self.grid[row, col]

    def col(self, col):
        for row in rows:
            yield row, col, self.grid[row, col]

    def box(self, box):
        for row, col in box_cells(box):
            yield row, col, self.grid[row, col]

    def remaining_values(self, cells):
        return set(value for _, _, values in cells for value in values)

    def locations_for(self, value, cells):
        return set((row, col) for (row, col, vs) in cells if value in vs)

    def find_only_one_digit_in_cell(self):
        for (row, col), values in self.grid.items():
            if len(values) == 1:
                (value,) = values
                yield Place(row, col, value)
    
    def find_only_one_place_in_row(self):
        for row in rows:
            occurrences = defaultdict(set)
            for _, col, values in self.row(row):
                for value in values:
                    occurrences[value].add(col)

            for value, positions in occurrences.items():
                if len(positions) == 1:
                    (col,) = positions
                    yield Place(row, col, value)

    def find_only_one_place_in_col(self):
        for col in cols:
            occurrences = defaultdict(set)
            for row, _, values in self.col(col):
                for value in values:
                    occurrences[value].add(row)

            for value, positions in occurrences.items():
                if len(positions) == 1:
                    (row,) = positions
                    yield Place(row, col, value)

    def find_only_one_place_in_box(self):
        for box in boxes:
            for row, col, values in self.box(box):
                if len(values) == 1:
                    (value,) = values
                    yield Place(row, col, value)

    def find_digits_in_one_box_row(self):
        for box in boxes:
            box_row, box_col = box
            for digit in self.remaining_values(self.box(box)):
                digit_rows = set()
                for row in box_cell_axes(box_row):
                    for _, col, values in self.row(row):
                        if col not in box_cell_axes(box_col):
                            continue
                        if digit in values:
                            digit_rows.add(row)
                
                if len(digit_rows) == 1:
                    (row,) = digit_rows
                    for _, col, values in self.row(row):
                        if box_position(row, col) == box:
                            continue
                        if digit in values:
                            yield Remove(row, col, digit)

    def find_digits_in_one_box_col(self):
        for box in boxes:
            box_row, box_col = box
            for digit in self.remaining_values(self.box(box)):
                digit_cols = set()
                for col in box_cell_axes(box_col):
                    for row, _, values in self.col(col):
                        if row not in box_cell_axes(box_row):
                            continue
                        if digit in values:
                            digit_cols.add(col)
                
                if len(digit_cols) == 1:
                    (col,) = digit_cols
                    for row, _, values in self.col(col):
                        if box_position(row, col) == box:
                            continue
                        if digit in values:
                            yield Remove(row, col, digit)

    def find_subsets_in_row(self):
        for row in rows:
            remaining_values = self.remaining_values(self.row(row))
            if len(remaining_values) < 2:
                continue

            for fst_val, snd_val in combinations(remaining_values, 2):
                fst_locations = self.locations_for(fst_val, self.row(row))
                snd_locations = self.locations_for(snd_val, self.row(row))

                common_locations = fst_locations & snd_locations
                common_locations = set(loc for loc in common_locations 
                                       if self.grid[loc].issuperset(set([fst_val, snd_val])))
                if len(common_locations) == 2: 
                    (fst_loc, snd_loc) = common_locations
                    if len(fst_locations) > 2 or len(snd_locations) > 2:
                        if self.grid[fst_loc] == self.grid[snd_loc] == set([fst_val, snd_val]):
                            for other_row, other_col in fst_locations - common_locations:
                                yield Remove(other_row, other_col, fst_val)

                            for other_row, other_col in snd_locations - common_locations:
                                yield Remove(other_row, other_col, snd_val)

                    if len(fst_locations) == len(snd_locations) == 2:
                        for val in self.grid[fst_loc] - set([fst_val, snd_val]):
                            fst_row, fst_col = fst_loc
                            yield Remove(fst_row, fst_col, val)

                        for val in self.grid[snd_loc] - set([fst_val, snd_val]):
                            snd_row, snd_col = snd_loc
                            yield Remove(snd_row, snd_col, val)



    def find_subsets_in_col(self):
        for col in cols:
            remaining_values = self.remaining_values(self.col(col))
            if len(remaining_values) < 2:
                continue

            for fst_val, snd_val in combinations(remaining_values, 2):
                fst_locations = self.locations_for(fst_val, self.col(col))
                snd_locations = self.locations_for(snd_val, self.col(col))

                common_locations = fst_locations & snd_locations
                common_locations = set(loc for loc in common_locations 
                                       if self.grid[loc].issuperset(set([fst_val, snd_val])))
                if len(common_locations) == 2: 
                    (fst_loc, snd_loc) = common_locations
                    if len(fst_locations) > 2 or len(snd_locations) > 2:
                        if self.grid[fst_loc] == self.grid[snd_loc] == set([fst_val, snd_val]):
                            for other_row, other_col in fst_locations - common_locations:
                                yield Remove(other_row, other_col, fst_val)

                            for other_row, other_col in snd_locations - common_locations:
                                yield Remove(other_row, other_col, snd_val)

                    if len(fst_locations) == len(snd_locations) == 2:
                        for val in self.grid[fst_loc] - set([fst_val, snd_val]):
                            fst_row, fst_col = fst_loc
                            yield Remove(fst_row, fst_col, val)

                        for val in self.grid[snd_loc] - set([fst_val, snd_val]):
                            snd_row, snd_col = snd_loc
                            yield Remove(snd_row, snd_col, val)


    def find_subsets_in_box(self):
        for box in boxes:
            remaining_values = self.remaining_values(self.box(box))
            if len(remaining_values) < 2:
                continue

            for fst_val, snd_val in combinations(remaining_values, 2):
                fst_locations = self.locations_for(fst_val, self.box(box))
                snd_locations = self.locations_for(snd_val, self.box(box))

                common_locations = fst_locations & snd_locations
                common_locations = set(loc for loc in common_locations 
                                       if self.grid[loc].issuperset(set([fst_val, snd_val])))
                if len(common_locations) == 2: 
                    (fst_loc, snd_loc) = common_locations
                    if len(fst_locations) > 2 or len(snd_locations) > 2:
                        if self.grid[fst_loc] == self.grid[snd_loc] == set([fst_val, snd_val]):
                            for other_row, other_col in fst_locations - common_locations:
                                yield Remove(other_row, other_col, fst_val)

                            for other_row, other_col in snd_locations - common_locations:
                                yield Remove(other_row, other_col, snd_val)

                    if len(fst_locations) == len(snd_locations) == 2:
                        for val in self.grid[fst_loc] - set([fst_val, snd_val]):
                            fst_row, fst_col = fst_loc
                            yield Remove(fst_row, fst_col, val)

                        for val in self.grid[snd_loc] - set([fst_val, snd_val]):
                            snd_row, snd_col = snd_loc
                            yield Remove(snd_row, snd_col, val)


    def find(self):
        while True:
            for strategy in self.strategies:
                next_result = next(strategy(), None)
                if next_result:
                    next_result.perform(self)
                    break
            else:
                return

    def load(self, grid):
        for row_num, row in enumerate(grid, 1):
            for col_num, cell in enumerate(row, 1):
                if cell != ' ':
                    self.place(row_num, col_num, int(cell))

    def formatted_grid(self):
        grid_str = []

        for row in range(1, 10):
            if row in (4, 7):
                grid_str.append('-'*12)
            rowstr = ''
            for col in range(1, 10):
                if col in (4, 7):
                    rowstr += '|'
                rowstr += str(self.placed_grid.get((row, col), ' '))
            grid_str.append(rowstr)

        return '\n'.join(grid_str)


HARD_TEST_GRID = [
    '   8 1   ',
    '7    9 5 ',
    '   2  4  ',
    '9        ',
    '6   1 34 ',
    ' 5   31  ',
    '  2      ',
    '   1  6  ',
    '53  64  9'
]

s = SudokuGrid()

s.load(HARD_TEST_GRID)
s.find()
print(s.formatted_grid())
