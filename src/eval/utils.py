from pathlib import Path
import os

from src.logger import get_logfile_id

def write_test_results(output_dir: Path, test_name: str, improved):
    timestamp, id = get_logfile_id(file_prefix="testgen")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_dir / f"{test_name}.txt", "w") as f:
        for testfile, cov_diff in improved:
            f.write(f"Log file @ {timestamp}/{id}\n")
            f.write(f"Coverage Improve : {cov_diff.total_cov.covered}\n")
            f.write(f"{testfile.to_code()}\n")

    print(f"File written to {output_dir / f'{test_name}.txt'}")
