from src.config import RUN_TEST
if RUN_TEST == "app":
    from src.runner.service import run_test
elif RUN_TEST == "test":
    from src.runner.local.run_test import run_test
