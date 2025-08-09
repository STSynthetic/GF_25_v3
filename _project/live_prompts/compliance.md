# Production Compliance & Feature Checklist  
**Automated Image Analysis Workflow System**  
_Expanded, Detailed Compliance Document for AI Codebase Review (Aligned with PRD v2.4 – July 2025)_

## Section 1. Core Architecture Principles

### 1.1. Configuration-Driven Architecture

- **All business logic, prompts, constraints, validation, and performance settings are externalized into YAML configuration files**.  
  - No hardcoded business logic or analysis type lists anywhere in the codebase.
- **21 analysis types**, each in its own YAML file as per PRD, auto-discovered at runtime.
- **Runtime hotswapping** supports configuration reloads without code changes or restarts.

### 1.2. Type-Safe Enum Handling

- **AnalysisType enum** (code-level) provides:
  - Full mapping of all supported types (slug, display, filename).
  - IDE-supported auto-completion, compile-time validation.
  - Prevents any string-based mismatches or invalid values.

### 1.3. Centralized Configuration Management

- **Single configuration loader** with:
  - TTL-based cache with invalidation and atomic reload.
  - Deep schema validation of *every* YAML field (meta, prompts, constraints, models, error-handling).
  - Environment-aware overrides (`development`, `production`).

## Section 2. Workflow Orchestration & Dependency Injection

### 2.1. Unified Orchestrator Backbone

- `WorkflowOrchestrator` is constructed via dependency injection (services provided as arguments—not instantiated within).
- **Services injected:**
  - JobAcquisition: GoFlow API requests.
  - ImageManager: Downloads, organizes, validates all images before processing.
  - VisionClient: Model management and Ollama requests.
  - ConfigValidator: Validates loaded YAML and runtime state.
  - Logger: Job-specific structured logging.

### 2.2. Top-Level Workflow Lifecycle

- **Pre-flight:**
  - Ollama optimization via shell script, YAML-driven env constants.
- **Job Acquisition:**
  - GoFlow `/next-job` endpoint: Pulls jobs, validates every field; verifies API-key.
  - UUID extraction and mapping for client/project/media/analysis.
- **Manifest Generation:**
  - `job_metadata.json`: PRD-compliant job info + full API payload.
  - `manifest.json`: Detailed, auditable matrix—tracks by image, analysis type, task, QA tier, retries, timestamps.
- **Checkpoint System:**
  - Microsecond-precision checkpoint files written atomically for every batch step.
  - Auto-resume from last checkpoint after interruption.
- **Path Management:**
  - Centralized, environment-based path service ensures consistent directory and output structure.

## Section 3. YAML Configuration & Dynamic Validation

### 3.1. Analysis Type Configuration (per-Module)

Every `analysis_type.yaml` must contain, at minimum:

| Field                   | Description                                            | Required      |
|-------------------------|--------------------------------------------------------|---------------|
| `analysis_type`         | Unique ID (slug; maps to enum variant)                | Yes           |
| `name/description`      | Human-readable label and task summary                 | Yes           |
| `version`               | Schema/config version                                 | Yes           |
| `image_format_required` | COLOR or BLACK_AND_WHITE (mandatory selection)         | Yes           |
| `model_configuration`   | `primary_model`, `fallback_model`, quantization, etc. | Yes           |
| `system_prompt`         | Full methodology, guidelines, meta-desc prevention    | Yes           |
| `user_prompt`           | Task-specific, output format, meta-desc prevention    | Yes           |
| `validation_constraints`| Min/max sentences, chars, regex prohibited patterns   | Yes           |
| `output_schema`         | Dynamic, Pydantic-compatible JSON schema for outputs  | Yes           |
| `error_handling`        | JSON fallback for timeout/validation/processing errors| Yes           |
| `performance`           | Cache, concurrency, strictness flags                  | Yes           |
| `execution_settings`    | Overrides for environment                             | Yes           |
| `tier3_validation`      | Expert review and semantic rules                      | Yes           |

- **All prompts and constraints must explicitly ban meta-descriptive/self-referential language** (e.g.: "This image shows...", "In this photo...")
- **Output schema** enforced at runtime—only fields defined are allowed (no additional keys).

### 3.2. Centralized Model Registry

- Only models defined in `ollama_config.yaml` can be referenced in analysis configs.
- All model settings (name, quantization, context, tokens, temperature, performance, availability) are controlled in registry for global updates.

