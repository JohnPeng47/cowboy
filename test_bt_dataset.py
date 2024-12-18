from braintrust import Eval, traced
from braintrust_core import score
from typing import Dict
import random
import dotenv

dotenv.load_dotenv()

@traced(name="hello???")
def task(input: Dict):
    return random.randrange(0,5)

def duhuh(output, expected):
    return 5

Eval(
    name="test-scorer",
    data = [
        {"name": f"test_data", "tags": ["superlongtagggggggggggggggggggggg"], "input": [], "expected": 5, "metadata": {"hello": 5}}
        for _ in range(5)
    ],
    task=task,
    scores=[duhuh]
)