from src.llm import LLMModel
import dotenv

dotenv.load_dotenv()


# NOTE: responses are already cached in model
def test_cached_invoke():
    POETRY = [
        "Whispers of dawn paint the sky with golden hope.",
        "Whispers of stars adorn the silent night's embrace.",
        "Whispers of starlight kiss the silent sea."
    ]

    model = LLMModel()
    for i in range(3):
        res = model.invoke(
            "Write a single line of good poetry", 
            model_name="gpt-4o", 
            use_cache= True, 
            key=i,
            delete_cache=False
        )

        assert res == POETRY[i]

    