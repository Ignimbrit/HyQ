import math

def theis_u(r: float, S: float, T: float, t: float) -> float:
    r = r if r > 0 else 0.01
    return (r**2*S)/(4*T*t)

def theis_wellfunction(u: float, n: int = 30) -> float:
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
    u = theis_u(r = r, S = S, T = T, t = t)
    W_von_u = theis_wellfunction(u = u, n = n)

    return (Q/(4*math.pi*T))*W_von_u
