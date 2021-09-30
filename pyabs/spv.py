from dataclasses import dataclass, asdict
from pampy import match, _
import pandas as pd
import numpy as np
import json
import functools
from enum import IntEnum
from pyabs.liability import FEE_TYPE,Fee, Tranche, pay_bonds_int, pay_bonds_prin, pay_fee
from pyabs.util import init_cf
# constants
MAX_MONTH = 12*30+1


@dataclass
class SPVBase:
    def to_json(self) -> str:
        return json.dumps(asdict(self))


