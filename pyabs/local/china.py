from pyabs.liability import FEE_TYPE, Fee,AMORTIZE_TYPE,_pay_with
import pandas as pd 

def VAT(rate:float,last_paid_date=None,shortfall=0):
    return Fee('增值税',
                FEE_TYPE.BASE_POOL_INT,
                rate,
                last_paid_date,
                shortfall)

def pay_vat(vat:VAT, base:float, cash:float, pdate:pd.Timestamp)->list:
    # calc due vat tax
    current_due = vat.rate * base

    # pay fee
    remain_cash, fee_paid, new_shortfall = _pay_with(cash, current_due+vat.fee_shortfall)

    # update status
    vat.last_paydate = pdate
    vat.fee_shortfall = new_shortfall
    return f"{vat.name}_FEE",fee_paid,remain_cash