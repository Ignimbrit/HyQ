import math

import numpy as np

import HyQ.wells
from HyQ.wells import well
from HyQ.theis import theis_drawdown, jakob_freegw_mod
from HyQ.model_backend import calculate_well_dist_mat, calculate_well_drawdown

class GWModel:
    def __init__(self):
        self.grid = {}
        self.aquifer = {}
        self.wells = []
        self.timesteps = []
        self.H = []

    def set_grid(self, len_x, len_y, res_x, res_y):
        self.grid["len_x"] = len_x
        self.grid["len_y"] = len_y
        self.grid["res_x"] = res_x
        self.grid["res_y"] = res_y
        self.grid["ncol"] = int(len_x / res_x) + 1
        self.grid["nrow"] = int(len_y / res_y) + 1

        self.grid["dist"] = np.zeros(shape = [self.grid["nrow"], self.grid["ncol"]])
        with np.nditer(self.grid["dist"], flags=['multi_index'], op_flags=['readwrite']) as it:
            for cell in it:
                i, j = it.multi_index
                x = j * self.grid["res_x"]
                y = i * self.grid["res_y"]
                #print(f'j = {j}, x = {x} and i = {i}, y = {y}')
                cell[...] = math.dist([0, 0], [x, y])

    def set_aquiferparams(self, H0, T, S, M, confined):
        self.grid["H0"] = np.full(shape = [self.grid["nrow"], self.grid["ncol"]], fill_value=H0)
        self.aquifer["T"] = T
        self.aquifer["S"] = S
        self.aquifer["M"] = M
        self.aquifer["confined"] = confined

    def __calculate_well_dist_mat(self):
        for well in self.wells:
            well.distmat = calculate_well_dist_mat(
                well = well,
                shape = self.grid["dist"].shape,
                res_x = self.grid["res_x"],
                res_y = self.grid["res_y"]
            )

    def add_wells(self, *args):
        for arg in args:
            if isinstance(arg, HyQ.wells.well):
                self.wells.append(arg)
        self.__calculate_well_dist_mat()

    def set_timesteps(self, tlist):
        self.timesteps = tlist

    def run(self):
        H0 = self.grid["H0"]
        for t in self.timesteps:
            H = H0
            for well in self.wells:
                sgrid = calculate_well_drawdown(
                    H0 = H0, t = t, well = well, aquiferparams = self.aquifer
                )
                well.drawdown = sgrid
                H = H - sgrid
            self.H.append(H)