## Section 4. Parallelism & Resource Management

### 4.1. Image & Analysis Task Scheduling

- **Image-level parallelism:** Up to 5 concurrent images (`OLLAMA_NUM_PARALLEL=5` as per optimization guide).
- **Per-image, analysis types are run sequentially** per PRD—never all at once (memory conservation).
- **Resource semaphores** enforce concurrency caps; async/await used for all I/O and network operations.
- **Circuit breaker:** If >30% analyses fail, batch is halted, status/logs updated.

### 4.2. Image Handling Constraints

- **All images downloaded (color + greyscale) before any analysis starts.**
- **Strict image selection:** JPEG preferred, 1344px longest edge, min 224x224; no preprocessing in code (pre-optimized from API).
- **Directory structure:**
  ```
  /output/{job_id}/images/color/
  /output/{job_id}/images/bw/
  ```

## Section 5. Three-Tier AI-Driven QA Validation

### 5.1. Tier 1 – Gatekeeper (Structure & Schema)

- Enforced via runtime-generated Pydantic models from YAML schemas.
- Checks:
  - Fields present, strictly typed.
  - Character and sentence count rules.
  - JSON structure matches `output_schema`.
  - Fails immediately if rules not met.

### 5.2. Tier 2 – Specialist (Meta-Descriptive & Prohibited Phrases)

- AI-based review (Ollama text model).
- All phrases/regex from YAML enforced (60+ percent coverage).
- Detects **semantic as well as literal meta-descriptive violations**.
- Immediate rejection if *any* pattern/phrase occurs.

### 5.3. Tier 3 – Expert (Semantic, Domain, Tone)

- AI expert reviews for:
  - Semantic coherence with system/user prompt and content guidelines.
  - Domain/subject matter accuracy.
  - Stylistic compliance (direct, non-meta, accessible tone).
  - Expert scoring; auto-escalation if <0.8 confidence.

### 5.4. Correction Loop

- For recoverable failures (as judged by Expert), AI-based correction is attempted using the context and expert feedback, preserving all valid data.
- Limited retries per constraint.

### 5.5. Manifest Tracking

- **Every QA tier’s result, retry count, errors, and timestamps are logged** by image and analysis type in manifest.json.
- **Per-task logs:**  
  ```
  /output/{job_id}/logs/processing.log
  /output/{job_id}/logs/qa_validation.log
  /output/{job_id}/logs/errors.log
  /output/{job_id}/logs/performance.log
  ```

## Section 6. GoFlow API Integration & Output Handling

### 6.1. API Job Handling

- **GET** `/api/v1/agent/next-job` to retrieve new job (validates structure, UUIDs, matches PRD).
- **POST** results using correct UUIDs: `/api/v1/agent/projects/{projectId}/media/{mediaId}/analysis/{analysisId}`.
- **Only requested (not all) analysis types are processed and submitted**.

### 6.2. Manifest & Report Artifact Requirements

- **job_metadata.json:** Full input contract, all mapped values, analysis types, batch config.
- **manifest.json:** Nested status by image, analysis, task, QA tier, result file paths, retry count, audit trail.
- **Batch reports (all required):**
  - `batch_summary_report.md` (human readable)
  - `performance_metrics.json`
  - `quality_analysis.json`
  - `scaling_projections.json`

## Section 7. Fault Tolerance, Audit, & Recovery

- **Microsecond-precision checkpointing**: after key phases and every batch step.
- Auto-resume using precise manifest state.
- No manual intervention required for half-completed batches.
- **Audit trail**: Every manifest/edit/change, error and retry is logged with full context.

## Section 8. Detailed Feature & Function Compliance Table

