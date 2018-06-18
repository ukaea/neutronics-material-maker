# -*- coding: utf-8 -*-
"""
Created on Thu May  3 20:51:25 2018

@author: matti
"""

# =============================================================================
# The home of base material objects. Use classes in here to make new materials.
# =============================================================================

import numpy as np
from functools import wraps  # TODO: Improve wrapper syntax. Looks ugly
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from neutronics_material_maker.nmm import Material, Element, Compound
from thermo import Chemical
from neutronics_material_maker.utilities import (list_array, array_or_num,
                                                 kgm3togcm3,
                                                 gcm3tobcm, apuctobcm)


def matproperty(Tmin, Tmax):
    '''
    Material property decorator object
    Checks that input T vector is within bounds
    Handles floats and arrays
    '''
    def decorator(f):
        def wrapper(*args, **kwargs):
            T = list_array(args[0])

            if not (T <= Tmax).all():
                raise ValueError('Material property not valid outside of tempe'
                                 f'rature range: {T} > Tmax = {Tmax}')
            if not (T >= Tmin).all():
                raise ValueError('Material property not valid outside of tempe'
                                 f'rature range: {T} < Tmin = {Tmin}')
            T = array_or_num(T)
            return f(T, **kwargs)
        return wrapper
    return decorator


def __raiseError__():
    raise NotImplementedError('This Material has not yet been given this '
                              'property. Please add it.')


class _Void(Material):
    name = 'Void'
    T0 = 293.15  # for now
    
    def __init__(self):
        super().__init__(material_card_name=self.name,
                         density_g_per_cm3=0,
                         density_atoms_per_barn_per_cm=0,
                         elements=[ ],
                         element_mass_fractions=[ ],
                         temperature_K=self.T0)


class MfMaterial(Material):
    T0 = 293.15  # Default temperature for all materials

    def __init__(self, **kwargs):
        self.T0 = kwargs.get('T', self.T0)  # Opens up T as kwarg if needed
        try:  # Set density if a rho property exists
            self.density = self.rho(self.T0)
        except NotImplementedError:
            if self.density is None:
                raise ValueError('No density (value or T-function) specified.')
        super().__init__(material_card_name=self.name,
                         density_g_per_cm3=kgm3togcm3(self.density),
                         density_atoms_per_barn_per_cm=self.brho,
                         elements=[Element(e) for e in self.mf.keys()],
                         element_mass_fractions=self.mf.values(),
                         temperature_K=self.T0)
# =============================================================================
#         try:  # Set density if a rho property exists
#             self.density = self.rho(self.T0)
#             self.density_g_per_cm3 = kgm3togcm3(self.density)
#         except NotImplementedError:
#             pass
# =============================================================================

    @staticmethod
    def mu(T):
        '''
        Poisson's ratio
        '''
        return 0.33

    @staticmethod
    def k(T):
        '''
        Thermal conductivity in W.m/K
        '''
        __raiseError__()

    @staticmethod
    def E(T):
        '''
        Young's modulus in GPa
        '''
        __raiseError__()

    @staticmethod
    def Cp(T):
        '''
        Specific heat in J/kg/K
        '''
        __raiseError__()

    @staticmethod
    def CTE(T):
        '''
        Mean coefficient of thermal expansion in 10**-6/T
        '''
        __raiseError__()

    @staticmethod
    def rho(T):
        '''
        Mass density in kg/m**3
        '''
        __raiseError__()

    @staticmethod
    def erho(T):
        '''
        Electrical resistivity in 10^(-8)Ohm.m
        '''
        __raiseError__()

    @staticmethod
    def Ms(T):
        '''
        Magnetic saturation in Am^2/kg
        '''
        __raiseError__()

    @staticmethod
    def Mt(T):
        '''
        Viscous remanent magnetisation in Am^2/kg
        '''
        __raiseError__()

    @staticmethod
    def Hc(T):
        '''
        Coercive field in A/m
        '''
        __raiseError__()

    @staticmethod
    def Sy(T):
        '''
        Minimum yield stress in MPa
        '''
        __raiseError__()

    @staticmethod
    def Savg(T):
        '''
        Average yield stress in MPa
        '''
        __raiseError__()

    @staticmethod
    def Su(T):
        '''
        Minimum ultimate tensile stress in MPa
        '''
        __raiseError__()

    @staticmethod
    def Suavg(T):
        '''
        Average ultimate tensile stress in MPa
        '''
        __raiseError__()

    @property
    def T(self):
        '''
        Temperature: this is a pythonic property, but not an actual material
        property!
        '''
        return self.T0

    @T.setter
    def T(self, value: 'Kelvin'):
        try:
            self.density_g_per_cm3 = float(kgm3togcm3(self.rho(value)))
            self.density = float(self.rho(value))
        except NotImplementedError:
            self.density_g_per_cm3 = float(kgm3togcm3(self.density))
        self.T0 = value


