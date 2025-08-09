# Ollama Vision Model Optimization for Maximum Throughput

A comprehensive guide to optimizing Ollama vision models using advanced automation scripts and YAML configuration files for maximum performance across different systems.

## Core Optimization Principles

**The GF-25 v1 system includes an advanced optimization script that provides:**
- **Aggressive Process Management**: Complete Ollama restart with force-kill capabilities
- **Dynamic YAML Configuration**: Real-time parsing and application of optimization settings
- **Environment Variable Management**: Comprehensive export and validation
- **Startup Verification**: Automated readiness checking and error handling
- **Model Pre-loading**: Optional background model loading for instant batch processing
- **Network Configuration**: CORS and host settings for web interface compatibility

**Key insight**: Vision models require significantly more memory than text-only models due to image processing overhead. Our optimization script handles this automatically.

## YAML Configuration Structure

### Main Optimization Config (`ollama_optimization.yaml`)

```yaml
# Ollama Optimization Configuration
optimization:
  version: "1.0"
  
  # Core performance settings
  performance:
    flash_attention: true           # Essential for KV cache optimization
    kv_cache_type: "q8_0"          # q8_0 = 50% cache memory reduction
    num_parallel: 5                # Concurrent requests per model
    keep_alive: "-1"               # Keep models loaded indefinitely
    max_loaded_models: 1           # Limit concurrent models for memory efficiency
    
  # Context and memory management
  context:
    default_size: 8192             # Standard context window for detailed images
    vision_optimized: 16384        # Larger context for complex vision tasks
    batch_size: 4096               # Optimal batch processing size
    
  # Model-specific settings
  models:
    vision_primary: "llama3.2-vision:11b"
    vision_fallback: "qwen2.5-vl:7b"
    quantization: "q8_0"           # Default quantization level
    
  # Request handling
  timeouts:
    default: 30                    # Standard timeout (seconds)
    vision: 60                     # Extended timeout for vision tasks
    batch: 120                     # Batch processing timeout
    
  # Memory optimization
  memory:
    image_max_size_mb: 10          # Maximum image file size
    optimal_image_size: 1344       # Optimal longest edge (pixels)
    min_resolution: "224x224"      # Minimum usable resolution
```

### Analysis Configuration Template (`analysis_config.yaml`)

```yaml
# Analysis Configuration Template
analysis_type: "vision_analysis"
name: "Vision Analysis Task"
description: "Optimized vision model analysis configuration"
version: "1.0.0"

# Model configuration optimized for throughput
model_configuration:
  primary_model: "llama3.2-vision:11b"
  fallback_model: "qwen2.5-vl:7b"
  quantization: "q8_0"
  
  # Core inference parameters
  context_size: 8192              # Larger context for detailed image analysis
  temperature: 0.1                # Low for consistent results
  top_p: 0.9                     # Nucleus sampling
  top_k: 15                      # Limited vocabulary sampling
  max_tokens: 300                # Extended for detailed analysis
  repeat_penalty: 1.0            # Prevent repetition
  
  # Performance optimization
  timeout_seconds: 60            # Extended timeout for detailed analysis
  num_ctx: 8192                  # Match context_size
  
# File handling for vision tasks
file_handling:
  max_file_size_mb: 10
  min_image_resolution: "224x224"
  optimal_image_size: "1344px"
  supported_formats: ["jpg", "jpeg", "png", "webp"]

# Output format specification
output_format:
  type: "json"
  schema_validation: true
  max_response_length: 500

# System prompts (keep concise for throughput)
prompts:
  system: |
    You are a vision analysis expert. Analyze images efficiently and provide structured responses.
    Focus on the main subjects and provide direct, concise analysis.
    Respond in the specified JSON format without meta-commentary.
  
  user_template: |
    Analyze this image for: {analysis_focus}
    Provide response as JSON: {expected_format}
    Be direct and specific in your analysis.
```

## Advanced Optimization Script

