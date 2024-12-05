from typing import Dict

from cowboy_lib.repo import SourceRepo
from braintrust import Dataset, init_dataset

from dataclasses import dataclass

@dataclass
class TMRecord:
    name: str
    coverage: float