| Feature Area                       | Expanded Detail                                                                                                     | PRD Compliance        |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------|----------------------|
| YAML-Only Config                    | Dynamic, editable; strictly no business logic or validation hardcoded in code; all 21 types in config              | **MANDATORY**        |
| Enum-Based Type Safety              | Compile-time analysis type checking, full API slug ↔ YAML filename ↔ enum mapping, extensible                      | **MANDATORY**        |
| Model Registry                      | Only models in centralized YAML registry; no code-side model refs for types                                         | **MANDATORY**        |
| Hotswappable, Zero-Downtime Config  | Any YAML/config/model update takes effect at runtime, no code reload needed                                         | **MANDATORY**        |
| Job Manifest Generation             | PRD-aligned manifest; full status tracking down to individual image and tier                                        | **MANDATORY**        |
| Sequential Analysis & Parallelism   | Async concurrency at image level; sequential per-image analysis                                                     | **MANDATORY**        |
| Ollama Optimization                 | Flash Attention, q8_0 cache, parallelism=5, persistent loading set via env/scripts                                  | **MANDATORY**        |
| Three-Tier QA Pipeline              | OpenAI Agent SDK API callout; never bypassed; all outputs processed through T1, T2, T3                             | **MANDATORY**        |
| Meta-Descriptive Prevention         | 60+ patterns via YAML, semantic detection (not just pattern)                                                        | **MANDATORY**        |
| Correction Agent Logic              | T3 failures invoke correction agent; successful outputs must pass original schema/guidelines                        | **MANDATORY**        |
| Job-Specific Logging                | Structured, atomic, directory-based, per-task function logs, with correlation IDs                                   | **MANDATORY**        |
| Checkpoints & Recovery              | Precision checkpoint microfiles; auto-recovery flows                                                                | **MANDATORY**        |
| Structured Output Schema            | YAML-driven, dynamic Pydantic model autogen for validation and Instructor powered parsing                           | **MANDATORY**        |
| Batch Report Generation             | 4 mandatory artifacts, auto-written in output dir for every batch                                                   | **MANDATORY**        |

## Section 9. Analyst Review Procedure

**For each compliance point above, check that:**

- **All core config/enum/model logic is fully in config, not code.**
  - No business rule, prompt, constraint, or model assignment can be found hardcoded.
- **Dynamic discovery**: New analysis YAML file → automatically available as new type.
- **File and path layouts**: Follow `/output/{job_id}/` as required with subfolders, per PRD.
- **Logging and checkpointing**: Every action/result/failure timestamped, attributed to job/UUID/image/type/task/tier.
- **QA pipeline**: Unbroken T1-T2-T3 flow with manifest and retry tracking.
- **Zero meta-descriptive**: Every result must be proved clean via both regex and semantic QA; samples checked for compliance.
- **Job manifests and batch reports match samples in PRD (fields, structure, nesting).**
- **Runtime config edits**: Live YAML edit (e.g. update prohibited phrase) → immediately seen in new/time QA checks.

## Section 10. Mandatory File/Datastructure Inventory

**All files and data structures required per batch:**

- `/output/{job_id}/job_metadata.json`
- `/output/{job_id}/manifest.json`
- `/output/{job_id}/images/color/` and `/bw/`
- `/output/{job_id}/analysis/{analysis_type}/result_{timestamp}.json`
- `/output/{job_id}/logs/processing.log`, `qa_validation.log`, `errors.log`, `performance.log`
- `/output/{job_id}/reports/batch_summary_report.md`
- `/output/{job_id}/reports/performance_metrics.json`
- `/output/{job_id}/reports/quality_analysis.json`
- `/output/{job_id}/reports/scaling_projections.json`
- `/output/{job_id}/checkpoints/{manifest_checkpoint}.{ts}.json`

## Section 11. Special Edge and Error Cases

- **System halts** if *any* critical YAML config is missing or invalid—no partial runs allowed.
- **Circuit breaker logic**: If QA validation failures cross threshold, run aborts and logs detail (for further diagnosis).
- **Fallbacks invoked** on timeout or uncaught exception—must always yield valid schema-compliant fallback result.  
- **API key and endpoint** config is loaded from secure environment, never embedded or hardcoded.

## Section 12. End-to-End Validation Example (Walkthrough)

1. **New YAML analysis uploaded** → appears as new enum variant, in config scan, available for use, schema validated, no code edited.
2. **Config edit for prohibited language** → next run, validation in both regex and AI semantic search, instantly enforced.
3. **Manifest.json** → tracks each image and each requested analysis type with status for analysis, all QA tiers, submission status, paths to results, retry count, error messages.
4. **Failed QA** → triggers correction loop, with cause/effect logged, and pass/fail outcome attributed explicitly.
5. **Resumption after crash** → system loads last checkpoint, recovers to precise last known good state, resumes from incomplete image/analysis pairs only.

**This document must be used by code reviewers as an exhaustive, non-negotiable checklist for launch-readiness. Failure in any single area is a launch-blocking defect.**
