from braintrust import Eval
from typing import Dict
import random
import dotenv

dotenv.load_dotenv()

def task(input: Dict):
    return random.randrange(0,5)

def scorer(output, expected):
    return output / expected

Eval(
    name="test-scorer",
    data = [{"input": [], "expected": 5} for _ in range(5)],
    task=task,
    scores=[scorer]
)