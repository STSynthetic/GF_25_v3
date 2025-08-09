# Master Prompts JSON Profile Documentation

## Overview

This JSON configuration file defines a comprehensive **multi-modal AI image analysis system** built specifically for **Qwen2.5VL vision-language models** running on **Ollama/LiteLLM infrastructure**. The system provides **15 specialized analysis capabilities** with advanced error recovery and quality assurance mechanisms.

## System Architecture

### Core Design Principles
- **Vision-Language Expertise**: Specialized prompts for Qwen2.5VL's multimodal capabilities
- **Production-Ready Reliability**: Three-tier error correction with progressive refinement
- **Parameter Optimization**: Fine-tuned sampling parameters for each analysis type
- **Schema Compliance**: Strict JSON output validation with automatic correction
- **Respectful AI**: Built-in safeguards for sensitive demographic analysis

### Error Recovery Framework
Each analysis capability includes a **sophisticated 3-tier correction system**:

1. **Structural Correction**: Fixes JSON schema violations and formatting errors
2. **Content Quality**: Removes prohibited language patterns and meta-descriptions
3. **Domain Expert**: Ensures accuracy and contextual appropriateness

## Analysis Capabilities Profile

| Capability | Primary Use Case | Complexity | Special Features |
|------------|------------------|------------|------------------|
| **Activities** | Action/behavior detection | Medium | Present participle focus |
| **Ages** | Demographic analysis | High | Respectful age ranges, privacy-aware |
| **Body Shapes** | Physical description | High | Body-positive terminology, professional |
| **Captions** | Content summarization | Medium | 30-250 character constraint |
| **Category** | Content classification | Low | 25 predefined categories |
| **Ethnicity** | Demographic analysis | High | Culturally sensitive, broad categories |
| **Genders** | Gender presentation | High | Inclusive terminology, respectful |
| **Key Objects** | Object detection | Medium | Hierarchical importance ranking |
| **Keywords** | SEO/searchability | Medium | 10-50 keyword extraction |
| **Locations** | Environment identification | Medium | Indoor/outdoor/context classification |
| **Logo/Brand** | Commercial recognition | Medium | Brand name + spatial positioning |
| **Longform Description** | Detailed narratives | High | 200-2000 character comprehensive |
| **Mood/Sentiment** | Emotional analysis | Medium | 15 predefined emotional states |
| **Predominant Color** | Color analysis | Low | 38 predefined color palette |
| **People Count** | Quantitative analysis | Low | Featured person focus |
| **Season** | Temporal context | Medium | Environmental evidence-based |
| **Setting** | Spatial context | Low | 3-tier classification system |
| **Text Recognition** | OCR capabilities | High | Multi-language, multi-format |
| **Themes** | Abstract analysis | High | 6 thematic categories |
| **Time of Day** | Temporal analysis | Medium | 9 time periods + lighting cues |
| **Title** | Content naming | Medium | 5-10 word constraint, SEO-friendly |

## Technical Specifications

### Model Configuration
- **Primary Model**: `qwen2.5vl:32b` (maximum capability)
- **Fallback Strategy**: Same model for consistency
- **Context Window**: 8192-16384 tokens (content-dependent)
- **Response Streaming**: Disabled for complete JSON responses

### Parameter Optimization Matrix

| Analysis Type | Temperature | Top-P | Top-K | Use Case |
|---------------|-------------|--------|--------|----------|
| **High Precision** (OCR, Counting) | 0.01-0.05 | 0.7-0.8 | 5-10 | Factual accuracy |
| **Standard Analysis** (Objects, Colors) | 0.1 | 0.9 | 20 | Balanced performance |
| **Creative Tasks** (Themes, Descriptions) | 0.2-0.3 | 0.9 | 30-40 | Nuanced interpretation |
| **Error Correction** | 0.01-0.1 | 0.7-0.8 | 5-20 | Precise fixes |

### Quality Assurance Features

#### Prohibited Language Prevention
- **Meta-descriptive phrases**: "This image shows", "I can see"
- **Uncertainty markers**: "seems to be", "possibly", "might be"
- **Self-referential language**: References to the image itself
- **Judgmental terminology**: Replaced with respectful alternatives

#### Schema Validation
- **Strict JSON formatting**: All responses validated against predefined schemas
- **Data type enforcement**: Arrays, strings, objects properly typed
- **Range validation**: Numeric and length constraints enforced
- **Enumeration compliance**: Only predefined values accepted

## Sensitive Content Handling

### Demographic Analysis Safeguards
- **Age Assessment**: Broad, respectful ranges (8 categories)
- **Ethnicity Recognition**: Inclusive, culturally sensitive terms
- **Gender Identification**: Non-binary inclusive options
- **Body Description**: Body-positive, professional terminology

### Privacy Protection
- **Featured Person Focus**: Analysis limited to main subjects
- **Respectful Classification**: Avoids invasive or inappropriate categorization
- **Professional Standards**: Maintains clinical, objective tone
- **Cultural Sensitivity**: Acknowledges limitations of visual assessment

## Integration Requirements

### Infrastructure Dependencies
- **Ollama Runtime**: Local LLM serving platform
- **Qwen2.5VL Model**: Vision-language model (32B parameter variant)
- **JSON Parser**: Robust parsing with error handling
- **Image Processing**: Base64 encoding capability

This configuration represents a **production-ready, ethically-designed AI system** optimized for comprehensive visual content analysis with built-in quality assurance and respectful handling of sensitive content.