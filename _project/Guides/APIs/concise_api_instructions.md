# GoFlow API Integration - Concise Instructions

## Overview
Integrate 4 GoFlow API endpoints into existing Python codebase to manage complete workflow from job setup to final reporting.

## Configuration
- **Base URL**: `https://goflow-backend.yellowsand-8784ae26.uksouth.azurecontainerapps.io`
- **API Key**: `dtJ9HEs59LEt1iEDRbH6BoKglCIuBJnmAvrO5XkRym3+RLtwGWTr/U+XwUw6DKsXsQZscn4OrXWPesVjCjmXQA==`
- **Header**: `X-API-Key: {api-key}` (required for all calls)

## Endpoint Integration

### 1. Job Setup
- **Method**: GET `/api/v1/agent/next-job`
- **Purpose**: Get job manifest and extract IDs
- **Implementation**: 
  - Extract `client.id`, `project.id`, `media[].id`, `analyses[].id`
  - Store project_id for use in all subsequent calls
  - Jobs typically have 10-20 media files × 15-25 analyses = 150-500 combinations
- **Response**: 200 (success), 404 (no jobs), 401 (auth error)

### 2. Project Status (2 calls per project)
- **Method**: PUT `/api/v1/agent/projects/{projectId}/status`
- **Purpose**: Report batch start and completion
- **Triggers**:
  - **Start**: First media begins processing → `{"status": "processing"}`
  - **Complete**: All media×analysis done → `{"status": "completed"}`
- **Response**: 200 (success), 404 (project not found), 401 (auth error)

### 3. Analysis Results (150-500 calls per project)
- **Method**: POST `/api/v1/agent/projects/{projectId}/media/{mediaId}/analysis/{analysisId}`
- **Purpose**: Report individual media×analysis completion
- **Trigger**: After each media file passes QA for specific analysis
- **Body**: Include `modelUsed`, `userPromptUsed`, `systemPromptUsed`, `status: "completed"`, `analysisResult`
- **Response**: 200/201 (success), 400 (duplicate), 422 (invalid data), 401/404 (auth/not found)

### 4. Final Report
- **Method**: PUT `/api/v1/agent/projects/{projectId}/reports`
- **Purpose**: Submit comprehensive project report
- **Trigger**: After ALL media×analysis combinations complete
- **Body**: Include `type: "quality_analysis"`, comprehensive `report` with summary and details
- **Response**: 201 (success), 404 (project not found), 401 (auth error)

## Implementation Requirements

**ID Management**:
- Store all UUIDs from endpoint 1 (project_id, media_ids, analysis_ids)
- Track completion of each media×analysis combination
- Only proceed to final steps when all combinations complete

**Error Handling**:
- Implement retry logic with exponential backoff (3-5 retries)
- Handle 404 on endpoint 1 as "no jobs available"
- Handle 400/422 as data errors (don't retry)
- Handle 429 rate limiting with backoff

**Integration Points**:
1. Call endpoint 1 at job start
2. Call endpoint 2 "processing" when first media starts
3. Call endpoint 3 after each media×analysis QA pass
4. Call endpoint 2 "completed" when all done
5. Call endpoint 4 with final report

**Critical Notes**:
- Endpoint 3 uses POST method
- No duplicate submissions allowed
- All identifiers are UUIDs
- Store API key as environment variable
- Follow existing codebase patterns for HTTP clients, logging, error handling