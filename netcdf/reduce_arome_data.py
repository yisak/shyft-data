from __future__ import print_function
from __future__ import absolute_import
from netCDF4 import Dataset
import numpy as np
from shyft import shyftdata_dir
from pyproj import Proj
from pyproj import transform


def reduce_netcdf(orig, dest, epsg, box):
    """
    Very simple script to limit data in orig to portion inside the box.
    """
    data_vars = orig.variables
    x = data_vars["x"][:] 
    y = data_vars["y"][:] 

    # Project box in epsg coordinates to dataset coordinates
    #for v in data_vars.itervalues():
    for v in data_vars.values():
        if hasattr(v, "grid_mapping"):
            #target_cs = "{} +towgs84=0,0,0".format(data_vars[v.grid_mapping].proj4)
            target_cs = data_vars[v.grid_mapping].proj4
            box_cs = ("+proj=utm +zone={} +ellps={} +datum={}"
                      " +units=m +no_defs".format(int(epsg) - 32600, "WGS84", "WGS84"))
            x_min, x_max, y_min, y_max  = box
            b_x = x_min, x_max, x_max, x_min
            b_y = y_max, y_max, y_min, y_min
            b_x, b_y = transform(Proj(box_cs), Proj(target_cs), b_x, b_y)
            x_min, x_max = min(b_x), max(b_x)
            y_min, y_max = min(b_y), max(b_y)
            break

    # Limit data
    x_mask = (x >= x_min) == (x <= x_max)
    y_mask = (y >= y_min) == (y <= y_max)
    n_x = np.count_nonzero(x_mask)
    n_y = np.count_nonzero(y_mask)

    #for (d, v) in orig.dimensions.iteritems():
    for (d, v) in orig.dimensions.items():
        if d not in ["x", "y"]: # Copy dimensions
            dest.createDimension(d, len(v))
        elif d == "x":
            dest.createDimension(d, n_x)
        elif d == "y":
            dest.createDimension(d, n_y)

    #for (k, v) in data_vars.iteritems():
    for (k, v) in data_vars.items():
        # Construct slice
        data_slice = len(v.dimensions)*[slice(None)]
        if "x" in v.dimensions:
            data_slice[v.dimensions.index("x")] = x_mask
        if "y" in v.dimensions:
            data_slice[v.dimensions.index("y")] = y_mask
        # Write all variables back, but slice in xy-direction
        dest.createVariable(k, v.datatype, v.dimensions)
        dest.variables[k][:] = v[tuple(data_slice)]
#        if hasattr(v, "grid_mapping"):
#            dest.variables[k].grid_mapping = v.grid_mapping
#        if k == "projection_lambert":
#            dest.variables[k].proj4 = v.proj4
        dest.variables[k].setncatts({k_attr: v.getncattr(k_attr) for k_attr in v.ncattrs()})
    


if __name__ == "__main__":
    from os import path
    import sys

    fromfile = sys.argv[-2]
    tofile = path.join(sys.argv[-1], path.split(fromfile)[-1])
    if not path.isfile(fromfile):
        raise IOError("File '{}' not found".format(fromfile))
    ids = Dataset(fromfile)
    ods = Dataset(tofile, "w")
    epsg = "32633"
    x_min, x_max =  21000.0,  260000.0
    y_min, y_max = 6840000.0, 6900000.0
    reduce_netcdf(ids, ods, epsg, [x_min, x_max, y_min, y_max])
    ods.close()
