# src/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

# This exact variable name 'limiter' is what your routes are trying to import
limiter = Limiter(key_func=get_remote_address)