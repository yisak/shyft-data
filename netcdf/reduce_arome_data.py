from netCDF4 import Dataset
from numpy import where
from numpy import intersect1d
from shyft import shyftdata_dir


def reduce_netcdf(orig, dest, box):
    """
    Very simple script to limit data in orig to portion inside the box.
    """
    x_min, x_max, y_min, y_max = box
    data_vars = orig.variables

    # Limit data
    x = data_vars["x"][:] 
    x1 = where(x >= x_min)[0]
    x2 = where(x <= x_max)[0]
    x_inds = intersect1d(x1, x2, assume_unique=True)
    y = data_vars["y"][:] 
    y1 = where(y >= y_min)[0]
    y2 = where(y <= y_max)[0]
    y_inds = intersect1d(y1, y2, assume_unique=True)

    for (d, v) in orig.dimensions.iteritems():
        if d not in ["x", "y"]: # Copy dimensions
            dest.createDimension(d, len(v))
        elif d == "x":
            dest.createDimension(d, len(x_inds))
        elif d == "y":
            dest.createDimension(d, len(y_inds))

    for (k, v) in data_vars.iteritems():
        # Construct slice
        data_slice = len(v.dimensions)*[slice(None)]
        if "x" in v.dimensions:
            data_slice[v.dimensions.index("x")] = x_inds
        if "y" in v.dimensions:
            data_slice[v.dimensions.index("y")] = y_inds
        # Write all variables back, but slice in xy-direction
        dest.createVariable(k, v.datatype, v.dimensions)
        dest.variables[k][:] = v[tuple(data_slice)]
        if hasattr(v, "grid_mapping"):
            dest.variables[k].grid_mapping = v.grid_mapping
        if k == "projection_lambert":
            dest.variables[k].proj4 = v.proj4
    


if __name__ == "__main__":
    from os import path
    import sys

    fromfile = sys.argv[-2]
    tofile = path.join(sys.argv[-1], path.split(fromfile)[-1])
    if not path.isfile(fromfile):
        raise IOError("File '{}' not found".format(fromfile))
    ids = Dataset(fromfile)
    ods = Dataset(tofile, "w")
    x_min, x_max = -69202.0, 15167.0
    y_min, y_max = 316649.0, 421070.0
    reduce_netcdf(ids, ods, [x_min, x_max, y_min, y_max])
    ods.close()
