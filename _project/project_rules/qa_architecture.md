---
description: "GF-25 v3 QA System & Agent SDK Architecture"
globs: ["**/qa/**/*.py", "**/agents/**/*.py", "**/corrective/**/*.py"]
activation: "model_decision"
priority: "high"
version: "1.0"
---

# GF-25 v3 Quality Assurance Architecture

## Meta Rule
**CRITICAL**: State "[QA-ARCH]" when applying these rules.

## OpenAI Agent SDK Integration ([AGENT-SDK])

### **[AGENT-FACTORY]**: Dynamic Agent Instantiation
- **ALWAYS** use Agent Factory pattern: 3 agent templates, 21 corrective profiles
- **ALWAYS** implement StructuralQAAgent, ContentQualityAgent, DomainExpertAgent classes
- **ALWAYS** configure agents with `model="ollama/qwen2.5vl:latest"` via LiteLLM
- Pattern: `Agent(name="structural_validator", model="ollama/qwen2.5vl:latest")`

### **[AGENT-COORDINATION]**: Sequential QA Processing
- **ALWAYS** process validation in sequence: structural → content_quality → domain_expert
- **ALWAYS** implement context sharing between agent stages
- **ALWAYS** trigger corrective processing on agent failure detection
- Pattern: `await orchestrator.sequential_validation(agents, context)`

## Three-Tier QA System ([QA-TIERS])

### **[TIER1-STRUCTURAL]**: JSON Schema Validation
- **ALWAYS** validate JSON structure with compiled Pydantic models
- **ALWAYS** check field presence, data types, enumeration compliance
- **ALWAYS** complete structural validation under 100ms
- Pattern: `StructuralValidator.validate(json_response, analysis_schema)`

### **[TIER2-CONTENT]**: Quality & Language Validation
- **ALWAYS** detect meta-descriptive language patterns via qwen2.5vl:latest
- **ALWAYS** scan for prohibited phrases: "this image shows", "I can see", "appears to be"
- **ALWAYS** validate professional tone and analytical expression
- Pattern: `ContentQualityAgent.detect_meta_descriptive(response_text)`

### **[TIER3-DOMAIN]**: Expert-Level Validation
- **ALWAYS** apply domain expertise validation per analysis type
- **ALWAYS** verify confidence scores and professional accuracy
- **ALWAYS** ensure cultural sensitivity for demographic analysis
- Pattern: `DomainExpertAgent.validate_expertise(analysis_result, domain_context)`

## Corrective Processing System ([CORRECTIVE-SYS])

### **[CORRECTIVE-PROMPTS]**: Stage-Specific Correction
- **ALWAYS** load corrective prompts from analysis_type_corrective.yaml
- **ALWAYS** include {{BASE64_IMAGE_PLACEHOLDER}} and {{OLLAMA_RESPONSE}} in prompts
- **ALWAYS** apply stage-specific correction: structural/content_quality/domain_expert
- Pattern: `corrective_config['structural']['system_prompt'].replace(placeholders)`

### **[CORRECTION-CYCLES]**: Progressive Enhancement
- **ALWAYS** limit corrective attempts to 3 per stage maximum
- **ALWAYS** implement progressive enhancement with each attempt
- **ALWAYS** re-validate corrected outputs through QA pipeline
- Pattern: `for attempt in range(3): corrected = await apply_correction()`

### **[AGENT-TOOLS]**: Function Tool Integration
- **ALWAYS** implement @function_tool decorators for Agent SDK tools
- **ALWAYS** provide validate_structure, detect_meta_language, expert_assess tools
- **ALWAYS** return structured validation results with confidence scores
- Pattern: `@function_tool def validate_structure(json_data: str) -> ValidationResult`

## Model Configuration for QA ([QA-MODEL-CONFIG])

### **[QA-OPTIMIZATION]**: qwen2.5vl:latest Parameters
- **ALWAYS** use ultra-low temperature: 0.05 for validation consistency
- **ALWAYS** configure high precision: top_p=0.95, top_k=10
- **ALWAYS** limit context: num_ctx=16384, num_predict=500 for QA tasks
- Pattern: `{"temperature": 0.05, "top_p": 0.95, "num_predict": 500}`

### **[CORRECTIVE-OPTIMIZATION]**: Correction Model Settings
- **ALWAYS** optimize for corrective processing: temp=0.1, focused vocabulary
- **ALWAYS** preserve context and maintain analytical accuracy
- **ALWAYS** enable structured output enforcement for corrections
- Pattern: `corrective_params = {"temperature": 0.1, "context_preservation": True}`

## LiteLLM Integration ([LITELLM-QA])

### **[OLLAMA-BRIDGE]**: Agent SDK to Ollama Bridge
- **ALWAYS** configure LiteLLM base_url: "http://localhost:11434"
- **ALWAYS** use "ollama/" prefix for model names in Agent SDK
- **ALWAYS** implement error handling for LiteLLM connection failures
- Pattern: `litellm.completion(model="ollama/qwen2.5vl:latest", base_url=ollama_url)`

### **[AGENT-COMMUNICATION]**: Inter-Agent Messaging
- **ALWAYS** implement agent handoff protocols with context preservation
- **ALWAYS** aggregate validation results across all three tiers
- **ALWAYS** provide comprehensive QA reports with failure reasons
- Pattern: `HandoffContext(validation_history, failure_patterns, correction_attempts)`

## QA Performance Targets ([QA-PERFORMANCE])

### **[VALIDATION-SPEED]**: QA Processing Targets
- **ALWAYS** complete Tier 1 structural validation under 100ms
- **ALWAYS** complete Tier 2 content validation under 3 seconds
- **ALWAYS** complete Tier 3 domain validation under 5 seconds
- **ALWAYS** achieve total QA cycle under 10 seconds including correction

### **[SUCCESS-RATES]**: Quality Metrics
- **ALWAYS** target 95%+ QA failure detection across all tiers
- **ALWAYS** achieve 95%+ corrective processing success rate
- **ALWAYS** ensure compliance with analysis-type requirements or route to manual review
- Pattern: `qa_metrics.success_rate >= 0.95`

## Error Handling & Recovery ([QA-ERROR])

### **[FAILURE-ROUTING]**: Manual Review Escalation
- **ALWAYS** route to manual review after 3 failed correction attempts
- **ALWAYS** preserve complete correction history for manual reviewers
- **ALWAYS** implement escalation thresholds per analysis type
- Pattern: `if correction_attempts >= 3: route_to_manual_review(task, history)`

### **[AGENT-FAILURES]**: Agent SDK Error Management
- **ALWAYS** handle Agent SDK connection failures gracefully
- **ALWAYS** implement fallback validation for agent communication errors
- **ALWAYS** log agent performance metrics for optimization
- Pattern: `try: agent_result = await agent.validate() except: fallback_validation()`

## Critical Constraints

### **NEVER** Rules
- **NEVER** skip any of the three QA tiers for analysis outputs
- **NEVER** allow meta-descriptive language in corrected responses
- **NEVER** exceed 3 corrective attempts per QA stage
- **NEVER** process without Agent SDK coordination for QA

### **ALWAYS** Rules
- **ALWAYS** use OpenAI Agent SDK for QA orchestration per PRD Section 2
- **ALWAYS** implement corrective processing with stage-specific prompts
- **ALWAYS** validate corrected outputs through complete QA pipeline
- **ALWAYS** preserve original image context in all correction attempts

---
**Source**: PRD Section 2, 3 - Enhanced QA System & Agent SDK
**Character Count**: 3,948