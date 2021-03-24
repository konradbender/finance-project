# copy pasting from this article : https://medium.com/swlh/calculating-option-premiums-using-the-black-scholes-model-in-python-e9ed227afbee
# i see problems here we have to panda imports


from math import sqrt, exp

import numpy as np

from scipy.stats import norm


def d1(S, K, T, r, sigma):
    assert (T >= 0), "illegal Time"
    return (np.log(S / K) + (r + sigma ** 2 / 2.) * T) / sigma * np.sqrt(T)


def d2(S, K, T, r, sigma):
    assert (T >= 0), "illegal Time"
    return d1(S, K, T, r, sigma) - sigma * np.sqrt(T)


def bs_call(S, K, T, r, sigma):
    return S * norm.cdf(d1(S, K, T, r, sigma)) - K * np.exp(-r * T) * norm.cdf(d2(S, K, T, r, sigma))


def bs_put(S, K, T, r, sigma):
    return K * exp(-r * T) - S + bs_call(S, K, T, r, sigma)




# 3rd block of content
def call_implied_volatility(Price, S, K, T, r):
    sigma = 0.001
    while sigma < 1:
        Price_implied = S * \
                        norm.cdf(d1(S, K, T, r, sigma)) - K * exp(-r * T) * \
                        norm.cdf(d2(S, K, T, r, sigma))
        if Price - (Price_implied) < 0.001:
            return sigma
        sigma += 0.001
    return "Not Found"


def put_implied_volatility(Price, S, K, T, r):
    sigma = 0.001
    while sigma < 1:
        Price_implied = K * exp(-r * T) - S + bs_call(S, K, T, r, sigma)
        if Price - (Price_implied) < 0.001:
            return sigma
        sigma += 0.001
    return "Not Found"


# 4th block of Code


def call_delta(S, K, T, r, sigma):
    return norm.cdf(d1(S, K, T, r, sigma))


def call_gamma(S, K, T, r, sigma):
    return norm.pdf(d1(S, K, T, r, sigma)) / (S * sigma * sqrt(T))


def call_vega(S, K, T, r, sigma):
    return 0.01 * (S * norm.pdf(d1(S, K, T, r, sigma)) * sqrt(T))


def call_theta(S, K, T, r, sigma):
    return 0.01 * (-(S * norm.pdf(d1(S, K, T, r, sigma)) * sigma) / (2 * sqrt(T)) - r * K * exp(-r * T) * norm.cdf(
        d2(S, K, T, r, sigma)))


def call_rho(S, K, T, r, sigma):
    return 0.01 * (K * T * exp(-r * T) * norm.cdf(d2(S, K, T, r, sigma)))


def put_delta(S, K, T, r, sigma):
    return -norm.cdf(-d1(S, K, T, r, sigma))


def put_gamma(S, K, T, r, sigma):
    return norm.pdf(d1(S, K, T, r, sigma)) / (S * sigma * sqrt(T))


def put_vega(S, K, T, r, sigma):
    return 0.01 * (S * norm.pdf(d1(S, K, T, r, sigma)) * sqrt(T))


def put_theta(S, K, T, r, sigma):
    return 0.01 * (-(S * norm.pdf(d1(S, K, T, r, sigma)) * sigma) / (2 * sqrt(T)) + r * K * exp(-r * T) * norm.cdf(
        -d2(S, K, T, r, sigma)))


def put_rho(S, K, T, r, sigma):
    return 0.01 * (-K * T * exp(-r * T) * norm.cdf(-d2(S, K, T, r, sigma)))

# 5th block of Code
