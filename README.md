# What is this
This is a tool that can be used to automatically generate unit test cases with LLMs and to extend existing unit tests suites. Note that 

TestModule, a generic container that I use to group testcases. In the case of python, it is either a unit test file or a class implementing many test cases.


# Evaluations
Currently only public evaluation I have is on https://github.com/codecov/codecov-api.git
Here is the link (may need to sign up for a BrainTrust account)
<link>
The data set is constructed by iterating through each testsuite in the repo and removing testcases until 2 are left (src/evals/create_dataset.py). Reason I do this is, coverage gain is currently the only reliable evaluation metric I have for good tests. Most testsuites though have already saturated coverage, so removing some testcases makes it more likely that generated tests will increase coverage

Dataset:
Each row of the dataset represents a TestModule, a generic container that I use to group testcases. In the case of python, it is either a unit test file or a class implementing many test cases.
The output column contains the list of unit tests generated as well as the total coverage improvement
The expected column is the total coverage from the removed tests from the TestModule
