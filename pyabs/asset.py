import numpy
from pandas import * 
from pampy import *
from dataclasses import dataclass  
from enum import IntEnum
from datetime import datetime

""" This module should generate a dataframe cashflow like from a function """

class AMORTIZE_TYPE(IntEnum):
    EVEN_PRINCIPAL=1
    EVEN_LEVEL=2

@dataclass
class mortgage:
    origin_balance:float
    origin_rate:float
    origin_term:int
    current_balance:float
    current_rate:float
    current_term:float
    amort_type:AMORTIZE_TYPE
    last_level_pay:float
    as_date:datetime

def project_cf(x, since=None):
    pass

def installment_cf(x:dict, since=None):
    pass
