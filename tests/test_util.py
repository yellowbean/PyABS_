import pytest
import pyabs.util as u # import *
import pandas as pd

def test_ts():
    x = u.ts("20200101")
    assert isinstance(x, pd.Timestamp)


def test_filter_user_field():
    tst_fields = ['_A',"_B","C","D"]
    r = list(u.filter_user_field(tst_fields))
    assert (len(r)==2)
    assert ("C" in r)
    assert ("D" in r)

def test_init_cf():
    d = {"date":[u.ts("20210101"),u.ts("20210201"),u.ts("20210301")],
        "PRIN":[100,200,350],
        'init_bal' : 650
    }
    r = u.init_cf(d)

    assert(pytest.approx( r["BEG_BAL"][0],0.01)==650)
    assert(pytest.approx( r["BEG_BAL"][1],0.01)==550)
    assert(pytest.approx( r["BEG_BAL"][2],0.01)==350)

    assert(pytest.approx( r["END_BAL"][0],0.01)==550)
    assert(pytest.approx( r["END_BAL"][1],0.01)==350)
    assert(pytest.approx( r["END_BAL"][2],0.01)==0)
