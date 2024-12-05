from src.test_modules.iter_tms import iter_test_modules
from cowboy_lib.repo import SourceRepo
from cowboy_lib.test_modules import TestModule
from cowboy_lib.ast import NodeType

from typing import List

import sys
from pathlib import Path

def num_delete(tm: TestModule, to_keep: int = 1, to_delete: int = 1) -> int:
    if to_keep and to_delete:
        raise Exception("Cannot have both values > 0")

    # always leave at least one test
    if to_keep:
        num_to_del = max(0, len(tm.tests) - to_keep)
        return num_to_del
    elif to_delete:
        num_to_del = min(len(tm.tests) - 1, to_delete)
        return num_to_del
    else:
        raise Exception("Must provide either to_keep or to_delete value")


def neuter_tests(
    test_modules: List[TestModule], src_repo: SourceRepo, to_keep, to_delete=0
):
    total_deleted = 0
    failed_mod = 0
    for tm in test_modules:
        try:
            print("Deleting tm: ", tm.name)
            to_exclude = []
            # BUG: tm.tests gets modified somehow
            num_to_del = num_delete(tm, to_keep=to_keep, to_delete=to_delete)
            total_tests = len(tm.tests)

            for func in tm.tests[:num_to_del]:
                to_exclude.append((func, tm.test_file.path))
                # CARE: this operation has changes state of src_repo,
                # which is then propagated to strategy below
                src_repo.find_file(tm.path).delete(
                    func.name, node_type=NodeType.Function
                )
                # tm.test_file.delete(func.name, node_type=NodeType.Function)

                with open(src_repo.repo_path / tm.test_file.path, "w") as f:
                    # print(tm.test_file.to_code())
                    f.write(src_repo.find_file(tm.path).to_code())

                total_deleted += 1
        except Exception as e:
            failed_mod += 1

    print("Total failed:", failed_mod)

def neuter_tests2(
    test_modules: List[TestModule], 
    src_repo: SourceRepo, 
    to_keep, 
    to_delete=0, 
    new_repo: Optional[Path] = None
):
    total_deleted = 0
    failed_mod = 0
    for test_file in src_repo.test_files:
        for tm in [tm for tm in test_modules if tm.test_file == test_file]:
            og_bytes = len(open(src_repo.repo_path / test_file.path, "r").read())
            try:
                print("Deleting tm: ", tm.name)
                to_exclude = []
                # BUG: tm.tests gets modified somehow
                num_to_del = num_delete(tm, to_keep=to_keep, to_delete=to_delete)
                total_tests = len(tm.tests)

                for func in tm.tests[:num_to_del]:
                    to_exclude.append((func, tm.test_file.path))
                    # CARE: this operation has changes state of src_repo,
                    # which is then propagated to strategy below
                    src_repo.find_file(tm.path).delete(
                        func.name, node_type=NodeType.Function
                    )
                    # tm.test_file.delete(func.name, node_type=NodeType.Function)

                    total_deleted += 1

            except Exception as e:
                failed_mod += 1

        output_path = (new_repo if new_repo else src_repo.repo_path) / test_file.path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(src_repo.find_file(test_file.path).to_code())

        new_bytes = len(src_repo.find_file(test_file.path).to_code())
        print(f"Reduced {test_file.path} by {og_bytes - new_bytes} bytes and {total_deleted} tests")

    print("Total failed:", failed_mod)


if __name__ == "__main__":
    """
    python -m neuter_repo <repo_path> [new_repo_path]
    """
    repo = Path(sys.argv[1])
    if not repo.exists():
        print("Repo does not exist")
        sys.exit()

    new_repo = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    src_repo = SourceRepo(repo)
    test_modules = iter_test_modules(src_repo)

    neuter_tests(test_modules, src_repo, to_keep=2, to_delete=0)
