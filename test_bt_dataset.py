from braintrust import init_dataset
from src.config import BT_PROJECT, BT_API_KEY
from src.eval.datasets import TestModuleRow
from src.runner.local.run_test import get_repo_config 
from src.config import TESTCONFIG_ROOT
from pathlib import Path
import json

dataset = init_dataset(name="codecovapi-neutered", project=BT_PROJECT, api_key=BT_API_KEY)

with open(Path(TESTCONFIG_ROOT) / f"codecovapi-neutered.json", "r") as f:
    repo_config = json.loads(f.read())        

# for d in dataset:
#     d["input"].update({})
#     dataset.update(d["id"], d)

