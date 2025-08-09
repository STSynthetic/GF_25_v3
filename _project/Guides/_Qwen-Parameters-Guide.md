# Qwen2.5VL:32b Parameter Guide for Ollama

This document explains the various parameters that can be passed to the Qwen2.5VL:32b model when using it through Ollama, helping you optimize output quality, control behavior, and tailor the model's responses to your specific needs.

## Core Ollama Parameters

These parameters control the general behavior of the language model:

### temperature
- **Range**: 0.0 - 1.0
- **Purpose**: Controls the randomness of the output
- **Usage**:
  - Low values (0.1-0.3): More deterministic, factual responses
  - Medium values (0.4-0.6): Balanced creativity and accuracy
  - High values (0.7-0.9): More creative, varied responses
- **Best Practice**: Use 0.1-0.3 for factual tasks, 0.7-0.9 for creative tasks

### top_p
- **Range**: 0.0 - 1.0
- **Purpose**: Nucleus sampling parameter that controls diversity
- **Description**: Limits the cumulative probability of tokens considered for sampling

### top_k
- **Range**: Integer values
- **Purpose**: Limits the number of highest probability tokens considered
- **Description**: Restricts sampling to the top k most likely tokens

### num_predict
- **Range**: Integer values
- **Purpose**: Maximum number of tokens to generate
- **Description**: Controls the length of the model's response

### num_ctx
- **Range**: Integer values
- **Purpose**: Context window size
- **Description**: Number of tokens the model considers from the input

### seed
- **Range**: Integer values
- **Purpose**: Reproducibility
- **Description**: Sets a fixed seed for deterministic outputs

### stop
- **Type**: Array of strings
- **Purpose**: Defines stop sequences
- **Description**: Tokens that will cause the model to stop generating

### num_gpu
- **Range**: Integer values
- **Purpose**: GPU allocation
- **Description**: Number of GPU layers to use

### keep_alive
- **Type**: String (time format)
- **Purpose**: Model memory retention
- **Description**: How long to keep the model loaded in memory

## Vision-Specific Parameters

These parameters are specific to the vision capabilities of Qwen2.5VL:

### Resolution Control

#### min_pixels
- **Purpose**: Minimum image resolution for processing
- **Example**: `min_pixels = 256 * 28 * 28`

#### max_pixels
- **Purpose**: Maximum image resolution for processing
- **Example**: `max_pixels = 1280 * 28 * 28`

### Video Processing Parameters

#### total_pixels
- **Purpose**: Maximum pixel budget for video sequences
- **Example**: `total_pixels = 24576 * 28 * 28`

#### fps
- **Purpose**: Frame sampling rate
- **Example**: `fps = 1.0` (1 frame per second)

## Parameter Usage Examples

### Factual Analysis (Low Creativity)
```python
options = {
  "temperature": 0.1,
  "top_p": 0.9,
  "num_predict": 1000
}
```

### Creative Analysis (High Creativity)
```python
options = {
  "temperature": 0.8,
  "top_p": 0.9,
  "num_predict": 1500
}
```

### JSON Output Control
```python
options = {
  "temperature": 0.3,
  "num_predict": 1200,
  "stop": ["\n\n", "}\n"]
}
```

## Best Practices for Parameter Tuning

1. **Start with defaults**: Begin with the recommended values and adjust based on results
2. **Adjust one parameter at a time**: This helps isolate the effects of each change
3. **Use lower temperatures for factual tasks**: 0.1-0.3 for data extraction, analysis
4. **Use higher temperatures for creative tasks**: 0.7-0.9 for descriptions, storytelling
5. **Control output length**: Set appropriate `num_predict` values to prevent run-on responses
6. **Ensure reproducibility**: Use `seed` parameter when consistent outputs are needed
7. **Optimize for hardware**: Adjust `num_gpu` based on available VRAM
8. **Manage resources**: Use `keep_alive` to control memory usage

## Parameter Interactions

- **temperature and top_p**: Both control randomness but in different ways; using both gives finer control
- **num_predict and stop**: The model will stop at the earlier of reaching `num_predict` tokens or encountering a stop sequence
- **num_ctx and input length**: Ensure `num_ctx` is large enough to accommodate your full prompt

This guide provides a comprehensive overview of the parameters available for controlling Qwen2.5VL:32b behavior through Ollama. Experiment with different combinations to find the optimal settings for your specific use cases.
