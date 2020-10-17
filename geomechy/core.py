# AUTOGENERATED! DO NOT EDIT! File to edit: 05_Solvers.ipynb (unless otherwise specified).

__all__ = ['NodeSet', 'ElementSet', 'GroupSet', 'MaterialSet', 'ShapeFunctionsManager', 'ConstitutiveManager',
           'ElementManager']

# Cell
import numpy as np
import scipy
from scipy.sparse import csr_matrix

from .base import ItemDict, BaseElement
from .utils import *
from .io import jsonReader
from .materials import *
from .shape import *
from .constitutive import *

# Cell
class NodeSet(ItemDict):

    def readFromDict(self, data):
        nodes_dict    = data["Nodes"]
        self.numNodes = len(nodes_dict["coords"])
        self.dimNodes = nodes_dict["dim"]

        for node in nodes_dict["coords"]:
            dim = eval(self.dimNodes)
            self.add(node[0], np.array(node[1:])*dim)

    def getNodeCoords(self, nodeId):
        return self.get(nodeId)

# Cell
class ElementSet(ItemDict):

    def readFromDict(self, data):
        elems_dict = data["Elements"]
        self.elementType = elems_dict["elementType"]
        self.numElements = len(elems_dict["elems"])

        max_node = np.max([np.max(elem[1:]) for elem in elems_dict["elems"]])
        num_node = len(elems_dict["elems"][0][1:])

        sparse_row  = np.array(range(num_node))
        sparse_data = np.ones(num_node)

        for elem in elems_dict["elems"]:
            sparse_col = np.sort(np.array(elem[1:])-1, axis=None)
            sparse_Le  = csr_matrix((sparse_data, (sparse_row, sparse_col)), shape=(num_node, max_node))

            self.add(elem[0], {"Nodes":elem[1:],"Le":sparse_Le})

    def getElementNodes(self, elemId):
        return self.get(elemId)

# Cell
class GroupSet(ItemDict):
    def readFromDict(self, data):
        nodeGroups    = data["NodeGroups"]
        elementGroups = data["ElementGroups"]

        for group in nodeGroups:
            self.add(group["name"],group["nodes"])

        for group in elementGroups:
            self.add(group["name"],group["elements"])

# Cell
class MaterialSet(dict):

    def __init__(self, material):

        fluids = material["Fluids"]
        media  = material["PorousMedia"]
        temp   = material["Temp"]

        for idx, f in enumerate(fluids):
            name = f["name"]
            if f["Type"] == "Water":
                w = Water(f)
                self[name] = w
            elif f["Type"] == "Oil":
                o = Oil(f)
                self[name] = o
            elif f["Type"] == "Gas":
                g = Gas(f)
                self[name] = g
            elif f["Type"] == "Air":
                a = Air(f)
                self[name] = a
            else:
                pass

        for idx, m in enumerate(media):
            name = m["name"]
            if m["Type"] == "Soil":
                s = Soil(m)
                self[name] = s
            elif m["Type"] == "Rock":
                r = Rock(m)
                self[name] = r
            else:
                pass

    def getMaterial(self, materialId):
        return self.get(materialId)

    def getData(self, Ids):
        return {Id:self[Id] for Id in Ids}

# Cell
class ShapeFunctionsManager(ItemDict):

    def __init__(self, nodeSet, elemSet, reduced=False):
        self.nodeSet = nodeSet
        self.elemSet = elemSet
        self.reduced = reduced

        if not self.elemSet.elementType:
            e1_nodes  = self.elemSet.getElementNodes(1)
            e1_coords = np.array([self.nodeSet.getNodeCoords(c) for c in e1_nodes])
            self.elementType = getElemetType(e1_coords)
        else:
            self.elementType = self.elemSet.elementType

        self.gp, self.we = getGaussPoints(elemType=self.elementType, reduced=self.reduced)

    def getShapeFunc(self):
        all_N = []
        all_dN = []
        for gp in self.gp:
            N, dN = getAllShapeFunctions(self.elementType, gp)
            all_N.append(N)
            all_dN.append(dN)
        self.N, self.dN = all_N, all_dN

        for key, value in self.elemSet.items():
            self[key] = {"gp": self.gp, "we": self.we,"N":self.N, "dN":self.dN}

    def getShapeData(self, elementId):
        return self.get(elementId)

# Cell
class ConstitutiveManager(ItemDict):

    def __init__(self, constitutive):

        for idx, c in enumerate(constitutive):

            if c["Model"] == "Elastic":
                elastic = Elastic(c["params"])
                self.add(c["name"],elastic)

            elif c["Model"] == "PlaneStrain":
                planeStrain = PlaneStrain(c["params"])
                self.add(c["name"],planeStrain)

            elif c["Model"] == "PlaneStress":
                planeStess = PlaneStess(c["params"])
                self.add(c["name"],planeStress)

            elif c["Model"] == "TransverseIsotropic":
                transverseIsotropic= TransverseIsotropic(c["params"])
                self.add(c["name"],transverseIsotropic)

            elif c["Model"] == "MCC":
                mcc= MCC(c["params"])
                self.add(c["name"],mcc)

    def getConstitutive(self, constitutiveId):
        return self.get(constitutiveId)

# Cell
class ElementManager(ItemDict):

    def __init__(self, nodes, elems, groups, shapes, mats, constis):
        ItemDict.__init__(self)
        self.numNodes = nodes.numNodes
        self.numElems = elems.numElements
        self.nodes    = nodes
        self.elems    = elems
        self.groups   = groups
        self.shapes   = shapes
        self.mats     = mats
        self.constis  = constis

        for Id, dataElem in elems.items():
            el = self.elems.getData([Id])
            no = self.nodes.getData(el[Id]["Nodes"])
            gr = self.groups["ElementGroups"]
            sh = self.shapes.getShapeData(Id)

            for item in gr:
                if Id in list(item.values())[0]["elements"]:
                    ma = self.mats.getData(list(item.values())[0]["materials"])

            for name,_ in self.constis.items():
                if name in ma:
                    co = self.constis[name]

            element = BaseElement(Id, no, el, gr, sh, ma, co)
            self.add(Id, element)


    def add(self, Id, item):
        self[Id] = item

# Cell
import numpy as np
import scipy
from scipy.sparse.linalg import spsolve
from scipy.io import loadmat
import torch
import time
from .base import BaseLinearSolver
from .utils import lanczos, arnoldi