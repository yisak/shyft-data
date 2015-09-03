from netCDF4 import Dataset
from numpy import where
from numpy import intersect1d


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
    from os.path import pardir
    from os.path import dirname
    from os.path import join

    ibase_dir = join(dirname(__file__), "arome")
    obase_dir = join(dirname(__file__), "arome-testdata")
    id1 = join(ibase_dir, "arome_metcoop_default2_5km_20150823_06.nc")
    id2 = join(ibase_dir, "arome_metcoop_test2_5km_20150823_06.nc")
    od1 = join(obase_dir, "arome_metcoop_red_default2_5km_20150823_06.nc")
    od2 = join(obase_dir, "arome_metcoop_red_test2_5km_20150823_06.nc")
    ids1 = Dataset(id1)
    ods1 = Dataset(od1, "w")
    ids2 = Dataset(id2)
    ods2 = Dataset(od2, "w")
    x_min, x_max = -69202.0, 15167.0
    y_min, y_max = 316649.0, 421070.0
    reduce_netcdf(ids1, ods1, [x_min, x_max, y_min, y_max])
    reduce_netcdf(ids2, ods2, [x_min, x_max, y_min, y_max])
    ods1.close()
    ods2.close()
