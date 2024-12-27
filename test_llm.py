from src.llm import LLMModel, Model
import dotenv

dotenv.load_dotenv()

model = LLMModel()
res = model.invoke("hello?", model_name="gpt-4o")
print("GPT4O: ", res)

model = LLMModel()
res = model.invoke("hello?", model_name=Model.CLAUDE)
print("GPT4O: ", res)