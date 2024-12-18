import json
from typing import Dict, List, Optional

from src.repo.models import RepoConfig
from src.config import EVAL_DATA_ROOT
from cowboy_lib.coverage import TestCoverage
from cowboy_lib.test_modules import TestModule
from pydantic import BaseModel

from .db import get_tm, persist_tm, get_repo_config

class TestModuleRow(BaseModel):
    name: str
    file_content: str
    repo_config: Dict
    expected: int = 0
    tags: List[str] = []
    # removed_tests: List[str]

    class Config:
        arbitrary_types_allowed = True

    def get_tm(self) -> Optional[TestModule]:
        return get_tm(self.repo_config["repo_name"], self.name)
        
    def to_json(self) -> Dict:
        return {
            "input": {
                "name": self.name,
                "file_content": self.file_content,
                "repo_config": self.repo_config
            },
            "expected": self.expected,
            "metadata": {},
            "tags": self.tags
        }

    def persist(self, tm: TestModule):
        repo_name = self.repo_config["repo_name"]
        repo_dir = EVAL_DATA_ROOT / repo_name
        repo_dir.mkdir(exist_ok=True)

        # Write the row data
        file_path = repo_dir / f"{self.name}.json"
        with open(file_path, "w") as f:
            json.dump(self.to_json(), f, indent=2)

        persist_tm(tm)
    
    @classmethod
    def from_json(cls, data) -> "TestModuleRow":
        input = data["input"]

        return cls(
            name=input["name"],
            file_content=input["file_content"],
            repo_config=input["repo_config"],
            expected=data["expected"],
            tags=data["tags"]
        )
    
    @classmethod
    def from_json2(cls, input) -> "TestModuleRow":

        return cls(
            name=input["name"],
            file_content=input["file_content"],
            repo_config=input["repo_config"],
            # CARE: we dont need tags for when we instantiate this object in 
            # eval_augment, only in when we use it to initialize the dataset
            # Prolly a bad design here to have same object have two different uses
            # tags=input["tags"],
        )
    
def read_rows(repo_name: str, limit=5) -> List["TestModuleRow"]:
    """
    Read TestModuleRows from disk
    """
    repo_dir = EVAL_DATA_ROOT / repo_name
    if not repo_dir.exists():
        raise ValueError(f"Dataset directory {repo_dir} does not exist")

    rows = []
    print(f"Reading up to {limit} rows from {repo_dir}")
    for file_path in list(repo_dir.glob("*.json"))[:limit]:
        print(f"Reading {repo_name} dataset from {file_path}")
        with open(file_path) as f:
            data = json.load(f)
            rows.append(TestModuleRow.from_json(data))

    print(f"Successfully read {len(rows)} rows from {repo_dir}")
    return rows