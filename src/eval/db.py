import os
import json
from typing import Dict, List, Optional
from src.repo.models import RepoConfig
from src.runner.local.run_test import get_repo_config 
from src.config import EVAL_DATA_ROOT
from cowboy_lib.test_modules import TestModule

# Note:
# Have to store TestModule separately because it exceeds what Braintrust is willing to store
# per dataset input

class DatasetCreationError(Exception):
    pass

# NEWTODO: the functions here probably should be implemented with a db instead
####################################################################################################
def get_tm(repo_name: str, tm_name: str) -> Optional[TestModule]:
    """
    Read TM from file
    """
    tm_dir = EVAL_DATA_ROOT / repo_name / "tms"
    os.makedirs(tm_dir, exist_ok=True)

    tm_file = tm_dir / f"{tm_name}.json"
    try:
        with open(tm_file, "r") as f:
            return TestModule.from_json(json.loads(f.read()))
    except FileNotFoundError:
        raise DatasetCreationError(f"{tm_file} was not created during create_dataset. Try to rerun create_dataset")

def persist_tm(self, tm: TestModule):
    """
    Persist both the TM and the row to disk
    """
    repo_name = self.repo_config["repo_name"]
    repo_dir = EVAL_DATA_ROOT / repo_name
    tm_dir = EVAL_DATA_ROOT / repo_name / "tms"

    repo_dir.mkdir(exist_ok=True)
    tm_dir.mkdir(exist_ok=True)

    # Write the row data
    file_path = repo_dir / f"{self.name}.json"
    with open(file_path, "w") as f:
        json.dump(self.to_json(), f, indent=2)
        
    # Write the test module
    tm_file = tm_dir / f"{self.name}.json"
    with open(tm_file, "w") as f:
        json.dump(tm.to_json(), f, indent=2)

def get_repo(repo_name: str) -> RepoConfig:
    return get_repo_config(repo_name)
####################################################################################################