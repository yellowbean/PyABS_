import pandas as pd
import numpy as np


def ts(x:str)->pd.Timestamp:
    return pd.Timestamp(x)

def filter_user_field(x:list)->list:
    return filter(lambda x:not x.startwith("_"),x)