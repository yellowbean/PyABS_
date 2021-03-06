import pandas as pd
import numpy as np
from pampy import match,_


def ts(x:str)->pd.Timestamp:
    return pd.Timestamp(x)

def filter_user_field(x:list)->list:
    return filter(lambda x:not x.startswith("_"),x)

def pick_by_key(f,v,xs:list):
    for x in xs:
        if x[f]==v:
            return x
    else:
        return None


def init_cf(x:dict,prin_col="PRIN",alias={})->pd.DataFrame:
    start_bal = x['init_bal']
    x.pop("init_bal")
    cf = pd.DataFrame.from_dict(x)
    cf.set_index('date',inplace=True)

    cumu_prin = cf['PRIN'].cumsum()
    cf["END_BAL"] = start_bal - cumu_prin
    cf["BEG_BAL"] = cf["END_BAL"] + cf[prin_col]
    return cf

def init_deal(x:dict):
    {

    }
    return None 