from dataclasses import dataclass, asdict
from pampy import match, _
import pandas as pd
import numpy as np
import json
import functools
from enum import IntEnum
from pyabs.liability import Tranche, pay_bonds_int, pay_bonds_prin

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

        def get_future_pool_flow(x) -> pd.DataFrame:
            return pool_flow

        def get_funds_collected(x: pd.Timestamp) -> float:
            #print("IN ", project_pool_cf['date'].to_list())
            prin_amt = project_pool_cf.loc[x, "POOL_PRIN"]
            int_amt = project_pool_cf.loc[x, "POOL_INT"]
            return prin_amt+int_amt

        def dist(available_funds, project_idx, dist_date):
            project_bond_cf.loc[dist_date] = pd.NA  # add empty row
            for pay_action in self.payment_seq:
                if pay_action[1]=="PRIN":
                    b_id = pay_action[2] 
                    project_bond_cf.loc[dist_date,f"{b_id}_BEG_BAL"] = self.bonds[b_id].current_balance
                update_field, outflow, available_funds = match(pay_action,
                                                               # ["FEE", _ ],  "PAY FEE",
                                                               ["BOND", "PRIN", _], lambda bid: pay_bonds_prin(
                                                                    self.bonds[bid], available_funds, dist_date),
                                                               ["BOND", "INT", _], lambda bid: pay_bonds_int(self,
                                                                    self.bonds[bid], available_funds, dist_date),
                                                               )
                project_bond_cf.loc[dist_date, update_field] = outflow
                if update_field.endswith("_PRIN"):
                    b_id = pay_action[2]  #
                    project_bond_cf.loc[dist_date,f"{b_id}_END_BAL"] = self.bonds[b_id].current_balance
            return available_funds

        bond_ids = self.bonds.keys()
        pool_fields = ["POOL_BEG_BAL","POOL_END_BAL", "POOL_PRIN", "POOL_INT"]
        interal_fields = ["_ADA", "_LOG", "_BEG_CASH", "_END_CASH"]
        fee_fields = ["TRUSTEE", "TAX", "SERVICE"]
        tranche_fields = [bid+fid for fid in ["_PRIN", "_INT","_END_BAL","_BEG_BAL"]
                          for bid in bond_ids]

        # variables for projection
        project_bond_cf = pd.DataFrame(columns=['date']+pool_fields+fee_fields +
                                       tranche_fields+interal_fields).set_index("date")
        project_pool_cf = get_future_pool_flow(pool_flow).set_index("date")
        project_index = 0
        funds_avail = 0
        proj_dist_dates = [self.begin_date +
                           pd.DateOffset(months=_) for _ in range(1, MAX_MONTH)]
        last_dist_date = proj_dist_dates[self.period_num]
        while (not stop_proj()) and(project_index < project_pool_cf.shape[0] ):
            dist_date = proj_dist_dates[project_index+self.period_num]
            funds_collected = get_funds_collected(dist_date)
            funds_avail = dist(funds_avail+funds_collected,
                               project_index, dist_date)
            project_index = project_index + 1

        return project_bond_cf
