# module level doc-string
__doc__ = """
hyq - simple analytical groundwater models
=====================================================================

**hyq** is a Python package providing a simple way to model the impact
of groundwater pumping wells on the head (~groundwater surface level) of
an aquifer. It is build around Theis Well Equation.

Main Features
-------------

  - Fast and simple one-aquifer analogue models
  - Multiple wells with different locations and pumping rates
  - Calculate impact for several points in time 
  - Export results as raster or contour lines for postprocessing with GIS.
"""


from hyq.model import GWModel
from hyq.wells import well