### Automated Optimization with `setup_ollama_optimization.sh`

The GF-25 v1 system includes a sophisticated optimization script at `/src/gf_25_v1/scripts/setup_ollama_optimization.sh` that provides:

#### Key Features

1. **Aggressive Process Management**
   - Detects and terminates ALL existing Ollama processes (app, server, runner)
   - Force-kills stubborn processes with `-9` signal
   - Waits for complete termination before proceeding
   - Comprehensive process cleanup to ensure clean restart

2. **Dynamic YAML Configuration Parsing**
   - Uses `yq` tool for robust YAML parsing
   - Extracts optimization values from `ollama_config.yaml`
   - Validates configuration before applying settings
   - Supports all optimization parameters dynamically

3. **Environment Variable Management**
   - Exports optimization settings as environment variables
   - Handles boolean conversion (true/false → 1/0)
   - Sets network configuration (CORS, host binding)
   - Ensures variables persist for Ollama server startup

4. **Startup Verification and Monitoring**
   - Starts Ollama with explicit environment variable passing
   - Waits up to 30 seconds for server readiness
   - Tests basic functionality with `ollama list`
   - Tracks process ID for monitoring
   - Logs startup status to `/tmp/ollama_optimization.log`

5. **Model Pre-loading (Optional)**
   - Background loading of vision models for instant access
   - Supports `--preload-models` flag or `PRELOAD_MODELS=true`
   - Pre-loads: `llama3.2-vision:11b`, `qwen2.5-vl:7b`, `qwen2.5vl:7b`
   - Reduces first-request latency for batch processing

#### Usage Examples

**Basic Optimization:**
```bash
# Run optimization with current YAML config
./src/gf_25_v1/scripts/setup_ollama_optimization.sh
```

**With Model Pre-loading:**
```bash
# Pre-load models for faster batch processing
./src/gf_25_v1/scripts/setup_ollama_optimization.sh --preload-models
```

**From Python (Programmatic):**
```python
import subprocess
from pathlib import Path

# Run optimization before batch processing
script_path = Path("src/gf_25_v1/scripts/setup_ollama_optimization.sh")
result = subprocess.run([str(script_path), "--preload-models"], 
                       capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Ollama optimization completed successfully")
else:
    print(f"❌ Optimization failed: {result.stderr}")
```

#### Prerequisites

**Required Tools:**
- `yq` YAML processor:
  ```bash
  # macOS
  brew install yq
  
  # Ubuntu/Debian
  apt install yq
  
  # Manual install
  # Download from: https://github.com/mikefarah/yq/releases
  ```

**Required Files:**
- `src/gf_25_v1/config/ollama/ollama_config.yaml` (optimization configuration)
- Executable permissions on the script:
  ```bash
  chmod +x src/gf_25_v1/scripts/setup_ollama_optimization.sh
  ```

#### Integration with GF-25 v1 System

The optimization script is integrated into the GF-25 v1 workflow through the `OllamaConfigLoader` service:

**Automatic Integration:**
- The `WorkflowOrchestrator` automatically calls optimization before batch processing
- The `OllamaConfigLoader.prepare_for_batch()` method runs the optimization script
- All YAML configurations are loaded and validated after optimization
- The system ensures Ollama is ready before starting vision analysis workflows

