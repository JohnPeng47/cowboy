from src.eval.datasets import read_rows, TestModuleEvalData

dataset = read_rows("codecovapi-neutered")
for d in dataset:
    print(d.to_json().keys())
    # print(TestModuleRow.from_json(d.to_json()))