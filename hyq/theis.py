import math

def theis_u(r: float, S: float, T: float, t: float) -> float:
    '''
    Helper-function to calculate the Theis-Parameter u for use with Theis-Wellfunction.

    :param r: distance from pumping well in [m]
    :param S: storativity of the aquifer [-]
    :param T: transmissivity of the aquifer [m²/s]
    :param t: time since pumping began [s]
    :return: Theis-Parameter u
    '''
    r = r if r > 0 else 0.01
    return (r**2*S)/(4*T*t)

def theis_wellfunction(u: float, n: int = 30) -> float:
    '''
    Helper-function to solve the Theis-wellfunction for use in drawdown calculations

    :param u: Theis-Parameter as calculated by theis_u
    :param n: Length of the polynomial to be solved. Defaults to 30
    :return: a solution for the Theis-Wellfunction, often denoted W(u) in literatur
    '''
    baseterm = -0.5772 - math.log(u) + u

    for i in range(n):
        x = 2 + i

        if (x % 2) == 0:
            # even
            baseterm -= (u**x)/(x*math.factorial(x))
        else:
            baseterm += (u**x)/(x*math.factorial(x))

    return baseterm

def theis_drawdown(Q: float, T: float, r: float, S: float, t: float, n: int = 30) -> float:
    '''
    Calculate the drawdown of the hydraulc potential within a CONFINED aquifer caused by a pumping well
    for a specific point in space and time.

    :param Q: pumping rate of the well [m³/s]
    :param T: transmissivity of the aquifer [m²/s]
    :param r: (observation) distance from pumping well in [m]
    :param S: storativity of the aquifer [-]
    :param t: time since pumping began [s]
    :param n: Length of the polynomial to be solved. Defaults to 30
    :return: drawdown s [m] for t at r
    '''
    u = theis_u(r = r, S = S, T = T, t = t)
    W_von_u = theis_wellfunction(u = u, n = n)

    return (Q/(4*math.pi*T))*W_von_u

def jakob_freegw_mod(s: float, H: float) -> float:
    '''
    Modify the drawdown caused by a pumping well calculated for a confined aquifer to represent
    a situation where the aquifer is not confined.
    Phrased differently: correct the drawdown s calculated with the Theis-formula
    (e.g. via call to theis_drawdown(...)) to be applicable to a free groundwater surface.

    :param s: drawdown as calculated for a confined aquifer [m]
    :param H: height of the groundwater surface measured from tha base of the aquifer/top of the aquitard [m]
    :return: drawdown [m] within an unconfined aquifer
    '''
    return s - ((s**2)/(2*H))