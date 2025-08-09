---
description: "GF-25 v3 API & GoFlow Integration Patterns"
globs: ["**/api/**/*.py", "**/routes/**/*.py", "**/integrations/**/*.py"]
activation: "always_on"
priority: "high"
version: "1.0"
---

# GF-25 v3 API & Integration Patterns

## Meta Rule
**CRITICAL**: State "[API-INT]" when applying these rules.

## FastAPI Application Architecture ([FASTAPI-ARCH])

### **[API-CONFIG]**: Centralized API Configuration
- **ALWAYS** load API settings from api_endpoints.yaml per PRD Section 4
- **ALWAYS** configure CORS, rate limiting, authentication via YAML
- **ALWAYS** implement hot-reload for API configuration changes
- Pattern: `app_config = load_yaml_config("api_endpoints.yaml")`

### **[ENDPOINT-STRUCTURE]**: Core API Endpoints
- **ALWAYS** implement /health for liveness checks
- **ALWAYS** implement /metrics for Prometheus monitoring
- **ALWAYS** implement /admin/config/reload for configuration updates
- Pattern: `@app.get("/health") async def health_check() -> HealthResponse`

## GoFlow Integration System ([GOFLOW-INT])

### **[JOB-ACQUISITION]**: GoFlow API Client
- **ALWAYS** use `GET /api/v1/agent/next-job` with X-API-Key authentication
- **ALWAYS** implement 10-second polling interval for job availability
- **ALWAYS** extract client, project, media, analysis data per PRD Section 8
- Pattern: `async with httpx.AsyncClient() as client: response = await client.get()`

### **[STATUS-MANAGEMENT]**: Job Lifecycle Updates
- **ALWAYS** update status via `PUT /api/v1/agent/projects/{projectId}/status`
- **ALWAYS** use statuses: "processing", "completed" per GoFlow requirements
- **ALWAYS** implement comprehensive error handling for API failures
- Pattern: `await goflow_client.update_project_status(project_id, "processing")`

### **[RESULT-SUBMISSION]**: Analysis Result Reporting
- **ALWAYS** submit per analysis: `POST /api/v1/agent/projects/{projectId}/media/{mediaId}/analysis/{analysisId}`
- **ALWAYS** include required fields: modelUsed, userPromptUsed, systemPromptUsed, status, analysisResult
- **ALWAYS** implement result validation before GoFlow submission
- Pattern: `result_payload = build_goflow_result(analysis_result, prompts_used)`

## Image Management Integration ([IMAGE-MGT])

### **[IMAGE-DOWNLOAD]**: Optimized Image Processing
- **ALWAYS** use optimised_path as primary, greyscale_path as fallback
- **ALWAYS** implement concurrent downloads with semaphore control (8 concurrent)
- **ALWAYS** cache images locally with 24-hour TTL per PRD Section 8
- Pattern: `async with download_semaphore: image_data = await download_image()`

### **[IMAGE-VALIDATION]**: Format & Size Validation
- **ALWAYS** validate formats: jpg, jpeg, png, webp
- **ALWAYS** enforce max 100MB file size, resolution 640x480 to 4096x4096
- **ALWAYS** implement auto-orientation and metadata preservation
- Pattern: `validate_image_constraints(image_data, supported_formats)`

## Discord Webhook Integration ([DISCORD-INT])

### **[MULTI-CHANNEL]**: Specialized Notifications
- **ALWAYS** use dedicated channels per PRD Section 8: batch_manifest, qa_structural, qa_content, qa_domain, batch_report
- **ALWAYS** include structured payloads with client_slug, project_slug, analysis metrics
- **ALWAYS** implement color coding: success=#00ff00, warning=#ffaa00, error=#ff0000
- Pattern: `await discord_notifier.send_webhook(channel_type, structured_payload)`

### **[NOTIFICATION-TRIGGERS]**: Event-Driven Alerts
- **ALWAYS** trigger on job_acquisition_complete, validation_failures, batch_completion
- **ALWAYS** include comprehensive metrics in batch reports
- **ALWAYS** implement retry logic with exponential backoff for webhook failures
- Pattern: `if event_type in webhook_triggers: await send_notification(event_data)`

