# AUTOGENERATED! DO NOT EDIT! File to edit: 04_io.ipynb (unless otherwise specified).

__all__ = ['jsonReader']

# Cell
import json
import numpy as np
from .utils import units

# Cell
def jsonReader(jsonFile):
    try:
        with open(jsonFile) as f:
            data = json.load(f)

        #  Dict keys check ---------------------------------------------
        assert list(data.keys()) == ['Nodes', 'Elements', 'Groups', 'Materials', 'Physics',
                                     'Constitutive', 'FEM', 'Solver', 'Modules', 'Writers']

        #  Nodes Check ------------------------------------------------
        assert list(data["Nodes"].keys()) in [['dim', 'coords']]
        assert np.array(data["Nodes"]["coords"]).shape[0]>1
        assert np.array(data["Nodes"]["coords"]).shape[1]>=1
        assert data["Nodes"]["dim"] in units["distance"]

        # Elements Check ----------------------------------------------

        return data
    except:
        print("json invalid structure")
