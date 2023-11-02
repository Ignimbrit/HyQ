from importlib.resources import files
import fiona


def dataset_exp1():
    rastlocs = {
        "H0_raster": files("hyq").joinpath("data/exp1_pseudoH0.tif").absolute()
    }

    veclocs = {}

    vecpath_1 = files("hyq").joinpath("data/sptutorial_1.gpkg").absolute()
    for layer in fiona.listlayers(vecpath_1):
        veclocs[layer] = {"path": vecpath_1, "layer": layer}

    return (rastlocs, veclocs)