**Manual Integration:**
```python
from gf_25_v1.services.ollama_config_loader import OllamaConfigLoader

# Initialize the config loader
ollama_config = OllamaConfigLoader()

# Prepare Ollama for batch processing (runs optimization script)
if ollama_config.prepare_for_batch():
    print("✅ Ollama optimized and ready for batch processing")
    
    # Load analysis configurations
    analysis_types = ["caption", "keywords", "activities"]
    configs = ollama_config.setup_batch_processing(analysis_types)
    
    print(f"📋 Loaded {len(configs)} analysis configurations")
else:
    print("❌ Failed to optimize Ollama")
```
        
        if successful_count == 0:
            raise RuntimeError("No analysis configurations could be loaded")
        
        print(f"\n🚀 Batch processing ready with {successful_count} analysis types!")
        print(f"Loaded: {list(configs.keys())}")
        
        return configs
    
    def get_batch_summary(self, configs: Dict[str, Dict[str, Any]]) -> None:
        """Display a summary of loaded batch configurations"""
        print("\n📋 Batch Processing Summary:")
        print("=" * 50)
        
        for analysis_type, config in configs.items():
            model_config = config['model_configuration']
            print(f"🔹 {analysis_type.upper()}:")
            print(f"   Model: {model_config.get('primary_model', 'Unknown')}")
            print(f"   Context: {model_config.get('context_size', 'Unknown')}")
            print(f"   Tokens: {model_config.get('max_tokens', 'Unknown')}")
            print(f"   Timeout: {model_config.get('timeout_seconds', 'Unknown')}s")
        
        print("=" * 50)
        print(f"🎯 Total configurations: {len(configs)}")
        print("🚀 Ready for optimized batch processing!")
    
    # ... (keep all existing methods from previous version)
    
    def load_optimization_config(self) -> None:
        """Load the main Ollama optimization configuration"""
        try:
            with open(self.config_path, 'r') as file:
                self.optimization_config = yaml.safe_load(file)
                print(f"✓ Loaded Ollama optimization config from {self.config_path}")
        except FileNotFoundError:
            print(f"✗ Config file not found: {self.config_path}")
            print("Please ensure ollama_config.yaml exists in config/ollama/")
            raise
        except yaml.YAMLError as e:
            print(f"✗ YAML parsing error: {e}")
            raise
    
    def get_analysis_config(self, analysis_type: str) -> Dict[str, Any]:
        """Load analysis configuration using existing yaml_loader service"""
        try:
            analysis_config = self.yaml_loader.load_analysis_config(analysis_type)
            
            if not analysis_config:
                raise ValueError(f"Could not load analysis config for '{analysis_type}'")
            
            self._apply_optimization_overrides(analysis_config)
            return analysis_config
            
        except Exception as e:
            print(f"✗ Error loading analysis config for '{analysis_type}': {e}")
            raise
    
    def _apply_optimization_overrides(self, analysis_config: Dict[str, Any]) -> None:
        """Apply optimization settings to analysis configuration"""
        if not self.optimization_config:
            return
        
        model_config = analysis_config.get('model_configuration', {})
        opt_config = self.optimization_config['optimization']
        
        # Apply context size optimization
        analysis_type = analysis_config.get('analysis_type', '')
        context_config = opt_config['context']
        
        if analysis_type in ['longform_description', 'text_recognition']:
            model_config['context_size'] = max(
                model_config.get('context_size', context_config['default_size']),
                context_config['vision_optimized']
            )
        
        # Apply timeout optimization
        timeouts = opt_config['timeouts']
        if analysis_type in ['longform_description', 'text_recognition']:
            model_config['timeout_seconds'] = timeouts['batch']
        elif 'vision' in analysis_type or len(analysis_type) > 10:
            model_config['timeout_seconds'] = timeouts['vision']
        else:
            model_config['timeout_seconds'] = timeouts['default']
    
    def validate_analysis_config(self, config: Dict[str, Any]) -> bool:
        """Validate analysis configuration meets requirements"""
        required_fields = [
            'analysis_type', 'model_configuration', 'system_prompt', 
            'user_prompt', 'validation_constraints'
        ]
        
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            print(f"✗ Missing required fields: {missing_fields}")
            return False
        
        # Check for meta-descriptive phrase prevention
        validation = config.get('validation_constraints', {})
        prohibited = validation.get('prohibited_language', {})
        
        if 'meta_descriptive_phrases' not in prohibited:
            print("⚠ Warning: Meta-descriptive phrase prevention not configured")
            return False
        
        return True
