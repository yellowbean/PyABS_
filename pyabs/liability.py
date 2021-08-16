from dataclasses import dataclass, asdict
import json
from enum import IntEnum
#from pyabs.spv import SPVBase
import pandas as pd
import numpy as np

class AMORTIZE_TYPE(IntEnum):
    PASS_TRHOUGH=1
    SCHEDULE=2

class LAST_PAY_TYPE(IntEnum):
    PRIN=0
    INT=1
    FEE=2


@dataclass
class TrancheBase:
    def to_json(self) -> str:
        return json.dumps(asdict(self))

@dataclass
class Tranche(TrancheBase):
    name:str
    origin_balance:float
    origin_rate:float
    rate_type:dict
    current_balance:float
    current_rate:float
    amort_type:AMORTIZE_TYPE

    #payment txn info 
    last_paydate:list
    interest_shortfall:float
    principal_shortfall:float


@dataclass
class ScheduleTranche(Tranche):
    payment_schedule:pd.DataFrame

def _pay_with(cash:float,target:float):
    paid = target if cash>target else cash
    remain = cash - paid
    new_shortfall = target - paid 
    return remain, paid, new_shortfall


def pay_bonds_int(spv, b:Tranche,cash:float,pdate:pd.Timestamp,days_in_year=360)->float:
    if(b.last_paydate[LAST_PAY_TYPE.INT]):
        days_accured = (pdate - b.last_paydate[LAST_PAY_TYPE.INT]).days
    else:
        days_accured = (pdate - spv.begin_date).days
    due_int_this_period = (days_accured/days_in_year)*b.current_rate*b.current_balance
    due_int = due_int_this_period + b.interest_shortfall

    #pay interest
    remain_cash, int_paid, new_shortfall = _pay_with(cash, due_int)

    #change status
    b.last_paydate[LAST_PAY_TYPE.INT] = pdate
    b.interest_shortfall = new_shortfall

    return f"{b.name}_INT",int_paid,remain_cash

def pay_bonds_prin(b:Tranche,cash:float,pdate:pd.Timestamp)->float:
    def calc_due_prin()->float:
        if isinstance(b,ScheduleTranche):
            if "date" in b.payment_schedule.columns:
                b.payment_schedule.set_index('date',inplace=True)
            if pdate in b.payment_schedule.index:
                current_target_balance = b.payment_schedule.loc[pdate,"target_balance"]
                current_due = max(b.current_balance - current_target_balance,0)
                return current_due
            else:
                return b.current_balance

        elif isinstance(b, Tranche):
            return b.current_balance
        else:
            raise RuntimeError(f"Not Match for bond type:{type(b)}")

    due_principal = calc_due_prin() #

    #pay principal
    remain_cash, prin_paid, new_shortfall = _pay_with(cash, due_principal)
    
    #change status
    b.last_paydate[LAST_PAY_TYPE.PRIN] = pdate
    b.principal_shortfall = new_shortfall
    b.current_balance = b.current_balance - prin_paid

    return f"{b.name}_PRIN",prin_paid,remain_cash


@dataclass
class FeeBase:
    def to_json(self) -> str:
        return json.dumps(asdict(self))

class FEE_TYPE(IntEnum):
    BASE_POOL_BAL=1
    BASE_BOND_BAL=2
    BASE_POOL_INT=3 # interest collected
    BASE_POOL_PRIN=4 # principal collected

@dataclass
class Fee(FeeBase):
    name:str
    base:FEE_TYPE
    rate:float
    #payment txn info 
    last_paydate:pd.Timestamp
    fee_shortfall:float

def pay_fee(spv, f:Fee,base:float,cash:float,pdate:pd.Timestamp)->float:
    # calc due fee
    if f.last_paydate is None:
        days_accrued = (pdate - spv.closing_date).days
    else:
        days_accrued = (pdate - f.last_paydate).days
    current_due = f.rate * days_accrued/360 * base

    # pay fee
    remain_cash, fee_paid, new_shortfall = _pay_with(cash, current_due+f.fee_shortfall)

    # update status
    f.last_paydate = pdate
    f.fee_shortfall = new_shortfall
    return f"{f.name}_FEE",fee_paid,remain_cash