TOKEN_COST = {
    "gpt-4o": {
        "max_tokens": 16384,
        "max_input_tokens": 128000,
        "max_output_tokens": 16384,
        "input_cost_per_token": 0.0000025,
        "output_cost_per_token": 0.00001,
        "input_cost_per_token_batches": 0.00000125,
        "output_cost_per_token_batches": 0.000005,
        "cache_read_input_token_cost": 0.00000125,
        "supports_function_calling": True,
        "supports_parallel_function_calling": True,
        "supports_response_schema": True,
        "supports_vision": True,
        "supports_prompt_caching": True,
        "supports_system_messages": True
    },
    "claude-3-5-sonnet-20240620": {
        "max_tokens": 8192,
        "max_input_tokens": 200000,
        "max_output_tokens": 8192,
        "input_cost_per_token": 0.000003,
        "output_cost_per_token": 0.000015,
        "cache_creation_input_token_cost": 0.00000375,
        "cache_read_input_token_cost": 3e-7,
        "supports_function_calling": True,
        "supports_vision": True,
        "tool_use_system_prompt_tokens": 159,
        "supports_assistant_prefill": True,
        "supports_prompt_caching": True,
        "supports_response_schema": True
    },
    "deepseek/deepseek-chat": {
        "max_tokens": 4096,
        "max_input_tokens": 128000,
        "max_output_tokens": 4096,
        "input_cost_per_token": 1.4e-7,
        "input_cost_per_token_cache_hit": 1.4e-8,
        "cache_read_input_token_cost": 1.4e-8,
        "cache_creation_input_token_cost": 0,
        "output_cost_per_token": 2.8e-7,
        "supports_function_calling": True,
        "supports_assistant_prefill": True,
        "supports_tool_choice": True,
        "supports_prompt_caching": True
    }
}
