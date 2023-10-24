import math
from pathlib import Path
import os
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show

from osgeo import osr
from osgeo import ogr
from osgeo import gdal

import hyq.wells
from hyq.wells import well
from hyq.theis import theis_drawdown, jakob_freegw_mod
from hyq.model_backend import calculate_well_dist_mat, calculate_well_drawdown, raster_from_scratch

class GWModel:
    '''Simulate the impact of pumping groundwater from an aquifer on its head

    This class is the backbone to set up and run a model to calculate what happens to an aquifers head (which
    for unconfined aquifers we shall think of as "the groundwater surface" for now) when you start using pumping
    wells to extract groundwater

    Attributes:
        grid: A dict containing the spatial discretisation of the model. Set up by set_grid method.
        aquifer: A dict containing aquifer parameters. Set up by set_aquiferparams method.
        wells: A list of pumping wells. Set up by add_wells method.
        timesteps: A list of points in time [seconds since pumping started] to model. Set up by set_timesteps method.
        H: A list of numpy arrays giving the aquifer head at the designated timesteps. Model result.

    '''
    def __init__(self):
        '''Initialize the new model
        '''
        self.grid = {}
        self.aquifer = {}
        self.wells = []
        self.timesteps = []
        self.H = []

    def set_grid(
            self, x_min: float, y_max: float, len_x: float, len_y: float, res_x: float, res_y: float, crs = None
    ) -> None:
        '''Define the spatial discretization of the model

        The impact of a well on the groundwater head is strongly dependent on the distance of the observation
        point from said well. Therefore, some thought should be devoted to the dimension of your model,
        the resolution of the calculation raster and the position of the model in real world space. As for the latter,
        HyQ expects its model to be located in some form of cartesian space.

        Args:
            x_min: Easting of the "left" model border [m]
            y_max: Northing of the "upper" model border [m]
            len_x: Width of the model (east-west length) [m]
            len_y: Height of the model (south-north length) [m]
            res_x: Model resolution in east-west direction [m]
            res_y: Model resolution in south-north direction [m]
            crs: Either None (the default) or something that rasterio will accept as a valid crs
        '''
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

    def set_aquiferparams(self, H0: float, T: float, S: float, M: float, confined: bool) -> None:
        '''Define the model aquifer

        HyQ by design supports only single-aquifer-models. The impact that pumping groundwater from the aquifer
        will have on its head depends on a couple of mostly hydrogeological parameters, which can be specified here.

        Args:
            H0: Initial unified aquifer head [m]
            T: Transmissivity of the aquifer [m²/s]
            S: Storativity of the aquifer [-] (dimensionless)
            M: Thickness of the aquifer [m]
            confined: whether the aquifer is confined
        '''
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

    def add_wells(self, *args: hyq.wells.well) -> None:
        '''Add pumping wells to the model that extract water from the aquifer

        Args:
            *args: A well class object as defined by hyq.wells.well
        '''
        for arg in args:
            if isinstance(arg, hyq.wells.well):
                self.wells.append(arg)
        self.__calculate_well_dist_mat()

    def set_timesteps(self, tlist: list) -> None:
        '''Set points in time for which to calculate aquifer heads

        Model results are calculated for concrete points in time. Which points, that can be set here.

        Args:
            tlist: A list with integers that are times in seconds since pumping started.
        '''
        self.timesteps = tlist

    def run(self):
        '''Actually run the model calculations
        '''
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
        '''Simple plotting utility to visually inspect the results of a model run
        '''
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

    def export_head(self, fp: str) -> None:
        '''Export calculated heads to raster in (Geo-)Tiff-Format

        After you run a (more or less) successfull model simulation you can export the resulting heads as rasters
        to Geo-Tiff. That way you can inspect or postprocess them in third-party-programs such as QGIS.

        Args:
            fp: Output filepath. Should end with .tiff, e.g.: "path/to/my.tiff"

        '''
        with rasterio.open(
                fp, "w", driver = 'GTiff',
                height = self.grid["arrayshape"][0], width = self.grid["arrayshape"][1], crs = self.grid["crs"],
                count = len(self.H), dtype = self.H[0].dtype, transform = self.grid["affine"]) as dest:
            for i, H in enumerate(self.H):
                dest.write(H, i+1)

    def export_contours_head(self, gpkgpath: str, levels: list) -> None:
        '''Export contours for the modeled aquifer heads as Vector Geodata

        This method allows you to calculate contours for the head rasters in your model and saves the results in a
        GeoPackage.

        Args:
            gpkgpath: Output filepath. Should end with .gpkg, e.g.: "path/to/my.gpkg"
            levels: list of floats that give the levels at which contours should be calculated.
        '''
        fd, path = tempfile.mkstemp(suffix=".tiff")

        try:
            self.export_head(path)

            contourDs = ogr.GetDriverByName("GPKG").CreateDataSource(gpkgpath)

            for i, H in enumerate(self.H):
                # Open tif file as select band
                rasterDs = gdal.Open(path)
                rasterBand = rasterDs.GetRasterBand(i+1)
                proj = osr.SpatialReference(wkt=rasterDs.GetProjection())

                # Get elevation as numpy array
                elevArray = rasterBand.ReadAsArray()

                # define not a number
                demNan = -9999

                # get dem max and min
                demMax = elevArray.max()
                demMin = elevArray[elevArray != demNan].min()

                # define layer name and spatial
                contourShp = contourDs.CreateLayer(f"cntr_{i+1}", proj)

                # define fields of id and elev
                fieldDef = ogr.FieldDefn("ID", ogr.OFTInteger)
                contourShp.CreateField(fieldDef)
                fieldDef = ogr.FieldDefn("elev", ogr.OFTReal)
                contourShp.CreateField(fieldDef)

                conList = levels

                gdal.ContourGenerate(rasterBand, 0, 0, conList, 1, demNan, contourShp, 0, 1)

        finally:
            contourDs.Destroy()
            os.remove(path)
