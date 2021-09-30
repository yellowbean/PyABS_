from pyabs.analysis import price_bond
import pytest
from datetime import date
import pandas as pd



def test_pricing():
	#Excel XIRR
    #               A           	B
    # 2021-1-1	    -100	        -500
    # 2021-6-15	    10	             550
    # 2022-10-10	30	             10
    # 2022-12-15	80	             5
    #               0.108229941	     0.287865502
    dates = [date(2021, 1, 1), date(2021, 6, 15), date(2022, 10, 10), date(2022, 12, 15)]
    amountsA = [-100, 10,30,80]

    cf_dfA = pd.DataFrame(
        data={
            "date": dates,
            "cash": amountsA
        },
    )


    resultA = price_bond(cf_dfA)
    assert(pytest.approx(resultA['irr'],0.0001)==0.10822994) 
    
    amountsB = [-500, 550 ,10,5]
    cf_dfB = pd.DataFrame(
        data={
            "date": dates,
            "cash": amountsB
        },
    )
    resultB= price_bond(cf_dfB)
    assert(pytest.approx(resultB['irr'],0.0001)==0.28786550) 