class Superconductor(object):
    '''
    Presently gratutious use of multiple inheritance to convey plot function
    and avoid repetition. In future perhaps also a useful thing.
    '''

    def plot_SC(self, Bmin, Bmax, Tmin, Tmax, eps=None, n=101, m=100):
        '''
        Plots superconducting surface parameterisation
        strain `eps` only used for Nb3Sn
        '''
        jc = np.zeros([m, n])
        B = np.linspace(Bmin, Bmax, n)
        T = np.linspace(Tmin, Tmax, m)
        for j, b in enumerate(B):
            for i, t in enumerate(T):
                args = (b, t, eps) if eps else (b, t)
                jc[i, j] = self.Jc(*args)
        fig = plt.figure()
        B, T = np.meshgrid(B, T)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_title(self.name)
        ax.set_xlabel('B [T]')
        ax.set_ylabel('T [K]')
        ax.set_zlabel('$j_{c}$ [A/mm^2]')
        ax.plot_surface(B, T, jc, cmap=plt.cm.viridis)
        ax.view_init(30, 45)

    def Jc(self):
        __raiseError__()

    @staticmethod
    def _handle_ij(number):
        '''
        Takes the real part of the imagniary number that results from
        exponing a negative number with a fraction
        '''
        # return np.sqrt(number.real**2+number.imag**2)
        return number.real


class NbTiSuperconductor(MfMaterial, Superconductor):
    mf = None
    name = None
    rho = None
    brho = None
    # Superconducting parameterisation
    C_0 = None
    Bc_20 = None
    Tc_0 = None
    alpha = None
    beta = None
    gamma = None

    def Bc2(self, T):
        '''
        Critical field \n
        :math:`B_{C2}^{*}(T) = B_{C20}(1-(\\frac{T}{T_{C0}})^{1.7})`
        '''
        return self.Bc_20*(1-(T/self.Tc_0)**1.7)

    def Jc(self, B, T):
        '''
        Critical current \n
        :math:`j_{c}(B, T) = \\frac{C_{0}}{B}(1-(\\frac{T}{T_{C0}})^{1.7})
        ^{\gamma}(\\frac{B}{B_{C2}(T)})^{\\alpha}(1-(\\frac{B}{B_{C2}(T)}))
        ^{\\beta}`
        '''
        a = self.C_0/B*(1-(T/self.Tc_0)**1.7)**self.gamma
        ii = B/self.Bc2(T)
        b = ii**self.alpha
        # The below is an "elegant" dodge of numpy RuntimeWarnings encountered
        # when raising a negative number to a fractional power, which in this
        # parameterisation only occurs if a non-physical (<0) current density
        # is returned.
        # TODO: Check the above..
        c = (1-ii)**self.beta if 1-ii > 0 else 0
        return a*b*c


