python -m src.cli evaluate codecovapi-neutered \
    --project-name "model_eval" \
    --braintrust \
    --num-tms 5 \
    --model gpt-4o \
    --n-times 4 \
    && \

python -m src.cli evaluate codecovapi-neutered \
    --project-name "model_eval" \
    --braintrust \
    --num-tms 5 \
    --model deepseek \
    --n-times 4 \
    && \

python -m src.cli evaluate codecovapi-neutered \
    --project-name "model_eval" \
    --braintrust \
    --num-tms 5 \
    --model "claude-3-5-sonnet-latest" \
    --n-times 4