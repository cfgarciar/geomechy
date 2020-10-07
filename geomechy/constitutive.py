# AUTOGENERATED! DO NOT EDIT! File to edit: 02_constitutive.ipynb (unless otherwise specified).

__all__ = ['Elastic', 'PlaneStrain', 'PlaneStress', 'TransverseIsotropic']

# Cell
from .base import BaseMaterial, Properties
import numpy as np

# Cell
class Elastic(BaseMaterial):

    def __init__(self, props):

        #Call the BaseMaterial constructor
        BaseMaterial.__init__(self, props)

        #Create the hookean matrix
        fc1 = self.E/((1+self.nu)*(1-2*self.nu))
        fc2 = (1-2*self.nu)/2
        D11 = self.nu*(np.ones(3)-np.eye(3))+(1-self.nu)*np.eye(3)
        D12 = np.zeros((3,3))
        D21 = D12.copy()
        D22 = fc2*np.eye(3)

        self.De = fc1*np.block([[D11,D12],[D21,D22]])

    def getStress(self, deformation):
        sigma = np.matmul(self.De, deformation.eps)
        return sigma, self.De

    def getTangent(self):
        return self.De

# Cell
class PlaneStrain(BaseMaterial):

    def __init__(self, props):

        #Call the BaseMaterial constructor
        BaseMaterial.__init__(self, props)

        #Create the hookean matrix
        fc1 = self.E/((1+self.nu)*(1-2*self.nu))
        fc2 = (1-2*self.nu)/2
        D11 = self.nu*(np.ones(2)-np.eye(2))+(1-self.nu)*np.eye(2)
        D12 = np.zeros((2,1))
        D21 = np.zeros((1,2))
        D22 = np.array([fc2]).reshape((1,1))

        self.De = fc1*np.vstack([np.hstack([D11,D12]),np.hstack([D21,D22])])

    def getStress(self, deformation):
        sigma = np.matmul(self.De, deformation.eps)
        return sigma, self.De

    def getTangent(self):
        return self.De

# Cell
class PlaneStress(BaseMaterial):

    def __init__(self, props):

        #Call the BaseMaterial constructor
        BaseMaterial.__init__(self, props)

        #Create the hookean matrix
        fc1 = self.E/(1-self.nu**2)
        fc2 = 1-self.nu
        D11 = self.nu*(np.ones(2)-np.eye(2))+np.eye(2)
        D12 = np.zeros((2,1))
        D21 = np.zeros((1,2))
        D22 = np.array([fc2]).reshape((1,1))

        self.De = fc1*np.vstack([np.hstack([D11,D12]),np.hstack([D21,D22])])

    def getStress(self, deformation):
        sigma = np.matmul(self.De, deformation.eps)
        return sigma, self.De

    def getTangent(self):
        return self.De

# Cell
class TransverseIsotropic(BaseMaterial):

    def __init__(self, props):

        #Call the BaseMaterial constructor
        BaseMaterial.__init__(self, props)

        #Create the hookean matrix
        fc1 = self.E2/(2*(1+self.nu23))

        D11 = np.ones((3,3))
        D11[0,0] *= 1./self.E1
        D11[1,1] *= 1./self.E2
        D11[2,2] *= 1./self.E2
        D11[0,1] *= -1.*self.nu12/self.E2
        D11[1,0]  = D11[0,1].copy()
        D11[0,2] *= -1.*self.nu12/self.E2
        D11[2,0]  = D11[0,2].copy()
        D11[1,2] *= -1.*self.nu23/self.E2
        D11[2,1]  = D11[1,2].copy()
        D12 = np.zeros((3,3))
        D21 = D12.copy()
        D22 = np.diagflat([self.G12, self.G12, fc1])

        self.De = np.linalg.inv(np.block([[D11,D12],[D21,D22]]))

    def getStress(self, deformation):
        sigma = np.matmul(self.De, deformation.eps)
        return sigma, self.De

    def getTangent(self):
        return self.De