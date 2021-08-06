from pyabs.liability import AMORTIZE_TYPE, Tranche, ScheduleTranche
from pyabs.util import *
from pyabs.spv import *
import pandas as pd
import pytest

def func(x):
    return x + 1


def test_answer():
    assert func(4) == 5


def test_bank_deal_01():
    ''' single bond'''
    bd = BankDeal("bd01",
                  ts("20210721"),
                  ts("20210821"),
                  pd.Timedelta("1M"),
                  ts("20210921"),
                  1, 
                  {"A": Tranche("A",1000,0.08,{},1000,0.07,
                    AMORTIZE_TYPE.PASS_TRHOUGH,[None,None],0,0),

                      },
                  None,
                  # payment sequence
                  [ 
                   ["BOND", "INT", "A"],
                   ["BOND", "PRIN", "A"]
                   ],
                  {}
                  )
    input_pool_cf = pd.DataFrame.from_dict(
        {"date":[ts("20211021"),ts("20211121"),ts("20211221")],
         "POOL_PRIN":[100,200,300],
         "POOL_INT":[300,400,500]
        }
    )
    projected_bond_result = bd.run_bonds(input_pool_cf)

    assert(projected_bond_result['A_PRIN'].sum()==1000.0)
    assert(pytest.approx(projected_bond_result['A_PRIN'][1],0.01)==596.31)
    assert(pytest.approx(projected_bond_result['A_INT'][1],0.001)==3.688)
    assert(pytest.approx(projected_bond_result['A_INT'].sum(),0.01)==15.64)

    projected_bond_result.to_csv("bank_deal_01.csv")


def test_bank_deal_02():
    ''' two bond'''
    bd = BankDeal("bd01",
                  ts("20210721"),
                  ts("20210821"),
                  pd.Timedelta("1M"),
                  ts("20210921"),
                  1, 
                  {
                      "A": Tranche("A",600,0.08,{},600,0.04,
                    AMORTIZE_TYPE.PASS_TRHOUGH,[None,None],0,0),

                      "B": Tranche("B",400,0.08,{},400,0.05,
                    AMORTIZE_TYPE.PASS_TRHOUGH,[None,None],0,0),
                      },
                  None,
                  # payment sequence
                  [ 
                   ["BOND", "INT", "A"],
                   ["BOND", "INT", "B"],
                   ["BOND", "PRIN", "A"],
                   ["BOND", "PRIN", "B"]
                   ],
                  {}
                  )
    input_pool_cf = pd.DataFrame.from_dict(
        {"date":[ts("20211021"),ts("20211121"),ts("20211221")],
         "POOL_PRIN":[100,200,300],
         "POOL_INT":[300,400,500]
        }
    )
    projected_bond_result = bd.run_bonds(input_pool_cf)

    assert(projected_bond_result['A_PRIN'].sum()==600.0)
    assert(pytest.approx(projected_bond_result['B_INT'][0],0.01)==3.39)
    assert(pytest.approx(projected_bond_result['A_INT'][0],0.001)==4.066)
    assert(pytest.approx(projected_bond_result['A_PRIN'][0],0.001)==392.544)
    assert(pytest.approx(projected_bond_result['B_INT'].sum(),0.001)==5.152)

    projected_bond_result.to_csv("bank_deal_02.csv")


def test_bank_deal_03():
    ''' two bond'''
    bd = BankDeal("bd03",
                  ts("20210721"),
                  ts("20210821"),
                  pd.Timedelta("1M"),
                  ts("20210921"),
                  1, 
                  {
                      "A": ScheduleTranche("A",600,0.08,{},600,0.04,
                    AMORTIZE_TYPE.PASS_TRHOUGH,[None,None],0,0
                    ,pd.DataFrame.from_dict({
                        "date":[ts('20211021'),ts('20211121')],
                        "target_balance":[550,400],
                    })
                    ),

                      "B": Tranche("B",400,0.08,{},400,0.05,
                    AMORTIZE_TYPE.PASS_TRHOUGH,[None,None],0,0),
                      },
                  None,
                  # payment sequence
                  [ 
                   ["BOND", "INT", "A"],
                   ["BOND", "INT", "B"],
                   ["BOND", "PRIN", "A"],
                   ["BOND", "PRIN", "B"]
                   ],
                  {}
                  )
    input_pool_cf = pd.DataFrame.from_dict(
        {"date":[ts("20211021"),ts("20211121"),ts("20211221")],
         "POOL_PRIN":[100,200,300],
         "POOL_INT":[300,400,500]
        }
    )
    projected_bond_result = bd.run_bonds(input_pool_cf)

    assert(projected_bond_result['A_PRIN'].sum()==600.0)
    assert(pytest.approx(projected_bond_result['A_PRIN'][0],0.01)==50)
    assert(pytest.approx(projected_bond_result['A_PRIN'][1],0.01)==150)
    assert(pytest.approx(projected_bond_result['B_PRIN'][0],0.001)==342.544)
    #assert(pytest.approx(projected_bond_result['B_INT'].sum(),0.001)==5.152)

    projected_bond_result.to_csv("bank_deal_03.csv")


