import os
from typing import List
import pint

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def list_of_floats(input:str)->List[float]:
    return [float(v) for v in input.split(';')]