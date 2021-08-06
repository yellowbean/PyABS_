from pandas.core.frame import DataFrame
import pandas as pd


def proj_cashflow():
    pass

def init_pool_cf(path:str)->pd.DataFrame:
    return pd.read_csv(path)