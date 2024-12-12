# What is this
This is a tool that can be used to automatically generate unit test cases with LLMs to extend existing unit tests suites, with zero manual interaction apart from some initial configuration
The test generation flow goes something like this:
1. Create repo
2. Find all TestModules inside repo. A TestModule is just a container for a set of tests. In Python/Pytest, it is either the source file of the test itself or its a class that implements its testcases as methods. Each TestModule will be associated with a single test file.

------------------------------------------------------------------------------------------------------------------------------------
test_file.py

import pytest
def test1(): 
  ...
  
def test2():
  ...

class TestClass:
  def test_meth1():
    ...
  def test_meth2():
    ...
------------------------------------------------------------------------------------------------------------------------------------
So for the above, two TestModules will be created, along with their associated tests 
TM1: test_file.py --(tests)--> test_file.py::test1, test_file.py::test2
TM2: TestClass    --(tests)--> TestClass::test_meth1, TestClass::test_meth2 

3. For each test TestModule, we then attempt to build a test_file -> source_file mapping. This is accomplished by a novel coverage diffing algorithm that iterates through each test in a TestModule and calculates the line coverage difference (set diff, ie. [1,2,3] - [1,2] = 3) between itself and the TestModule. Summing these line coverages together, we get a set of source file lines that are *uniquely* covered by the tests in the TestModule (more notes on this in following section)
4. For each TestModule, prompt a LLM with the following to generate a batch of tests
"""
Given the following existing test suite:
{existing_tests}
For the source file(s):
{source_file for source_file in from_step3}
Extend it with additional unittests that improve coverage
"""
(While it is possible generate tests without the source_files, empirical results suggests a significant reduction in quality as measured by total coverage contributed, up to 30-40% if the source_file context is not provided)
5. Get the coverage contributed by each new testfile. Throw away all those that error'd out or failed to contribute coverage
6. Write the coverage improving tests to the test file, loop 4-6 until some iterations N has been reached. This way of incrementally adding new generated tests to the prompt context pushes the LLM to consider new uncovered test conditions
7. Collect generated tests, each contributing new coverage. Win!

# Finding Target Coverage
This is not exactly a foolproof way to calculate the test -> src mappping as the existence of *uniquely* covered lines is not guranteed, since tests will depend on similar system components, leading to an overlap in their execution traces. This is the reason why I opted to compare test line coverage against TestModule line coverage rather than the whole repo coverage, because the repo 
The reason to diff the test lines against the TestModule rather than the whole repo coverage is because the repo wide test covers more lines, thereby making chance of overlap more likely. Also, repo wide code coverages take a long time to run.

# Code Highlights
cowboy_lib/coverage.py -> structure that implements all coverage diffing logic

# Dataset:
Each row of the dataset represents a TestModule, a generic container that I use to group testcases. In the case of python, it is either a unit test file or a class implementing many test cases.
The output column contains the list of unit tests generated as well as the total coverage improvement
The expected column is the total coverage from the removed tests from the TestModule