## Authentication & Security ([AUTH-SEC])

### **[API-SECURITY]**: Request Authentication
- **ALWAYS** implement JWT token validation for admin endpoints
- **ALWAYS** use X-API-Key header for GoFlow API authentication
- **ALWAYS** configure rate limiting per endpoint type: 100/min for processing, 50/min for reports
- Pattern: `@app.middleware("http") async def auth_middleware(request, call_next)`

### **[CORS-CONFIG]**: Cross-Origin Configuration
- **ALWAYS** configure CORS via YAML with environment-specific origins
- **ALWAYS** allow credentials for authenticated requests
- **ALWAYS** restrict methods to ["GET", "POST", "PUT", "DELETE"] as needed
- Pattern: `app.add_middleware(CORSMiddleware, **cors_config)`

## Monitoring & Observability ([MONITOR-OBS])

### **[METRICS-EXPORT]**: Prometheus Integration
- **ALWAYS** expose /metrics endpoint with gf25_* prefixed metrics per PRD Section 5
- **ALWAYS** track job throughput, latency histograms, QA success rates
- **ALWAYS** monitor GPU utilization, queue depths, error rates
- Pattern: `JOBS_PROCESSED = Counter("gf25_jobs_processed_total", labelnames=("type",))`

### **[HEALTH-CHECKS]**: System Status Monitoring
- **ALWAYS** implement comprehensive health checks: API, worker, database, Redis, Ollama
- **ALWAYS** return detailed status with component health in /health endpoint
- **ALWAYS** implement readiness vs liveness check differentiation
- Pattern: `health_status = await check_all_services() return {"status": "ok", "services": health_status}`

## Request/Response Patterns ([REQ-RESP])

### **[PYDANTIC-MODELS]**: API Schema Validation
- **ALWAYS** use Pydantic models for all request/response validation
- **ALWAYS** include Field descriptions for API documentation
- **ALWAYS** implement nested models for complex GoFlow data structures
- Pattern: `class GoFlowJobResponse(BaseModel): client: ClientData, project: ProjectData`

### **[ERROR-RESPONSES]**: Standardized Error Format
- **ALWAYS** return structured error responses with detail, error_code, timestamp
- **ALWAYS** use appropriate HTTP status codes: 422 for validation, 503 for service unavailable
- **ALWAYS** include correlation IDs for error tracking and debugging
- Pattern: `raise HTTPException(status_code=422, detail={"error": "validation_failed"})`

## Performance Optimization ([PERF-OPT])

### **[ASYNC-PATTERNS]**: Concurrent Request Handling
- **ALWAYS** use async/await for all I/O operations
- **ALWAYS** implement connection pooling for external services
- **ALWAYS** use asyncio.gather() for parallel API calls
- Pattern: `async with httpx.AsyncClient() as client: results = await asyncio.gather(*tasks)`

### **[TIMEOUT-MANAGEMENT]**: Request Timeout Configuration
- **ALWAYS** set timeouts: 30s for GoFlow APIs, 60s for analysis processing, 10s for QA
- **ALWAYS** implement graceful degradation for timeout scenarios
- **ALWAYS** provide timeout configuration via YAML
- Pattern: `timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=1.0)`

## Critical Constraints

### **NEVER** Rules
- **NEVER** hardcode GoFlow API endpoints or authentication credentials
- **NEVER** skip image validation before processing
- **NEVER** ignore webhook delivery failures without retry
- **NEVER** expose internal service errors in API responses

### **ALWAYS** Rules
- **ALWAYS** validate all inputs with Pydantic models before processing
- **ALWAYS** implement comprehensive error handling for all external API calls
- **ALWAYS** use environment-specific configuration for all integrations
- **ALWAYS** maintain audit trails for all GoFlow API interactions

---
**Source**: PRD Section 8 - External Integrations & API Architecture
**Character Count**: 3,952