from src.local.models import read_rows
from cowboy_lib.coverage import TestCoverage
from src.local.db import get_tm


repo_name = "codecovapi-neutered"
tms = [
    "TestImpactedFile",
    "TestOwnerMeasurements",
    "TestStaticAnalysisSuiteSerializer",
    "CoverageViewSetTests",
    "OwnerViewSetTests",
    "FlagCommandsTest",
    "PullRequestComparisonTests",
    "RepoPullList",
    "ReportTreeTests",
    "SaveTermsAgreementMutationTest",
    "StripeWebhookHandlerTests",
    "SuperTokenAuthenticationTests"
] 

for tm_name in tms:
    tm = get_tm(repo_name, tm_name)
    print("___________________")
    for f in tm.targeted_files():
        print(str(f))
