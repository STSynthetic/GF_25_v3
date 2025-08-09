---
trigger: always_on
description: "GF-25 v3 Core Python Standards"
globs: ["**/*.py", "src/**/*.py", "app/**/*.py"]
---

# GF-25 v3 Core Development Standards

## Meta Rule
**CRITICAL**: State "[CORE-STD]" when applying these rules.

## Essential Dependencies ([DEPS-CORE])

### **[UV-PKG]**: Package Management
- **ALWAYS** use `uv` for all dependency management
- **ALWAYS** pin versions: `pydantic>=2.5.0`, `fastapi>=0.104.0`
- Core stack: `pydantic`, `fastapi`, `uvicorn[standard]`, `httpx`, `redis`, `sqlalchemy`, `ollama`, `litellm`

### **[OLLAMA-OPT]**: Ollama Environment Optimization
- **ALWAYS** apply pre-job optimization per PRD Section 2
- **ALWAYS** set `OLLAMA_NUM_PARALLEL=8`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`
- **ALWAYS** configure `OLLAMA_MAX_VRAM=22000000000`, `OLLAMA_SCHED_SPREAD=true`
- Pattern: `os.environ.update(ollama_optimization_vars)`

## Type Safety Standards ([TYPE-SAFETY])

### **[PYDANTIC-V2]**: Data Validation
- **ALWAYS** use Pydantic v2 for all data models
- **ALWAYS** include Field descriptions for QA validation
- **NEVER** use raw dictionaries for API responses
- Pattern: `class AnalysisResult(BaseModel): confidence: float = Field(ge=0.0, le=1.0)`

### **[ENUM-TYPES]**: Analysis Type Safety
- **ALWAYS** use enums for 21 analysis types per master_prompts.json
- **ALWAYS** include QA stages: `structural`, `content_quality`, `domain_expert`
- Pattern: `class AnalysisType(str, Enum): AGES = "ages", THEMES = "themes"`

## Async Patterns ([ASYNC-CORE])

### **[HTTPX-CLIENT]**: HTTP Operations
- **ALWAYS** use `httpx.AsyncClient` for GoFlow API integration
- **ALWAYS** implement retry with tenacity for external services
- **ALWAYS** set timeouts: 30s for GoFlow, 60s for analysis, 10s for QA
- Pattern: `async with httpx.AsyncClient(timeout=30.0) as client:`

### **[CONCURRENT-PROCESSING]**: Parallel Analysis
- **ALWAYS** use `asyncio.gather()` for 8-thread processing
- **ALWAYS** implement semaphore for resource control
- Pattern: `semaphore = asyncio.Semaphore(8)`

## Model Configuration ([MODEL-CONFIG])

### **[QWEN-MODELS]**: Vision Model Setup
- **ALWAYS** use `qwen2.5vl:32b` for analysis stages
- **ALWAYS** use `qwen2.5vl:latest` for QA validation
- **ALWAYS** set analysis temp=0.1, QA temp=0.05
- Pattern: `{"model": "qwen2.5vl:32b", "temperature": 0.1, "num_ctx": 32768}`

### **[LITELLM-INTEGRATION]**: Agent SDK Bridge
- **ALWAYS** use LiteLLM for OpenAI Agent SDK + Ollama integration
- **ALWAYS** configure base_url: "http://localhost:11434"
- Pattern: `litellm.completion(model="ollama/qwen2.5vl:latest")`

## Error Handling ([ERROR-HANDLING])

### **[QA-FAILURES]**: Quality Assurance
- **ALWAYS** implement 3-tier QA: structural, content_quality, domain_expert
- **ALWAYS** route to corrective processing on validation failure
- **ALWAYS** limit corrective attempts to 3 per stage
- **NEVER** allow meta-descriptive language in outputs

### **[AGENT-COORDINATION]**: OpenAI Agent SDK
- **ALWAYS** use Agent SDK for QA orchestration per PRD Section 2
- **ALWAYS** implement agent handoffs between QA stages
- Pattern: `class StructuralQAAgent(Agent): model="ollama/qwen2.5vl:latest"`

## Critical Constraints

### **NEVER** Rules
- **NEVER** hardcode analysis prompts (use YAML configs)
- **NEVER** skip Ollama optimization before job processing
- **NEVER** use synchronous I/O for image downloads or API calls
- **NEVER** allow unvalidated JSON responses from analysis

### **ALWAYS** Rules
- **ALWAYS** validate against 21 analysis schemas from master_prompts.json
- **ALWAYS** implement Redis queue management for specialized queues
- **ALWAYS** persist state to PostgreSQL with comprehensive audit trails
- **ALWAYS** use base64 image encoding with {{BASE64_IMAGE_PLACEHOLDER}}

---
**Source**: PRD Section 2, 4, 7 - Core Technical Architecture
**Character Count**: 3,847