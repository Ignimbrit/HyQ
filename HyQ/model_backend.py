import math

import numpy as np
import rasterio

import HyQ.wells
from HyQ.theis import theis_drawdown, jakob_freegw_mod

def raster_from_scratch(x_min: float, y_max: float, len_x: float, len_y: float, res_x: float, res_y: float):
    new_griddescription = {
        "x_min": x_min, "y_max": y_max, "len_x": len_x, "len_y": len_y, "res_x": res_x, "res_y": res_y
    }

    new_transform = rasterio.transform.from_origin(
        west=x_min,
        north=y_max,
        xsize=res_x,
        ysize=res_y
    )

    new_arrayshape = (math.ceil((len_y/res_y)), math.ceil((len_x/res_x)))

    return (new_griddescription, new_arrayshape, new_transform)

def calculate_well_dist_mat(
        well: HyQ.wells.well, shape: tuple, res_x: float, res_y: float, x_min: float, y_max: float) -> np.array:

    welldistmat = np.zeros(shape=shape)

    with np.nditer(welldistmat, flags=['multi_index'], op_flags=['readwrite']) as it:
        for cell in it:
            i, j = it.multi_index
            x = x_min + (j * res_x)
            y = y_max - (i * res_y)
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
