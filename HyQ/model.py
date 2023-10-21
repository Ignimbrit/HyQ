import math
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show

import HyQ.wells
from HyQ.wells import well
from HyQ.theis import theis_drawdown, jakob_freegw_mod
from HyQ.model_backend import calculate_well_dist_mat, calculate_well_drawdown, raster_from_scratch

class GWModel:
    def __init__(self):
        self.grid = {}
        self.aquifer = {}
        self.wells = []
        self.timesteps = []
        self.H = []

    def set_grid(self, x_min, y_max, len_x, len_y, res_x, res_y, crs = None):
        self.grid["crs"] = crs

        self.grid["description"], self.grid["arrayshape"], self.grid["affine"] = raster_from_scratch(
            x_min=x_min, y_max=y_max, len_x=len_x, len_y=len_y, res_x=res_x, res_y=res_y
        )

        self.grid["origindist"] = np.zeros(shape = self.grid["arrayshape"])
        with np.nditer(self.grid["origindist"], flags=['multi_index'], op_flags=['readwrite']) as it:
            for cell in it:
                i, j = it.multi_index
                x = j * res_x
                y = i * res_y
                #print(f'j = {j}, x = {x} and i = {i}, y = {y}')
                cell[...] = math.dist([0, 0], [x, y])

    def set_aquiferparams(self, H0, T, S, M, confined):
        self.grid["H0"] = np.full(shape = self.grid["arrayshape"], fill_value=H0)
        self.aquifer["T"] = T
        self.aquifer["S"] = S
        self.aquifer["M"] = M
        self.aquifer["confined"] = confined

    def __calculate_well_dist_mat(self):
        res_x = self.grid["description"]["res_x"]
        res_y = self.grid["description"]["res_y"]
        x_min = self.grid["description"]["x_min"]
        y_max = self.grid["description"]["y_max"]


        for well in self.wells:
            well.distmat = calculate_well_dist_mat(
                well = well,
                shape = self.grid["origindist"].shape,
                res_x = res_x,
                res_y = res_y,
                x_min = x_min,
                y_max = y_max
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

    def plot(self):
        fig, axs = plt.subplots(len(self.H))

        for i, subax in enumerate(axs):
            show(
                self.H[i], transform = self.grid["affine"], ax = subax, title = f'H at t = {self.timesteps[i]}'
            )
            show(
                self.H[i], transform = self.grid["affine"], ax = subax,
                contour=True,
                colors='black'
            )
        plt.show()

    def export_head(self, fp):
        with rasterio.open(
                fp, "w", driver = 'GTiff',
                height = self.grid["arrayshape"][0], width = self.grid["arrayshape"][1], crs = self.grid["crs"],
                count = len(self.H), dtype = self.H[0].dtype, transform = self.grid["affine"]) as dest:
            for i, H in enumerate(self.H):
                dest.write(H, i+1)
