---
trigger: model_decision
description: "GF-25 v3 Data Persistence & State Management"
globs: ["**/models/**/*.py", "**/database/**/*.py", "**/redis/**/*.py", "**/state/**/*.py"]
---

# GF-25 v3 Data Persistence Architecture

## Meta Rule
**CRITICAL**: State "[DATA-PERSIST]" when applying these rules.

## PostgreSQL State Management ([POSTGRES-STATE])

### **[STATE-SCHEMA]**: Comprehensive State Tracking
- **ALWAYS** implement process_states, task_states, qa_attempts, audit_logs tables per PRD Section 8
- **ALWAYS** use UUID primary keys for all process and task identification
- **ALWAYS** include JSONB fields for configuration snapshots and error details
- Pattern: `process_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)`

### **[AUDIT-TRAILS]**: Complete Processing History
- **ALWAYS** log every state transition with timestamp and correlation_id
- **ALWAYS** persist QA attempt details: stage, attempt_number, validation_result, failure_reasons
- **ALWAYS** maintain configuration snapshots for auditability
- Pattern: `audit_log = AuditLog(process_id=pid, event_type="qa_validation", event_data=data)`

### **[SQLALCHEMY-MODELS]**: ORM Implementation
- **ALWAYS** use SQLAlchemy async sessions with connection pooling
- **ALWAYS** implement database models matching PRD schema requirements
- **ALWAYS** configure pool_size=10, max_overflow=20 for concurrent processing
- Pattern: `async with AsyncSession(engine) as session: await session.commit()`

## Redis Queue Management ([REDIS-QUEUES])

### **[SPECIALIZED-QUEUES]**: 21 Analysis Type Queues
- **ALWAYS** create dedicated queues per analysis type: ages_analysis_queue, themes_analysis_queue
- **ALWAYS** implement corrective queues: structural_correction_queue, content_correction_queue, domain_correction_queue
- **ALWAYS** add management queues: manual_review_queue, priority_processing_queue, batch_completion_queue
- Pattern: `await redis_client.lpush(f"{analysis_type}_analysis_queue", task_json)`

### **[QUEUE-COORDINATION]**: Worker Distribution
- **ALWAYS** implement round_robin task distribution across 8 workers
- **ALWAYS** monitor queue depths and processing rates per queue type
- **ALWAYS** configure worker_timeout=300 seconds for complex analysis tasks
- Pattern: `queue_length = await redis_client.llen(queue_name)`

### **[PRIORITY-HANDLING]**: Multi-Level Task Prioritization
- **ALWAYS** implement priority levels: high, normal, low
- **ALWAYS** process priority_processing_queue before standard analysis queues
- **ALWAYS** configure max_queue_size=10000 per specialized queue
- Pattern: `if priority == "high": await redis_client.lpush("priority_processing_queue", task)`

## State Management Patterns ([STATE-PATTERNS])

### **[PROCESS-TRACKING]**: Job-Level State
- **ALWAYS** track total_tasks, completed_tasks, failed_tasks, manual_review_tasks per process
- **ALWAYS** calculate overall progress percentage and update in real-time
- **ALWAYS** maintain process status: initializing, processing, completed, failed
- Pattern: `process.progress = (completed_tasks / total_tasks) * 100`

### **[TASK-GRANULARITY]**: Individual Analysis State
- **ALWAYS** track task status: pending, processing, qa_validation, completed, failed, manual_review
- **ALWAYS** record processing_start, processing_end timestamps for performance analytics
- **ALWAYS** maintain qa_attempts counter and confidence_score per task
- Pattern: `task.status = TaskStatus.QA_VALIDATION; task.qa_attempts += 1`

### **[CHECKPOINT-RECOVERY]**: Fault Tolerance
- **ALWAYS** create checkpoints at major processing milestones
- **ALWAYS** enable resume from exact failure point using process and task state
- **ALWAYS** implement graceful recovery with state consistency validation
- Pattern: `checkpoint = await create_checkpoint(process_id, "analysis_complete")`

## Data Models & Validation ([DATA-MODELS])

