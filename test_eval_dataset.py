from src.eval.eval_augment import eval_dataset
import asyncio

asyncio.run(eval_dataset("textual-neutered", "textual-neutered"))
