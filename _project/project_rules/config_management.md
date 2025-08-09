---
description: "GF-25 v3 YAML Configuration Architecture"
globs: ["**/config/**/*.py", "**/*.yaml", "**/settings/**/*.py"]
activation: "always_on"
priority: "high"
version: "1.0"
---

# GF-25 v3 Configuration Management Architecture

## Meta Rule
**CRITICAL**: State "[CONFIG-ARCH]" when applying these rules.

## YAML-Driven Configuration System ([YAML-CONFIG])

### **[CONFIG-STRUCTURE]**: Centralized Configuration Architecture
- **ALWAYS** organize configs: base/, environments/, components/, schemas/ per PRD Section 7
- **ALWAYS** implement hot-reload capabilities for runtime configuration updates
- **ALWAYS** validate YAML schemas with Pydantic models before application
- Pattern: `config/base/application.yaml`, `config/components/analysis_type.yaml`

### **[HOT-RELOAD]**: Runtime Configuration Updates
- **ALWAYS** monitor YAML files with file system watchers
- **ALWAYS** apply debouncing to prevent rapid-fire configuration updates
- **ALWAYS** notify registered components of configuration changes
- **ALWAYS** provide rollback capability if validation fails
- Pattern: `config_manager.register_reload_callback(component.reload_config)`

### **[ENVIRONMENT-OVERRIDES]**: Multi-Environment Support
- **ALWAYS** implement environment-specific overrides: development.yaml, staging.yaml, production.yaml
- **ALWAYS** merge base configurations with environment-specific settings
- **ALWAYS** use environment variables for sensitive data with ${VAR_NAME} syntax
- Pattern: `merged_config = merge_configs(base_config, env_overrides[environment])`

## Analysis Configuration Management ([ANALYSIS-CONFIG])

### **[21-ANALYSIS-CONFIGS]**: Analysis Type Configurations
- **ALWAYS** create dedicated YAML per analysis type from master_prompts.json
- **ALWAYS** include model parameters, prompts, validation constraints per analysis
- **ALWAYS** implement analysis-specific optimization profiles
- Pattern: `ages_analysis.yaml`, `themes_analysis.yaml` with model: "qwen2.5vl:32b"

### **[21-CORRECTIVE-CONFIGS]**: Corrective Processing Configurations
- **ALWAYS** create corrective YAML per analysis type with 3 stages each
- **ALWAYS** include stage-specific prompts: structural, content_quality, domain_expert
- **ALWAYS** use placeholder templates: {{BASE64_IMAGE_PLACEHOLDER}}, {{OLLAMA_RESPONSE}}
- Pattern: `ages_corrective.yaml` with corrective_stages: structural, content_quality, domain_expert

### **[PROMPT-TEMPLATING]**: Dynamic Prompt Generation
- **ALWAYS** support template variables with Jinja2-style syntax
- **ALWAYS** validate template rendering before model submission
- **ALWAYS** implement prompt versioning for audit and rollback
- Pattern: `system_prompt.replace("{{BASE64_IMAGE_PLACEHOLDER}}", base64_image)`

## System Configuration ([SYSTEM-CONFIG])

### **[OLLAMA-OPTIMIZATION]**: Performance Configuration
- **ALWAYS** configure Ollama environment variables via YAML per PRD Section 2
- **ALWAYS** include flash_attention, kv_cache_type, num_parallel settings
- **ALWAYS** implement pre-job optimization application with validation
- Pattern: `ollama_performance: {flash_attention: true, num_parallel: 8, kv_cache_type: "q8_0"}`

### **[MODEL-CONFIGURATIONS]**: AI Model Settings
- **ALWAYS** separate configurations for qwen2.5vl:32b (analysis) and qwen2.5vl:latest (QA)
- **ALWAYS** include temperature, top_p, top_k, num_ctx, num_predict parameters
- **ALWAYS** implement model-specific optimization profiles
- Pattern: `analysis_model: {name: "qwen2.5vl:32b", temperature: 0.1, num_ctx: 32768}`

### **[INTEGRATION-CONFIGS]**: External Service Configuration
- **ALWAYS** configure GoFlow API endpoints, Discord webhooks, Redis connections
- **ALWAYS** implement timeout, retry, authentication settings per service
- **ALWAYS** use environment variable substitution for credentials
- Pattern: `goflow_api: {base_url: "${GOFLOW_API_URL}", timeout_seconds: 30}`

## Configuration Validation ([CONFIG-VALIDATION])

### **[SCHEMA-VALIDATION]**: Pydantic Schema Enforcement
- **ALWAYS** define Pydantic models for all configuration structures
- **ALWAYS** validate configurations on load with comprehensive error reporting
- **ALWAYS** implement nested validation for complex configuration hierarchies
- Pattern: `class AnalysisConfig(BaseModel): model: str, temperature: float = Field(ge=0.0, le=2.0)`