class NbSnSuperconductor(MfMaterial, Superconductor):
    mf = None
    name = None
    rho = None
    brho = None
    # Superconducting parameterisation
    C_a1 = None
    C_a2 = None
    eps_0a = None
    eps_m = None
    B_c20m = None
    T_c0max = None
    C = None
    p = None
    q = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.eps_sh = self.C_a2*self.eps_0a/np.sqrt(self.C_a1**2-self.C_a2**2)

    def Tc_star(self, B, eps):
        '''
        Critical temperature \n
        :math:`T_{C}^{*}(B, {\epsilon}) = T_{C0max}^{*}s({\epsilon})^{1/3}
        (1-b_{0})^{1/1.52}`
        '''
        if B == 0:
            return self.T_c0max*self.s(eps)**(1/3)
        else:
            b = (1-self.Bc2_star(0, eps))**(1/1.52j)
            b = self._handle_ij(b)
            return self.T_c0max*self.s(eps)**(1/3) * b

    def Bc2_star(self, T, eps):
        '''
        Critical field \n
        :math:`B_{C}^{*}(T, {\epsilon}) = B_{C20max}^{*}s({\epsilon})
        (1-t^{1.52})`
        '''
        if T == 0:
            return self.B_c20m*self.s(eps)
        else:
            return self.B_c20m*self.s(eps)*(1-(self.t152(T, eps)))

    def Jc(self, B, T, eps):
        '''
        Critical current \n
        :math:`j_{c} = \\frac{C}{B}s({\epsilon})(1-t^{1.52})(1-t^{2})b^{p}
        (1-b)^{q}`
        '''
        b = self.b(B, T, eps)
        t = self.t(T, eps)
        # Ensure physical current density with max (j, 0)
        # Limits of paramterisation likely to be encountered sooner
        return max((self.C/B*self.s(eps)*(1-self.t152(T, eps)) *
                   (1-t**2)*b**self.p)*(1-b**self.q), 0)

    def t152(self, T, eps):
        # 1.52 = 30000/19736
        t = self.t(T, eps)**1.52j
        t = self._handle_ij(t)
        return t

    def t(self, T, eps):
        '''
        Reduced temperature \n
        :math:`t = \\frac{T}{T_{C}^{*}(0, {\epsilon})}`
        '''
        return T/self.Tc_star(0, eps)

    def b(self, B, T, eps):
        '''
        Reduced magnetic field \n
        :math:`b = \\frac{B}{B_{C2}^{*}(0,{\epsilon})}`
        '''
        return B/self.Bc2_star(T, eps)

    def s(self, eps):
        '''
        Strain function \n
        :math:`s({\epsilon}) = 1+ \\frac{1}{1-C_{a1}{\epsilon}_{0,a}}[C_{a1}
        (\sqrt{{\epsilon}_{sk}^{2}+{\epsilon}_{0,a}^{2}}-\sqrt{({\epsilon}-
        {\epsilon}_{sk})^{2}+{\epsilon}_{0,a}^{2}})-C_{a2}{\epsilon}]`
        '''
        return (1+1/(1-self.C_a1*self.eps_0a)*(self.C_a1 *
                (np.sqrt(self.eps_sh**2+self.eps_0a**2) -
                 np.sqrt((eps-self.eps_sh)**2+self.eps_0a**2)) -
                 self.C_a2*eps))


class Liquid(Compound):
    '''
    :param: T [K]
    :param: P [Pa]
    '''
    symbol = None
    T0 = 293.15  # Default temperature for all liquids [K]
    P0 = 101325  # Default pressure for all liquids [Pa]

    def __init__(self, **kwargs):
        self.T0 = kwargs.get('T', self.T0)
        self.P0 = kwargs.get('P', self.P0)
        try:  # Set density if a rho property exists
            self.density = self.rho(self.T0, self.P0)
        except NotImplementedError:
            if self.density is None:
                raise ValueError('No density (value or T-function) specified.')
        super().__init__(self.symbol, state_of_matter='liquid',
                         temperature_K=self.T0, pressure_Pa=self.P0)

    def rho(self, T, P):
        return Chemical(self.chemical_equation, T=T, P=P).rho

    @property
    def P(self):
        '''
        Pressure [Pa]: this is a pythonic property, but not an actual
        material property!
        '''
        return self.P0

    @P.setter
    def P(self, value: 'Pascal'):
        try:
            rho = self.rho(self.T, value)
            self.density_g_per_cm3 = float(kgm3togcm3(rho))
            self.density = float(rho)
        except NotImplementedError:
            self.density_g_per_cm3 = float(kgm3togcm3(self.density))
        self.T0 = value

    @property
    def T(self):
        '''
        Temperature [K]: this is a pythonic property, but not an actual
        material property!
        '''
        return self.T0

    @T.setter
    def T(self, value: 'Kelvin'):
        try:
            rho = self.rho(value, self.P)
            self.density_g_per_cm3 = float(kgm3togcm3(rho))
            self.density = float(rho)
        except NotImplementedError:
            self.density_g_per_cm3 = float(kgm3togcm3(self.density))
        self.T0 = value