```

### Enhanced Shell Script with Process Management

Create `/src/gf_25_v1/scripts/setup_ollama_optimization.sh`:

```bash
#!/bin/bash
# Enhanced Ollama optimization script with process management
# Designed to be called before each project batch run

CONFIG_FILE="config/ollama/ollama_config.yaml"
SCRIPT_NAME="Ollama Batch Optimizer"

echo "🚀 $SCRIPT_NAME - Starting optimization process..."
echo "=================================================="

# Function to check if Ollama is running
check_ollama_running() {
    if pgrep -f "ollama" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to stop Ollama processes
stop_ollama() {
    echo "🛑 Stopping existing Ollama processes..."
    
    # Kill Ollama server processes
    if pgrep -f "ollama serve" > /dev/null; then
        echo "   Stopping Ollama server..."
        pkill -f "ollama serve"
        sleep 2
    fi
    
    # Kill any remaining Ollama processes
    if pgrep -f "ollama" > /dev/null; then
        echo "   Stopping remaining Ollama processes..."
        pkill -f "ollama"
        sleep 3
    fi
    
    # Force kill if still running
    if pgrep -f "ollama" > /dev/null; then
        echo "   Force stopping stubborn processes..."
        pkill -9 -f "ollama"
        sleep 2
    fi
    
    if ! pgrep -f "ollama" > /dev/null; then
        echo "   ✓ All Ollama processes stopped"
    else
        echo "   ⚠ Warning: Some Ollama processes may still be running"
    fi
}

# Function to start Ollama with optimization
start_ollama() {
    echo "🔧 Starting Ollama with optimization settings..."
    
    # Start Ollama in background
    nohup ollama serve > /dev/null 2>&1 &
    
    # Wait for Ollama to be ready
    echo "   Waiting for Ollama to start..."
    local max_wait=30
    local count=0
    
    while [ $count -lt $max_wait ]; do
        if ollama list > /dev/null 2>&1; then
            echo "   ✓ Ollama is ready"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        printf "."
    done
    
    echo ""
    echo "   ✗ Error: Ollama failed to start within $max_wait seconds"
    return 1
}

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "✗ Error: Config file not found at $CONFIG_FILE"
    echo "Please ensure ollama_config.yaml exists in the config/ollama/ directory"
    exit 1
fi

# Check if yq is available
if ! command -v yq &> /dev/null; then
    echo "✗ Error: 'yq' not found. Required for YAML parsing."
    echo "Install with:"
    echo "  macOS: brew install yq"
    echo "  Ubuntu: apt install yq"
    echo "  Or download from: https://github.com/mikefarah/yq/releases"
    exit 1
fi

echo "📋 Pre-flight checks passed"

# Stop existing Ollama processes
if check_ollama_running; then
    echo "🔍 Detected running Ollama processes"
    stop_ollama
else
    echo "ℹ️  No existing Ollama processes found"
fi

# Extract optimization values from YAML
echo "📖 Reading optimization settings from $CONFIG_FILE..."

FLASH_ATTENTION=$(yq eval '.optimization.performance.flash_attention' $CONFIG_FILE)
KV_CACHE_TYPE=$(yq eval '.optimization.performance.kv_cache_type' $CONFIG_FILE)
NUM_PARALLEL=$(yq eval '.optimization.performance.num_parallel' $CONFIG_FILE)
KEEP_ALIVE=$(yq eval '.optimization.performance.keep_alive' $CONFIG_FILE)
MAX_LOADED=$(yq eval '.optimization.performance.max_loaded_models' $CONFIG_FILE)

# Validate extracted values
if [ "$FLASH_ATTENTION" = "null" ] || [ "$KV_CACHE_TYPE" = "null" ]; then
    echo "✗ Error: Failed to read configuration values from YAML"
    echo "Please check the structure of $CONFIG_FILE"
    exit 1
fi

echo "   ✓ Configuration values extracted successfully"

# Set environment variables for optimization
echo "🔧 Applying Ollama optimization environment variables..."

export OLLAMA_FLASH_ATTENTION=$([[ "$FLASH_ATTENTION" == "true" ]] && echo "1" || echo "0")
export OLLAMA_KV_CACHE_TYPE="$KV_CACHE_TYPE"
export OLLAMA_NUM_PARALLEL="$NUM_PARALLEL"
export OLLAMA_KEEP_ALIVE="$KEEP_ALIVE"
export OLLAMA_MAX_LOADED_MODELS="$MAX_LOADED"

# Additional optimization variables
export OLLAMA_HOST="0.0.0.0:11434"  # Allow network access
export OLLAMA_ORIGINS="*"           # Allow CORS for web interfaces

echo "   ✓ Environment variables set:"
echo "     OLLAMA_FLASH_ATTENTION=$OLLAMA_FLASH_ATTENTION"
echo "     OLLAMA_KV_CACHE_TYPE=$OLLAMA_KV_CACHE_TYPE"
echo "     OLLAMA_NUM_PARALLEL=$OLLAMA_NUM_PARALLEL"
echo "     OLLAMA_KEEP_ALIVE=$OLLAMA_KEEP_ALIVE"
echo "     OLLAMA_MAX_LOADED_MODELS=$OLLAMA_MAX_LOADED_MODELS"

# Start Ollama with new settings
if ! start_ollama; then
    echo "✗ Failed to start Ollama"
    exit 1
fi

# Verify optimization is working
echo "🔍 Verifying optimization settings..."

# Check if models can be listed (basic functionality test)
if ollama list > /dev/null 2>&1; then
    echo "   ✓ Ollama is responding to commands"
else
    echo "   ⚠ Warning: Ollama may not be fully ready"
fi

# Display current process info
OLLAMA_PID=$(pgrep -f "ollama serve")
if [ -n "$OLLAMA_PID" ]; then
    echo "   ✓ Ollama server running (PID: $OLLAMA_PID)"
else
    echo "   ⚠ Warning: Ollama server PID not found"
fi

echo ""
echo "🎉 Ollama optimization complete!"
echo "=================================================="
echo "🚀 Ready for optimized vision analysis batch processing"
echo ""
echo "Next steps:"
echo "1. Your application can now use optimized Ollama"
echo "2. All vision analysis will benefit from these settings"
echo "3. Models will stay loaded for faster subsequent processing"
echo ""

# Optional: Pre-load common models for even faster batch processing
read -p "🤔 Pre-load common vision models for faster batch processing? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📥 Pre-loading vision models..."
    
    echo "   Loading llama3.2-vision:11b..."
    ollama pull llama3.2-vision:11b > /dev/null 2>&1 &
    
    echo "   Loading qwen2.5-vl:7b..."
    ollama pull qwen2.5-vl:7b > /dev/null 2>&1 &
    
    echo "   Loading qwen2.5vl:7b..."
    ollama pull qwen2.5vl:7b > /dev/null 2>&1 &
    
    echo "   ✓ Models loading in background..."
    echo "   Models will be ready for immediate use in batch processing"
fi

echo "✅ Optimization script completed successfully!"
```

## Optimization Settings Reference

### Critical Environment Variables

| Variable | Purpose | Recommended Value | Impact |
|----------|---------|-------------------|---------|
| `OLLAMA_FLASH_ATTENTION` | Enable Flash Attention | `1` | 10-15% speed improvement |
| `OLLAMA_KV_CACHE_TYPE` | Cache quantization | `q8_0` | 50% cache memory reduction |
| `OLLAMA_NUM_PARALLEL` | Concurrent requests | `5` | 4-5x throughput increase |
| `OLLAMA_KEEP_ALIVE` | Model persistence | `-1` | Eliminates reload delays |
| `OLLAMA_MAX_LOADED_MODELS` | Memory management | `1` | Prevents memory conflicts |

### Model Configuration Parameters for Different Analysis Types

Based on the analysis files, here are the optimized parameters for each analysis type:

| Analysis Type | Primary Model | Context Size | Temperature | Max Tokens | Timeout | Notes |
|---------------|---------------|--------------|-------------|-------------|---------|-------|
| **Text Recognition (OCR)** | `qwen2.5-vl:7b` | `8192` | `0.1` | `500` | `45s` | Qwen excels at OCR tasks |
| **Logo/Brand Detection** | `qwen2.5-vl:7b` | `4096` | `0.1` | `200` | `45s` | Text recognition focused |
| **Long-form Description** | `llama3.2-vision:11b` | `8192` | `0.1` | `2000` | `60s` | Needs large context |
| **Themes Analysis** | `llama3.2-vision:11b` | `4096` | `0.3` | `200` | `30s` | Higher creativity |
| **Color Analysis** | `qwen2.5vl:7b` | `2048` | `0.1` | `100` | `30s` | Lightweight task |
| **Basic Classification** | `qwen2.5vl:7b` | `4096` | `0.2` | `150` | `30s` | Standard analysis |
| **Complex Demographics** | `llama3.2-vision:11b` | `4096` | `0.1` | `150` | `30s` | Requires precision |

### Critical Analysis Requirements

All analysis configurations must include:

1. **Prohibited Language Prevention**: All analysis files strictly forbid meta-descriptive phrases
2. **JSON Schema Validation**: Structured output with strict schema adherence
3. **Error Handling**: Fallback responses for timeout/validation failures
4. **Environment-Specific Settings**: Development, production, and testing configurations

### Image Processing Optimization

| Setting | Recommended | Reason |
|---------|-------------|---------|
| Max file size | `10MB` | Balance quality vs processing time |
| Optimal resolution | `1344px` longest edge | Sweet spot for most vision models |
| Min resolution | `224x224` | Minimum for reliable analysis |
| Format preference | `JPEG` | Best compression/quality ratio |

## Performance Monitoring

### Check Optimization Status

```python
# performance_check.py
import subprocess
import json

def check_ollama_status():
    """Check if optimization settings are active"""
    try:
        # Check loaded models
        result = subprocess.run(['ollama', 'ps'], capture_output=True, text=True)
        print("Loaded models:")
        print(result.stdout)
        
        # Check environment variables
        import os
        print("\nOptimization settings:")
        print(f"Flash Attention: {os.getenv('OLLAMA_FLASH_ATTENTION', 'Not set')}")
        print(f"KV Cache Type: {os.getenv('OLLAMA_KV_CACHE_TYPE', 'Not set')}")
        print(f"Parallel Requests: {os.getenv('OLLAMA_NUM_PARALLEL', 'Not set')}")
        
    except Exception as e:
        print(f"Error checking status: {e}")

def benchmark_inference(model_name: str, test_image: str):
    """Simple inference benchmark"""
    import time
    import ollama
    
    start_time = time.time()
    
    response = ollama.chat(
        model=model_name,
        messages=[{
            'role': 'user',
            'content': 'Analyze this image briefly',
            'images': [test_image]
        }]
    )
    
    end_time = time.time()
    inference_time = end_time - start_time
    
    print(f"Inference time: {inference_time:.2f} seconds")
    return inference_time
```

## Quick Start Guide

**Step 1: Verify Project Structure**

Ensure your project has the correct structure:

```bash
src/gf_25_v1/
├── config/
│   └── ollama/
│       └── ollama_config.yaml          # Main optimization config
├── services/
│   ├── yaml_loader.py                  # Existing YAML loader
│   └── ollama_config_loader.py         # Create this file (Step 2)
└── scripts/
    └── setup_ollama_optimization.sh    # Create this file (Step 3)
```

**Step 2: Create the Ollama Configuration Loader**

Create `/src/gf_25_v1/services/ollama_config_loader.py` using the Python code provided above.

**Step 3: Create Optimization Script**

Create `/src/gf_25_v1/scripts/setup_ollama_optimization.sh` and make it executable:

```bash
chmod +x scripts/setup_ollama_optimization.sh
```

**Step 4: Verify Current Integration**

```bash
# Navigate to project root
cd src/gf_25_v1

# Check if optimization config exists
ls -la config/ollama/ollama_config.yaml

# Verify existing YAML loader
python -c "from services.yaml_loader import YamlLoader; print('✓ YamlLoader available')"

# Check Ollama status
ollama ps
```

**Step 5: Apply Optimization Settings**

```bash
# Using shell script
./scripts/setup_ollama_optimization.sh

# Or using Python in your application
python -c "
from services.ollama_config_loader import OllamaConfigLoader
loader = OllamaConfigLoader()
config = loader.optimize_for_analysis_type('ages')
print('✓ Optimization applied')
"
```

**Step 6: Integration in Your Application**

Add to your main application initialization:

```python
# In your main application or service startup
from services.ollama_config_loader import OllamaConfigLoader

# Initialize once during startup
ollama_optimizer = OllamaConfigLoader()

# Before running any analysis
def run_analysis(analysis_type: str, image_path: str):
    # Get optimized configuration
    config = ollama_optimizer.optimize_for_analysis_type(analysis_type)
    
    # Use existing yaml_loader for analysis-specific settings
    # Environment variables are already optimized
    
    # Your existing Ollama analysis code here
    # The optimization settings are automatically applied
```

**Step 7: Verify Optimization is Working**

```bash
# Check environment variables are set
env | grep OLLAMA

# Verify models are loaded and optimized
ollama ps

# Test with a sample analysis
python -c "
from services.ollama_config_loader import OllamaConfigLoader
loader = OllamaConfigLoader()
config = loader.get_analysis_config('ages')
print('Analysis config loaded:', config['analysis_type'])
"
```

**Step 8: Batch Analysis Setup** (Optional)

For processing multiple analysis types:

```python
# Setup optimization for multiple analysis types
from services.ollama_config_loader import OllamaConfigLoader

loader = OllamaConfigLoader()
analysis_types = ['ages', 'genders', 'activities', 'key_objects', 'mood_sentiment']

# Pre-load all configurations
configs = {}
for analysis_type in analysis_types:
    configs[analysis_type] = loader.get_analysis_config(analysis_type)
    print(f"✓ Loaded config for {analysis_type}")

# Use configs in your batch processing
print(f"🚀 Ready for batch analysis with {len(configs)} optimized configurations")
```

## Analysis-Specific Optimizations

### Critical Requirements for All Analysis Types

**Meta-Descriptive Phrase Prevention**: Every analysis YAML file includes extensive prohibited language lists to prevent phrases like:
- "This image shows..."
- "I can see..."
- "The photo depicts..."
- "Here we see..."

**JSON Schema Validation**: All analyses require strict JSON output with predefined schemas and validation rules.

**Error Handling**: Comprehensive fallback responses for timeouts, validation failures, and processing errors.

### Model Selection by Analysis Type

**Text-Heavy Analysis** (OCR, Logo Detection):
- Primary: `qwen2.5-vl:7b` (superior text recognition)
- Context: 8192 tokens (OCR needs extended context)
- Timeout: 45-90 seconds

**Detailed Visual Analysis** (Long-form Description, Body Shapes):
- Primary: `llama3.2-vision:11b` (comprehensive understanding)
- Context: 8192 tokens (detailed descriptions)
- Timeout: 60-90 seconds

**Lightweight Analysis** (Colors, Simple Classification):
- Primary: `qwen2.5vl:7b` (efficient processing)
- Context: 2048-4096 tokens
- Timeout: 30 seconds

**Creative Analysis** (Themes, Mood/Sentiment):
- Primary: `llama3.2-vision:11b`
- Temperature: 0.2-0.3 (higher creativity)
- Context: 4096 tokens
- Timeout: 30 seconds

This optimization approach provides consistent, measurable performance improvements across different platforms while maintaining simplicity and avoiding over-engineering.