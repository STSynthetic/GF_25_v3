---
description: "GF-25 v3 Analysis Configuration Patterns"
globs: ["**/analysis/**/*.py", "**/config/**/*.yaml", "**/prompts/**/*.py"]
activation: "model_decision"
priority: "high"
version: "1.0"
---

# GF-25 v3 Analysis Configuration Patterns

## Meta Rule
**CRITICAL**: State "[ANALYSIS-CFG]" when applying these rules.

## YAML Configuration Architecture ([YAML-ARCH])

### **[ANALYSIS-CONFIG]**: 21 Analysis Type Configs
- **ALWAYS** create separate YAML config per analysis type from master_prompts.json
- **ALWAYS** include model parameters: `qwen2.5vl:32b`, temp=0.1, num_ctx=32768
- **ALWAYS** define validation_constraints with prohibited_language
- Pattern: `ages_analysis.yaml`, `themes_analysis.yaml` (21 total files)

```yaml
# Template structure for each analysis type
analysis_configuration:
  name: "Ages Analysis"
  model: "qwen2.5vl:32b"
  temperature: 0.1
  validation_constraints:
    prohibited_language: ["this image shows", "I can see"]
```

### **[CORRECTIVE-CONFIG]**: 21 Corrective Prompt Configs  
- **ALWAYS** create corrective YAML per analysis type
- **ALWAYS** include 3 stages: structural, content_quality, domain_expert
- **ALWAYS** use {{BASE64_IMAGE_PLACEHOLDER}}, {{OLLAMA_RESPONSE}} placeholders
- Pattern: `ages_corrective.yaml` with 3 correction stages per file

## Analysis Processing ([ANALYSIS-PROC])

### **[PROMPT-LOADING]**: Dynamic Configuration Loading
- **ALWAYS** load prompts from YAML configs, never hardcode
- **ALWAYS** validate YAML schema on load with Pydantic
- **ALWAYS** implement hot-reload for configuration changes
- Pattern: `config_manager.load_analysis_config(analysis_type)`

### **[IMAGE-PROCESSING]**: Vision Input Handling
- **ALWAYS** encode images as base64 with 1344px longest edge
- **ALWAYS** validate image formats: jpg, jpeg, png, webp
- **ALWAYS** implement caching with TTL for image downloads
- Pattern: `base64_image = encode_image_optimal(image_path, max_edge=1344)`

### **[RESPONSE-VALIDATION]**: Output Schema Enforcement
- **ALWAYS** validate JSON responses against analysis-specific schemas
- **ALWAYS** extract from master_prompts.json schema definitions
- **ALWAYS** trigger corrective processing on validation failure
- Pattern: `validate_analysis_result(result, AnalysisType.AGES)`

## Parallel Processing ([PARALLEL-PROC])

### **[CONCURRENT-ANALYSIS]**: 8-Thread Processing
- **ALWAYS** use asyncio.Semaphore(8) for parallel control
- **ALWAYS** distribute across specialized Redis queues per analysis type
- **ALWAYS** implement intelligent load balancing across GPU cores
- Pattern: `async with semaphore: await process_analysis_batch()`

### **[QUEUE-MANAGEMENT]**: Redis Queue Distribution
- **ALWAYS** create dedicated queues: ages_analysis_queue, themes_analysis_queue (21 total)
- **ALWAYS** implement queue-specific workers with analysis type specialization
- **ALWAYS** monitor queue depth and processing rates
- Pattern: `redis_client.lpush(f"{analysis_type}_analysis_queue", task_data)`

## Model Optimization ([MODEL-OPT])

### **[QWEN-PARAMS]**: Analysis Model Configuration
- **ALWAYS** optimize for analysis: temp=0.1, top_p=0.9, top_k=20, num_predict=1000
- **ALWAYS** configure vision params: min_pixels=846720, image_factor=28
- **ALWAYS** enable batch processing and memory efficiency
- Pattern: `{"temperature": 0.1, "num_ctx": 32768, "top_k": 20}`

### **[PERFORMANCE-TUNING]**: Throughput Optimization  
- **ALWAYS** preload both models: qwen2.5vl:32b and qwen2.5vl:latest
- **ALWAYS** use OLLAMA_NUM_PARALLEL=8 for concurrent processing
- **ALWAYS** monitor processing rates targeting 800+ analyses/hour per worker
- Pattern: `ollama.list()` to verify model availability before processing

## Analysis Type Implementation ([ANALYSIS-IMPL])

### **[SCHEMA-COMPLIANCE]**: JSON Output Validation
- **ALWAYS** follow exact schemas from master_prompts.json
- **ALWAYS** implement analysis-specific validators per type
- Ages: `{"ages": ["AGE_GROUP1"]}` with 8 valid age groups
- Themes: `{"themes": ["THEME1", "THEME2"]}` with 3-7 themes uppercase
- Pattern: `AgesAnalysisResult(BaseModel): ages: List[AgeGroup]`

### **[PROMPT-ENGINEERING]**: Quality Assurance Integration
- **ALWAYS** remove meta-descriptive language: "this image shows", "appears to be"
- **ALWAYS** ensure professional tone without observational phrases
- **ALWAYS** maintain analytical accuracy while improving expression
- Pattern: Content validation detects and corrects unprofessional language

## Critical Constraints

### **NEVER** Rules
- **NEVER** hardcode analysis prompts or model parameters
- **NEVER** skip JSON schema validation for analysis outputs
- **NEVER** allow meta-descriptive language in final responses
- **NEVER** process without Ollama optimization environment variables

### **ALWAYS** Rules
- **ALWAYS** load configurations from analysis_type.yaml files
- **ALWAYS** implement corrective processing for QA failures
- **ALWAYS** use specialized Redis queues per analysis type
- **ALWAYS** validate outputs against master_prompts.json schemas

---
**Source**: PRD Section 3, 7 - Analysis Features & YAML Architecture
**Character Count**: 3,985