### **[DEPENDENCY-VALIDATION]**: Cross-Configuration Consistency
- **ALWAYS** validate model availability before configuration application
- **ALWAYS** check service endpoint connectivity during configuration validation
- **ALWAYS** verify required environment variables are present and valid
- Pattern: `await validate_ollama_model_availability(config.analysis_model.name)`

### **[CONFIGURATION-TESTING]**: Validation Testing
- **ALWAYS** implement configuration validation tests for all YAML files
- **ALWAYS** test environment-specific overrides and merging logic
- **ALWAYS** validate template rendering with sample data
- Pattern: `test_config_validation(ages_analysis_yaml, AgesAnalysisConfig)`

## Performance Configuration ([PERF-CONFIG])

### **[PARALLEL-PROCESSING]**: Concurrency Configuration
- **ALWAYS** configure thread counts, semaphore limits, batch sizes via YAML
- **ALWAYS** implement worker pool sizing and queue management settings
- **ALWAYS** optimize for 8-thread processing with 16 GPU cores per PRD
- Pattern: `parallel_optimization: {thread_pool_size: 8, gpu_core_utilization: 16}`

### **[CACHE-CONFIGURATION]**: Performance Caching
- **ALWAYS** configure Redis caching TTL, memory limits, eviction policies
- **ALWAYS** implement image caching settings with size and duration limits
- **ALWAYS** configure model response caching for repeated analysis patterns
- Pattern: `image_caching: {local_cache_dir: "/app/cache", ttl_hours: 24, cache_size_gb: 50}`

### **[MONITORING-CONFIG]**: Observability Configuration
- **ALWAYS** configure metrics collection intervals and retention policies
- **ALWAYS** implement alert thresholds and notification settings
- **ALWAYS** configure performance monitoring with target SLAs
- Pattern: `monitoring: {metrics_interval: 30, alert_thresholds: {qa_failure_rate: 0.1}}`

## Configuration Security ([CONFIG-SECURITY])

### **[SECRET-MANAGEMENT]**: Secure Configuration Handling
- **ALWAYS** use environment variable substitution for all sensitive data
- **ALWAYS** implement configuration encryption for sensitive YAML sections
- **ALWAYS** validate environment variable presence during configuration loading
- Pattern: `api_key: "${GOFLOW_API_KEY}"` with validation for missing variables

### **[ACCESS-CONTROL]**: Configuration Change Control
- **ALWAYS** implement configuration change logging and audit trails
- **ALWAYS** require authentication for configuration reload endpoints
- **ALWAYS** validate configuration change permissions per environment
- Pattern: `@requires_admin async def reload_config(config_type: str):`

### **[BACKUP-STRATEGIES]**: Configuration Versioning
- **ALWAYS** maintain configuration version history in version control
- **ALWAYS** implement configuration rollback capabilities
- **ALWAYS** create configuration snapshots before major changes
- Pattern: `config_snapshot = create_config_backup(current_config, timestamp)`

## Developer Experience ([DEV-EXPERIENCE])

### **[CONFIG-TOOLING]**: Development Support
- **ALWAYS** provide configuration validation CLI tools
- **ALWAYS** implement configuration diff tools for change comparison
- **ALWAYS** create configuration templates for new analysis types
- Pattern: `python -m config validate analysis_configs/`

### **[DOCUMENTATION]**: Configuration Documentation
- **ALWAYS** maintain comprehensive configuration documentation
- **ALWAYS** document all configuration options with examples and constraints
- **ALWAYS** provide troubleshooting guides for common configuration issues
- Pattern: `# ages_analysis.yaml - Configuration for age demographic analysis`

### **[ERROR-REPORTING]**: Configuration Error Handling
- **ALWAYS** provide detailed error messages for configuration validation failures
- **ALWAYS** include suggested corrections for common configuration errors
- **ALWAYS** implement configuration health checks with actionable feedback
- Pattern: `ConfigValidationError(f"Invalid temperature {temp}, must be 0.0-2.0")`

## Critical Constraints

### **NEVER** Rules
- **NEVER** hardcode configuration values in source code
- **NEVER** skip configuration validation before application
- **NEVER** store sensitive data in YAML files without encryption
- **NEVER** ignore configuration reload failures

### **ALWAYS** Rules
- **ALWAYS** use YAML-driven configuration for all system behavior
- **ALWAYS** implement hot-reload capabilities for operational flexibility
- **ALWAYS** validate configurations with Pydantic schemas
- **ALWAYS** maintain configuration audit trails and version control

---
**Source**: PRD Section 7 - YAML Configuration Architecture
**Character Count**: 3,958