import json
from dataclasses import dataclass
from pyabs.liability import FEE_TYPE, Fee,AMORTIZE_TYPE, Tranche,_pay_with,pay_fee,pay_bonds_prin,pay_bonds_int
import pandas as pd 
from pyabs.spv import SPVBase,MAX_MONTH
import pyabs.util as util
from pampy import match,_


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
    vat.last_paydate =pdate
    vat.fee_shortfall = new_shortfall
    return f"{vat.name}_FEE",fee_paid,remain_cash


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
    pools: dict
    # run_rules
    payment_seq: list
    stop_rule: dict

    def run_pool(self, assumption_type) -> pd.DataFrame:
        pass


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



def deal_from_report(path_to_deal_file:str, path_to_report_file:str, deal_type=BankDeal):
    def build_tranche()->dict:
        r = {}
        for b in deal_json['债券本金兑付']:
            bond_name = b['证券分层']
            origin_bal = b['信托设立日余额']
            current_bal = b['本期期末余额']
            r[bond_name] = Tranche(bond_name,
            origin_bal,
            origin_rate,
            rate_type,
            current_bal,
            util/util.pick_by_key('证券分层',
                                bond_name,
                                report_json['债券利息兑付'])['证券执行利率'],
            AMORTIZE_TYPE.PASS_TRHOUGH,
            [],0,0)
    
    def build_fee()->dict :
        pass 
    
    def build_pool()->dict :
        pass 

    report_json = json.load(path_to_report_file)
    deal_json = json.load(path_to_deal_file)
    report_y, report_m, report_d = report_json['报告日期']
    deal = BankDeal("bd_name",
        util.ts("20210721"), 
        util.ts("20210821"), 
        pd.Timedelta("1M"),
        pd.Timestamp(year=int(report_y),month=int(report_m),day=int(report_d)),
        1,
        build_tranche(),
        build_fee(),
        build_pool(),
        pay_seq,
        {})
        
    return deal