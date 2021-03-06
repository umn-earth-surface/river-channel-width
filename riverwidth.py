#! /usr/bin/python3

import numpy as np
from matplotlib import pyplot as plt

class TransportLimitedWidth(object):
    """
    The classic case for the gravel-bed river.
    """

    def __init__(self, h_banks, S, D, b0=None, Q0=None, 
                 Parker_epsilon=0.2, intermittency=1.):
        """
        :param h_banks: The height of the wall(s) immediately next to the river.
            This could be expanded in the future to vary with space and/or with
            river left/right. [m]
        :type param: float
        :param S: Channel slope [unitless: distance per distance].
        :type S: float
        :param D: Sediment grain size [m].
        :type D: float
        :param b0: Prescribed initial channel width [m].
        :type D: float
        :param Q0: "Initial" discharge from which to compute an equilibrium
            initial channel width. [m^3/s]
        :type Q0: float
        :param Parker_epsilon: Excess fractional shear stress with a stable
            channel. Equals (tau_b/tau_c) - 1, at an equilibrium channel width.
            [unitless: stress per stress, minus one]
        :type Parker_epsilon: float
        :param intermittency: The fraction of time that the river spends in a 
            geomorphically effective flood of the given stage. This is needed
            only when a characteristic flood, rather than a full hydrograph,
            is given. [unitless: time per time]
        :type intermittency float
        """
        
        # Input variables
        self.h_banks = h_banks
        self.S = S
        self.D = D
        self.intermittency = intermittency
        self.Parker_epsilon = Parker_epsilon
        
        # Constants
        self.MPM_phi = 3.97
        self.g = 9.805
        self.rho_s = 2700.
        self.rho = 1000.
        self.tau_star_crit = 0.0495
        self.SSG = (self.rho_s - self.rho) / self.rho
        
        # Derived constants
        self.k_b__eq = 0.17 / ( self.g**.5 * self.SSG**(5/3.)
                                * (1 + self.Parker_epsilon)**(5/3.)
                                * self.tau_star_crit**(5/3.) )
        self.k_bank = self.S**0.7 \
                        / ( 2.9 * self.SSG * self.g**0.3 * self.D**0.9 )

        # Initial conditions
        if (b0 is not None and Q0 is not None) or (b0 is None and Q0 is None):
            raise TypeError('You must specify exactly one of {b0, Q0}.')
        elif b0 is not None:
            self.b = [b0]
            self.Q0 = self.get_dischargeAtEquilibriumWidth(b0)
        else:
            self.b = [self.get_equilibriumWidth(Q0)]
            self.Q0 = Q0
        # Variables for Q and b right now
        self.bi = self.b[-1]
        self.Qi = self.Q0

    def get_equilibriumWidth(self, Q_eq):
        b_eq = self.k_b__eq * Q_eq * self.S**(7/6.) / self.D**1.5
        return b_eq

    def get_dischargeAtEquilibriumWidth(self, b_eq):
        Q_eq = (b_eq / self.k_b__eq) * (self.D**1.5 / self.S**(7/6.))
        return Q_eq
    
    def get_depth(self):
        kh = D**.1 / (2.9 * g**.3 * S**.3)
        h = kh * (self.Qi / self.bi[-1])**0.6
        return h
    
    def get_bedShieldsStress(self):
        h = get_depth(self)
        tau_star_bed = h * self.S / ( self.SSG * D)
        return tau_star_bed

    def get_bankShieldsStress(self):
        tau_star_bank = self.k_bank \
                          * (self.Qi / self.bi)**.6 \
                          / (1. + self.Parker_epsilon)
        return tau_star_bank
            
    def initialize(self, t, Q):
        self.t = list(t)
        self.Q = list(Q)
        # b already equals the starting b
        
    def update(self, dt, Qi):
        # Simple Euler forward.
        # Only widening; no narrowing
        self.bi = self.b[-1]
        # Current discharge
        self.Qi = Qi
        tau_star_bank = self.get_bankShieldsStress()
        if tau_star_bank > self.tau_star_crit:
            self.bi += ( tau_star_bank - self.tau_star_crit )**(3/2.) \
                     * dt * self.intermittency / self.h_banks
        self.b.append(self.bi)

    def run(self):
        # Start at 1: time 0 has the initial conditions
        for i in range(1, len(self.t)):
            # Not sure how inefficient this repeat check will be
            # Will find a better way in the future
            try:
                dt = (self.t[i] - self.t[i-1]).total_seconds()
            except:
                dt = (self.t[i] - self.t[i-1])
            self.update(dt, self.Q[i])

    def finalize(self):
        self.t = np.array(self.t)
        self.b = np.array(self.b)
        self.Q = np.array(self.Q)

    def plot(self):
        plt.figure()
        #plt.hlines(b_eq, t[0] / (24.*60.*60.), t[-1] / (24.*60.*60.),
        #           '.5', label='Equilibrium width', linewidth=2)
        plt.plot(self.t / (24.*60.*60.), b, 'k-', label='Transient width',
                 linewidth=2)
        plt.xlabel('Time [days]')
        plt.ylabel('Channel width [m]')
        plt.legend()
        plt.tight_layout()
        plt.show()


