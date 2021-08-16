from dataclasses import dataclass, asdict
from pampy import match, _
import pandas as pd
import numpy as np
import json
import functools
from enum import IntEnum
from pyabs.liability import FEE_TYPE,Fee, Tranche, pay_bonds_int, pay_bonds_prin, pay_fee
from pyabs.util import init_cf
from pyabs.local.china import pay_vat
# constants
MAX_MONTH = 12*30+1


@dataclass
class SPVBase:
    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class BankDeal(SPVBase):
    name: str

    # dates
    closing_date: pd.Timestamp
    begin_date: pd.Timestamp
    payment_interval: pd.Timedelta

    # status
    current_date: pd.Timestamp
    period_num: int

    # liabilities
    # bonds
    bonds: dict  # TrancheBase
    # fees
    fees: dict

    # assets

    # run_rules
    payment_seq: list
    stop_rule: dict

    def run_bonds(self, pool_flow: pd.DataFrame) -> pd.DataFrame:
        def stop_proj() -> bool:
            pass

        def get_pool_flow_bal(x:pd.Timestamp) -> pd.DataFrame:
            beg_bal = project_pool_cf.loc[x,"BEG_BAL"]
            end_bal = project_pool_cf.loc[x,"END_BAL"]
            prin = project_pool_cf.loc[x,"PRIN"]
            ints = project_pool_cf.loc[x,"INT"]
            return beg_bal,end_bal,prin,ints

        def cutoff_future_flow(x)->pd.DataFrame:
            return pool_flow

        def get_funds_collected(x: pd.Timestamp) -> float:
            #print("IN ", project_pool_cf['date'].to_list())
            prin_amt = project_pool_cf.loc[x, "PRIN"]
            int_amt = project_pool_cf.loc[x, "INT"]
            return prin_amt+int_amt

        def dist(available_funds, project_idx, dist_date, last_dist_date=None):
            project_bond_cf.loc[dist_date] = pd.NA  # add empty row
            b_bal,e_bal,prin,ints = get_pool_flow_bal(dist_date)
            project_bond_cf.loc[dist_date,'POOL_BEG_BAL'] = b_bal
            project_bond_cf.loc[dist_date,'POOL_END_BAL'] = e_bal
            project_bond_cf.loc[dist_date,'POOL_PRIN'] = prin
            project_bond_cf.loc[dist_date,'POOL_INT'] = ints
            for pay_action in self.payment_seq:
                if pay_action[1] == "PRIN":
                    b_id = pay_action[2]
                    project_bond_cf.loc[dist_date,
                                        f"{b_id}_BEG_BAL"] = self.bonds[b_id].current_balance
                update_field, outflow, available_funds = match(pay_action,
                                                               ["FEE", _ ], 
                                                               lambda fid:
                                                                    match(self.fees[fid], 
                                                                        Fee(_,FEE_TYPE.BASE_POOL_BAL,_,_,_), 
                                                                            lambda _1,_2,_3,_4 :pay_fee(self, self.fees[fid],project_bond_cf.loc[dist_date,"POOL_BEG_BAL"],available_funds,dist_date),
                                                                        Fee("增值税",FEE_TYPE.BASE_POOL_INT,_,_,_), 
                                                                            lambda _1,_2,_3 :pay_vat(self.fees[fid],project_bond_cf.loc[dist_date,"POOL_INT"],available_funds,dist_date)
                                                                        ), 
                                                               ["BOND", "PRIN", _], lambda bid: pay_bonds_prin(
                                                                   self.bonds[bid], available_funds, dist_date),
                                                               ["BOND", "INT", _], lambda bid: pay_bonds_int(self,
                                                                                                             self.bonds[bid], available_funds, dist_date),
                                                               )
                project_bond_cf.loc[dist_date, update_field] = outflow
                if update_field.endswith("_PRIN"):
                    b_id = pay_action[2]  #
                    project_bond_cf.loc[dist_date,
                                        f"{b_id}_END_BAL"] = self.bonds[b_id].current_balance
            return available_funds

        bond_ids = self.bonds.keys()
        pool_fields = ["POOL_BEG_BAL", "POOL_END_BAL", "POOL_PRIN", "POOL_INT"]
        interal_fields = ["_ADA", "_LOG", "_BEG_CASH", "_END_CASH"]
        fee_fields = [ f"{f}_FEE" for f in self.fees ] if self.fees else []
        tranche_fields = [bid+fid for fid in ["_PRIN", "_INT", "_END_BAL", "_BEG_BAL"]
                          for bid in bond_ids]

        # variables for projection
        project_bond_cf = pd.DataFrame(columns=['date']+pool_fields+fee_fields +
                                       tranche_fields+interal_fields).set_index("date")
        project_pool_cf = cutoff_future_flow(pool_flow)
        project_index = 0
        funds_avail = 0
        proj_dist_dates = [self.begin_date +
                           pd.DateOffset(months=_) for _ in range(1, MAX_MONTH)]
        last_dist_date = proj_dist_dates[self.period_num]
        while (not stop_proj()) and (project_index < project_pool_cf.shape[0]):
            dist_date = proj_dist_dates[project_index+self.period_num]
            funds_collected = get_funds_collected(dist_date)
            funds_avail = dist(funds_avail+funds_collected,
                               project_index, dist_date)
            project_index = project_index + 1

        return project_bond_cf
