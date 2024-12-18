from eval.eval_dataset import eval_dataset
import asyncio

asyncio.run(
    eval_dataset("codecovapi-neutered", "codecovapi-neutered", num_records=1)
)