class DetachmentLimitedWidth(object):
    """
    The classic case for the sand- and/or silt-bed river
    """

    def __init__(self, h_banks, S, tau_crit, k_d, b0=None, Q0=None, 
                 Parker_epsilon=0.2, intermittency=1., lambda_r=0.1):
        
        # Input variables
        self.h_banks = h_banks
        self.S = S
        self.tau_crit = tau_crit # Critical stress to detach particles from bank
        self.k_d = k_d # Bank rate constant
        self.intermittency = intermittency
        self.Parker_epsilon = Parker_epsilon
        self.lambda_r = lambda_r # Roughness (Cf, I think -- double check)
        
        # Constants
        self.g = 9.805
        self.rho = 1000.
        
        # Derived constants
        self.a1 = self.rho * self.g**.7 * self.S**.7 * self.lambda_r**.1 \
                  / (8.1**.6 * (1+self.Parker_epsilon))

        # Initial conditions
        if (b0 is not None and Q0 is not None) or (b0 is None and Q0 is None):
            raise TypeError('You must specify exactly one of {b0, Q0}.')
        elif b0 is not None:
            self.b = [b0]
            #self.Q0 = self.get_dischargeAtEquilibriumWidth(b0)
        else:
            self.b = [self.get_equilibriumWidth(Q0)]
            #self.Q0 = Q0
        # Variables for Q and b right now
        self.bi = self.b[-1]
        self.Qi = None # self.Q0

    def get_equilibriumWidth(self, Q_eq):
        b_eq = self.rho**(5/3.) * self.g**(7/6.) \
               * self.S**(7/6.) * self.lambda_r**(1/6.) \
               / (8.1 * (1 + self.Parker_epsilon)**(5/3.)) \
               * Q_eq / self.tau_crit**(5/3.)
        return b_eq

    def dynamic_time_step(self, max_fract_to_equilib=0.1):
        # Currently part of a big, messy "update" step
        pass

    def initialize(self, t, Q):
        self.t = list(t)
        self.Q = list(Q)
        # b already equals the starting b
        
    def update(self, dt, Qi, max_fract_to_equilib=0.1):
        # Euler forward wtih dynamic inner-loop time stepping
        # Only widening; no narrowing
        dt_outer = dt
        bi_outer = self.b[-1]
        self.Qi = Qi
        self.tau_bank = self.a1 * (self.Qi/bi_outer)**.6
        if self.tau_bank > self.tau_crit:
            self.bi = self.b[-1]
            dt_remaining = dt
            while dt_remaining != 0:
                if dt_remaining < 0:
                    raise RuntimeError('More time used than allowed. '
                                          +str(dt_remaining)
                                          +' seconds remaining')
                self.tau_bank = self.a1 * (self.Qi/self.bi)**.6
                dbdt = self.k_d/self.h_banks \
                           * ( self.tau_bank - self.tau_crit ) \
                           * self.intermittency
                b_eq = self.get_equilibriumWidth(self.Qi)
                dt_to_cutoff = max_fract_to_equilib * (b_eq - self.bi) / dbdt
                dt_inner = np.min((dt_to_cutoff, dt_remaining))
                self.bi += self.k_d/self.h_banks \
                              * ( self.tau_bank - self.tau_crit ) \
                              * dt_inner * self.intermittency
                dt_remaining -= dt_inner
                #print(dt_remaining, self.bi, b_eq)
        self.b.append(self.bi)

    def update__simple_time_step(self, dt, Qi):
        # Simple Euler forward.
        # Only widening; no narrowing
        self.bi = self.b[-1]
        # Current discharge
        self.Qi = Qi
        self.tau_bank = self.a1 * (self.Qi/self.bi)**.6
        if self.tau_bank > self.tau_crit:
            self.bi += self.k_d/self.h_banks \
                          * ( self.tau_bank - self.tau_crit ) \
                          * dt * self.intermittency
        self.b.append(self.bi)

    def run(self):
        # Start at 1: time 0 has the initial conditions
        for i in range(1, len(self.t)):
            # Not sure how inefficient this repeat check will be
            # Will find a better way in the future
            try:
                dt = (self.t[i] - self.t[i-1]).total_seconds()
            except:
                dt = (self.t[i] - self.t[i-1])
            self.update(dt, self.Q[i])

    def finalize(self):
        self.t = np.array(self.t)
        self.b = np.array(self.b)
        self.Q = np.array(self.Q)

    def plot(self):
        b_eq = self.get_equilibriumWidth(self.Qi)
        plt.figure()
        plt.hlines(b_eq, self.t[0], self.t[-1]/86400.,
                   '.5', label='Equilibrium width', linewidth=2)
        plt.plot(self.t/86400., self.b, 'k-', label='Transient width',
                 linewidth=2)
        plt.xlabel('Time [days of flood]')
        plt.ylabel('Channel width [m]')
        plt.legend(loc='lower right')
        plt.tight_layout()
        plt.show()


class RiverWidth(TransportLimitedWidth, DetachmentLimitedWidth):

  def __init__(self, h_banks, S, D, b0=None, Q0=None, intermittency=1.):
      """
      :param h_banks: The height of the wall(s) immediately next to the river.
          This could be expanded in the future to vary with space and/or with
          river left/right. [m]
      :type param: float
      :param S: Channel slope [unitless: distance per distance].
      :type S: float
      :param D: Sediment grain size [m].
      :type D: float
      :param b0: Prescribed initial channel width [m].
      :type D: float
      :param Q0: "Initial" discharge from which to compute an equilibrium
          initial channel width. [m^3/s]
      :type Q0: float
      :param intermittency: The fraction of time that the river spends in a 
          geomorphically effective flood of the given stage. This is needed
          only when a characteristic flood, rather than a full hydrograph,
          is given. [unitless: time per time]
      :type intermittency float
      """
      self.h_banks = h_banks
      self.S = S
      self.D = D
      if b0 is not None and Q0 is not None:
          raise TypeError('You must specify exactly one of {b0, Q0}.')
          self.b = [b0]
      else:
          pass

