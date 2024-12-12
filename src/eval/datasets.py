import os
import json
from pathlib import Path

from src.config import EVAL_DATA_ROOT
from cowboy_lib.coverage import TestCoverage
from cowboy_lib.test_modules import TestModule
from typing import Dict

from pydantic import BaseModel

DATASET_ROOT = Path(EVAL_DATA_ROOT)

# NEWTODO: move repo_config into INput
class TestModuleRow(BaseModel):
    tm: TestModule
    file_content: str
    module_cov: TestCoverage
    base_cov: TestCoverage
    repo_config: Dict
    expected: int = 0

    class Config:
        arbitrary_types_allowed = True

    def to_json(self):
        return {
            "input": {
                "tm": self.tm.to_json(),
                "file_content": self.file_content,
                "module_cov": self.module_cov.serialize(),
                "base_cov": self.base_cov.serialize(),
                "repo_config": self.repo_config
            },
            "expected": self.expected,
        }
    
    @classmethod
    def from_json(cls, data):
        input = data["input"]

        return cls(
            tm=TestModule.from_json(input["tm"]),
            file_content=input["file_content"],
            base_cov=TestCoverage.deserialize(input["base_cov"]),
            module_cov=TestCoverage.deserialize(input["module_cov"]),
            repo_config=input["repo_config"],
            expected=data["expected"]
        )
    
    @classmethod
    def from_json2(cls, input):
        return cls(
            tm=TestModule.from_json(input["tm"]),
            file_content=input["file_content"],
            base_cov=TestCoverage.deserialize(input["base_cov"]),
            module_cov=TestCoverage.deserialize(input["module_cov"]),
            repo_config=input["repo_config"],
            # expected=data["expected"]
        )


def persist_rows(row: TestModuleRow, repo_name: str):
    repo_dir = DATASET_ROOT / repo_name
    repo_dir.mkdir(exist_ok=True)

    # Write row data to file
    file_path = repo_dir / f"{row.tm.name}.json"
    with open(file_path, "w") as f:
        json.dump(row.to_json(), f, indent=2)

def read_rows(repo_name: str, limit=5) -> list[TestModuleRow]:
    repo_dir = DATASET_ROOT / repo_name
    if not repo_dir.exists():
        return []

    rows = []
    for file_path in list(repo_dir.glob("*.json"))[:limit]:
        with open(file_path) as f:
            data = json.load(f)
            rows.append(TestModuleRow.from_json(data))

    return rows