### **[ANALYSIS-RESULTS]**: Structured Result Storage
- **ALWAYS** use Pydantic models for analysis result validation before persistence
- **ALWAYS** implement analysis-type specific models matching master_prompts.json schemas
- **ALWAYS** validate JSON structure and enumeration compliance before database storage
- Pattern: `class AgesAnalysisResult(BaseModel): ages: List[AgeGroup] = Field(min_items=1)`

### **[QA-VALIDATION-DATA]**: Quality Assurance Records
- **ALWAYS** persist validation results with detailed failure reasons as JSONB
- **ALWAYS** store corrective prompts used and agent confidence scores
- **ALWAYS** maintain complete QA attempt history for manual review escalation
- Pattern: `qa_attempt.failure_reasons = {"structural": ["missing_field"], "content": ["meta_language"]}`

### **[CONFIGURATION-SNAPSHOTS]**: Version Control
- **ALWAYS** snapshot YAML configurations per process for reproducibility
- **ALWAYS** store model parameters used: temperature, top_k, num_ctx values
- **ALWAYS** maintain prompt versions for audit and debugging purposes
- Pattern: `config_snapshot = {"analysis_config": analysis_yaml, "model_params": model_config}`

## Performance Optimization ([PERF-DATA])

### **[CONNECTION-POOLING]**: Database Performance
- **ALWAYS** configure async connection pools with appropriate sizing
- **ALWAYS** use prepared statements for frequent queries
- **ALWAYS** implement batch operations for bulk state updates
- Pattern: `engine = create_async_engine(url, pool_size=20, max_overflow=50)`

### **[REDIS-OPTIMIZATION]**: Queue Performance
- **ALWAYS** configure Redis connection pooling with max_connections=20
- **ALWAYS** implement pipeline operations for bulk queue operations
- **ALWAYS** use Redis clustering for high-availability if needed
- Pattern: `async with redis_client.pipeline() as pipe: await pipe.execute()`

### **[INDEXING-STRATEGY]**: Query Optimization
- **ALWAYS** create indexes on process_id, task_id, status, timestamp columns
- **ALWAYS** optimize JSONB queries with GIN indexes for error_details and event_data
- **ALWAYS** implement query performance monitoring and optimization
- Pattern: `CREATE INDEX idx_tasks_status ON task_states(status, processing_start)`

## Backup & Recovery ([BACKUP-RECOVERY])

### **[DATA-PROTECTION]**: Backup Strategy
- **ALWAYS** implement continuous WAL archiving for PostgreSQL
- **ALWAYS** configure daily full backups with 30-day retention
- **ALWAYS** enable point-in-time recovery for critical data restoration
- Pattern: `pg_basebackup -D backup_dir -Ft -z -P`

### **[REDIS-PERSISTENCE]**: Queue State Protection
- **ALWAYS** configure Redis persistence with both RDB and AOF
- **ALWAYS** implement queue state recovery for unprocessed tasks
- **ALWAYS** maintain queue snapshots for disaster recovery scenarios
- Pattern: `redis_config = {"save": "900 1", "appendonly": "yes"}`

## Monitoring & Analytics ([DATA-MONITOR])

### **[PERFORMANCE-METRICS]**: Processing Analytics
- **ALWAYS** track processing rates per analysis type and worker
- **ALWAYS** monitor queue depths and processing latencies
- **ALWAYS** calculate success rates for QA stages and corrective processing
- Pattern: `metrics.track_processing_rate(analysis_type, tasks_per_hour)`

### **[QUALITY-ANALYTICS]**: QA Performance Tracking
- **ALWAYS** analyze validation failure patterns by analysis type
- **ALWAYS** monitor corrective processing success rates per stage
- **ALWAYS** track manual review routing rates and reasons
- Pattern: `qa_metrics.failure_rate[analysis_type][qa_stage] = failures / total_attempts`

## Critical Constraints

### **NEVER** Rules
- **NEVER** skip state persistence for any processing stage
- **NEVER** allow data inconsistency between PostgreSQL and Redis
- **NEVER** store sensitive data without proper encryption
- **NEVER** ignore database transaction failures

### **ALWAYS** Rules
- **ALWAYS** maintain atomic operations for state transitions
- **ALWAYS** implement comprehensive error handling for database operations
- **ALWAYS** validate data models before persistence
- **ALWAYS** provide complete audit trails for compliance requirements

---
**Source**: PRD Section 8 - State Management & Database Architecture
**Character Count**: 3,967