from src.local.models import read_rows 
from pathlib import Path

repo_name = "codecovapi-neutered"
selected_tms = [
    "PullRequestComparisonTests",
    "TestStaticAnalysisSuiteSerializer", 
    "UploadHandlerGithubActionsTokenlessTest",
    "SuperTokenAuthenticationTests"
]

rows = read_rows(repo_name,
                braintrust=True, 
                selected_tms=selected_tms)

base_path = "/home/ubuntu/codecov-api"


for data in rows:
    print(f"TM: {data.name}")
    data.expected.read_line_coverage(Path(base_path))
    for cov in data.expected.cov_list:
        print(cov.print_lines())