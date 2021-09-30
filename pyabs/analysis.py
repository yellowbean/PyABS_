import pandas as pd
import numpy as np
from pyxirr import xirr

def price_bond(x:pd.DataFrame, cash_column=('date','cash'), output=None)->dict:
    #  x-> a df with 'date' as index, 'cf' as cashflow
    if output is None: 
        irr = xirr(x[list(cash_column)]) 
        

        return {'irr':irr}
    else:
        return 


    