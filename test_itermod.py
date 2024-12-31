from pathlib import Path

from src.test_modules.iter_tms import iter_test_modules

from cowboy_lib.repo.source_repo import SourceRepo

src_repo = SourceRepo(Path("/home/ubuntu/codecov-api"))
tms = iter_test_modules(src_repo, lambda tm: tm.name == "test_serializers.py")
for t in tms:
    for test in t.tests:
        print(test.name)