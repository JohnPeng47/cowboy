Evaluations are performed on "neutered" repos, which is a pre-processing step that first eliminates some pre-existing test cases from each TestModule. This is done because:
1. To make it easier to generate non-coverage saturating tests
2. For every test removed, its unique coverage contribution is accumulated in a total_coverage variable that is then used as a benchmark for measuring the coverage improvements of generated tests. Specifically, the evaluation criteria for generated tests is:
score = sum([t.new_coverage for t in new_tests]) / total_coverage 

Currently, evaluation results are uploaded and displayed via Braintrust (https://www.braintrust.dev). 
