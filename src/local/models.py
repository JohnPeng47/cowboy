import yaml
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from pathlib import Path

from src.repo.models import RepoConfig
from src.config import EVAL_DATA_ROOT
from cowboy_lib.test_modules import TestModule

from .db import get_tm, get_repo, persist_tm

@dataclass
class TestCase:
    name: str
    coverage_added: int
    code: str

    @classmethod
    def from_dict(cls, data: Dict) -> "TestCase":
        return cls(
            name=data["name"],
            coverage_added=data["coverage_added"],
            code=data["code"]
        )

@dataclass
class TestResults:
    repo_name: str
    git_hash: str
    tm_name: str
    tests: List[TestCase]

    @classmethod
    def from_file(cls, file_path: Path) -> "TestResults":
        with open(file_path, "r") as f:
            data = yaml.safe_load(f.read())
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TestResults":
        return cls(
            repo_name=data["repo_name"],
            git_hash=data["git_hash"],
            tm_name=data["tm_name"],
            tests=[TestCase.from_dict(t) for t in data["tests"]]
        )

    def to_dict(self) -> Dict:
        return asdict(self)
    

@dataclass
class TestModuleData:
    """
    TestModuleData used for regular test generation
    """
    name: str
    file_content: str
    repo_config: Dict

    def get_tm(self) -> Optional[TestModule]:
        return get_tm(self.repo_config["repo_name"], self.name)

    @classmethod
    def from_json(cls, data):
        return cls(
            name=data["name"],
            file_content=data["file_content"],
            repo_config=data["repo_config"]
        )

@dataclass
class TestModuleEvalData(TestModuleData):
    """
    TestModuleData used for evaluations that contains extra fields for scoring evaluation results
    """
    expected: int = 0
    tags: List[str] = field(default_factory=list)
        
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
    def from_json(cls, data) -> "TestModuleEvalData":
        input = data["input"]

        return cls(
            name=input["name"],
            file_content=input["file_content"],
            repo_config=input["repo_config"],
            expected=data["expected"],
            tags=data["tags"]
        )
    
def read_rows(repo_name: str, limit=5) -> List["TestModuleEvalData"]:
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
            rows.append(TestModuleEvalData.from_json(data))

    print(f"Successfully read {len(rows)} rows from {repo_dir}")
    return rows