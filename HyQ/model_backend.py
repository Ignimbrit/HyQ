import math

import numpy as np

import HyQ.wells
from HyQ.theis import theis_drawdown, jakob_freegw_mod

def calculate_well_dist_mat(well: HyQ.wells.well, shape: tuple, res_x: int, res_y: int) -> np.array:
    welldistmat = np.zeros(shape=shape)

    with np.nditer(welldistmat, flags=['multi_index'], op_flags=['readwrite']) as it:
        for cell in it:
            i, j = it.multi_index
            x = j * res_x
            y = i * res_y
            cell[...] = math.dist([well.x, well.y], [x, y])

    return welldistmat

def calculate_well_drawdown(H0: np.array, t: int, well: HyQ.wells.well, aquiferparams: dict) -> np.array:
    sgrid = np.zeros(shape=H0.shape)
    with np.nditer(sgrid, flags=['multi_index'], op_flags=['readwrite']) as it:
        for cell in it:
            i, j = it.multi_index
            s = theis_drawdown(
                    Q=well.Q,
                    T=aquiferparams["T"],
                    r=well.distmat[i, j],
                    S=aquiferparams["S"],
                    t=t
                )

            if aquiferparams["confined"]:
                s_final = s
            else:
                s_final = jakob_freegw_mod(s = s, H = H0[i, j])

            cell[...] = s_final

    return sgrid
