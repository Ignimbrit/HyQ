import math

import numpy as np

import HyQ.wells

def calculate_well_dist_mat(well: HyQ.wells.well, shape: tuple, res_x: int, res_y: int) -> np.array:
    welldistmat = np.zeros(shape=shape)

    with np.nditer(welldistmat, flags=['multi_index'], op_flags=['readwrite']) as it:
        for cell in it:
            i, j = it.multi_index
            x = j * res_x
            y = i * res_y
            cell[...] = math.dist([well.x, well.y], [x, y])

    return welldistmat