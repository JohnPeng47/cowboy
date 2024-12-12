from cowboy_lib.coverage import TestCoverage
import json
from pathlib import Path

BASE_PATH = Path("/home/ubuntu/cowboy-server/repos/textual-neutered/liggsibm/")
BASECOV_PATH = "basecov_textual.json"
MODULECOV_PATH = "modulecov_textual.json"


def compare(a: TestCoverage, b: TestCoverage):
    for t1, t2 in zip(a.cov_list, b.cov_list):
        assert t1.filename == t2.filename
        if t1.stmts != t2.stmts:
            print(f"Diff in {t1.filename}: stmts")
            print(f"Base: {t1} || {t1.covered + t1.misses},{t1.stmts}")
            print(f"Module: {t2} || {t2.covered + t2.misses},{t2.stmts}")

            # CLUE #1: this always matches
            # if t1.covered + t1.misses != t1.stmts or t2.covered + t2.misses != t2.stmts:
            #     raise Exception(f"Total stmts mismatch for {t1.filename}")

            missing_stmts = set(t1.all_lines) - set(t2.all_lines)
            print("Missing stmts: ", missing_stmts)

            for stmt in missing_stmts:
                with open(BASE_PATH / t1.filename) as f:
                    lines = f.readlines()
                    print(f"Line {stmt}: {lines[stmt-1]}")

            if t1.covered < t2.covered:
                raise Exception(f"Coverage decreased for {t1.filename}")

def test_file_diff():
    with open(BASECOV_PATH) as f:
        base_cov = TestCoverage.from_coverage_file(json.load(f))
    with open(MODULECOV_PATH) as f:
        module_cov = TestCoverage.from_coverage_file(json.load(f))

    print("\nBase Cov: ", base_cov)
    print("Module Cov: ", module_cov)

    compare(base_cov, module_cov)

    cov_diff = base_cov - module_cov
    print(cov_diff)

    # assert cov_diff.total_cov.stmts == 33
    # assert cov_diff.total_cov.misses == 11
    # assert cov_diff.total_cov.covered == 22

test_file_diff()