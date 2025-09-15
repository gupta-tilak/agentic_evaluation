# 🆓 Free Models Setup Guide for Agentic Evaluation Framework

This guide shows you how to test and use the Agentic Evaluation Framework with free model APIs instead of OpenAI.

## 🎯 Available Free Options

### 1. 🦙 Ollama (Recommended for Local Testing)
**Best for**: Local development and testing
**Cost**: Free
**Setup**: Easy

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull free models
ollama pull llama2:7b
ollama pull mistral:7b
ollama pull codellama:7b
ollama pull phi:3b
```

### 2. 🤗 Hugging Face (Free Tier)
**Best for**: Cloud-based testing
**Cost**: Free (with rate limits)
**Setup**: Medium

```bash
# Install transformers
pip install transformers torch

# Set up Hugging Face token (optional)
export HUGGINGFACE_HUB_TOKEN="your-token-here"
```

### 3. 🟢 Google Colab (Free Tier)
**Best for**: Jupyter notebook testing
**Cost**: Free (with usage limits)
**Setup**: Easy

```python
# In Google Colab
!pip install transformers torch
```

## 🚀 Quick Start Testing

### Option 1: Simple Component Testing (No External APIs)
```bash
# Test all framework components without any external dependencies
python test_agentic_simple.py
```

### Option 2: Mock LLM Testing
```bash
# Test with mock LLM responses
python test_agentic_with_free_models.py
```

### Option 3: Real Free Model Testing
```bash
# Test with actual free models (requires setup)
python test_agentic_with_free_models.py
```

## 🔧 Configuration Examples

### 1. Ollama Configuration
```python
from deepeval.agentic import AgenticEvaluator, EvaluationConfig

# Configure for Ollama
config = EvaluationConfig(
    max_agents=50,
    batch_size=10,
    max_concurrent=5,
    timeout_seconds=300
)

evaluator = AgenticEvaluator(config=config)

# Register agents with Ollama models
agent_ids = evaluator.register_agents_batch([
    {"name": "Llama2 Agent", "model_name": "llama2:7b", "domain": "general"},
    {"name": "Mistral Agent", "model_name": "mistral:7b", "domain": "qa"},
    {"name": "CodeLlama Agent", "model_name": "codellama:7b", "domain": "code_generation"},
])
```

### 2. Hugging Face Configuration
```python
from transformers import pipeline

# Create Hugging Face models
hf_models = {
    "distilgpt2": pipeline("text-generation", model="distilgpt2"),
    "microsoft_dialo": pipeline("text-generation", model="microsoft/DialoGPT-medium"),
    "gpt2": pipeline("text-generation", model="gpt2")
}

# Use with agentic framework
for model_name, model in hf_models.items():
    evaluator.register_agent(
        name=f"HF {model_name}",
        model_name=model_name,
        domain="general",
        metadata={"provider": "huggingface", "model": model_name}
    )
```

### 3. Google Colab Configuration
```python
# In Google Colab notebook
!pip install transformers torch

from transformers import pipeline

# Create models
models = {
    "flan_t5": pipeline("text2text-generation", model="google/flan-t5-base"),
    "flan_t5_large": pipeline("text2text-generation", model="google/flan-t5-large")
}

# Use with agentic framework
for model_name, model in models.items():
    evaluator.register_agent(
        name=f"Colab {model_name}",
        model_name=model_name,
        domain="general",
        metadata={"provider": "colab", "model": model_name}
    )
```

## 📊 Testing Workflow

### Step 1: Basic Component Testing
```bash
# Test all framework components
python test_agentic_simple.py
```

Expected output:
```
🚀 Agentic Evaluation Framework - Simple Testing
============================================================
✅ Basic Imports: PASSED
✅ Agent Registry: PASSED
✅ Evaluation Dimensions: PASSED
✅ Domain Support: PASSED
✅ Reporting System: PASSED
✅ Configuration: PASSED
✅ Demo Workflow: PASSED

🎯 Overall Result: 7/7 tests passed
🎉 All tests passed! The agentic evaluation framework is working correctly.
```

### Step 2: Mock LLM Testing
```bash
# Test with mock LLM responses
python test_agentic_with_free_models.py
```

### Step 3: Real Model Testing (Optional)
```bash
# Test with actual free models
# Requires Ollama or Hugging Face setup
python test_agentic_with_free_models.py
```

## 🛠️ Custom Model Integration

### Creating Custom Model Wrapper
```python
class CustomModelWrapper:
    def __init__(self, model_name, model_type="ollama"):
        self.model_name = model_name
        self.model_type = model_type
        self._setup_model()
    
    def _setup_model(self):
        if self.model_type == "ollama":
            import requests
            self.api_url = "http://localhost:11434/api/generate"
        elif self.model_type == "huggingface":
            from transformers import pipeline
            self.model = pipeline("text-generation", model=self.model_name)
    
    def generate(self, prompt: str) -> str:
        if self.model_type == "ollama":
            return self._generate_ollama(prompt)
        elif self.model_type == "huggingface":
            return self._generate_huggingface(prompt)
    
    def _generate_ollama(self, prompt: str) -> str:
        import requests
        response = requests.post(self.api_url, json={
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        })
        return response.json()["response"]
    
    def _generate_huggingface(self, prompt: str) -> str:
        result = self.model(prompt, max_length=100, num_return_sequences=1)
        return result[0]["generated_text"]

# Use with agentic framework
custom_model = CustomModelWrapper("llama2:7b", "ollama")
evaluator.register_agent(
    name="Custom Llama2",
    model_name="custom-llama2",
    domain="general",
    metadata={"custom_model": custom_model}
)
```

## 📈 Performance Comparison

| Model Type | Setup Time | Inference Speed | Quality | Cost |
|------------|------------|-----------------|---------|------|
| **Ollama (Local)** | 5-10 min | Fast | Good | Free |
| **Hugging Face** | 2-5 min | Medium | Good | Free |
| **Google Colab** | 1-2 min | Medium | Good | Free |
| **Mock LLM** | Instant | Instant | N/A | Free |

## 🔍 Troubleshooting

### Common Issues

1. **Ollama not responding**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama if not running
   ollama serve
   ```

2. **Hugging Face model download issues**
   ```bash
   # Clear cache and retry
   rm -rf ~/.cache/huggingface
   pip install --upgrade transformers
   ```

3. **Memory issues with large models**
   ```python
   # Use smaller models
   config = EvaluationConfig(
       max_concurrent=2,  # Reduce concurrency
       batch_size=1       # Reduce batch size
   )
   ```

### Performance Optimization

1. **For Ollama**:
   ```bash
   # Use GPU if available
   OLLAMA_GPU=1 ollama serve
   
   # Use quantized models for better performance
   ollama pull llama2:7b-q4_0
   ```

2. **For Hugging Face**:
   ```python
   # Use smaller models
   from transformers import pipeline
   model = pipeline("text-generation", model="distilgpt2")
   ```

## 📝 Example Test Results

### Mock Testing Results
```
🧪 Testing Mock LLM...
   Prompt: Evaluate instruction following
   Response: The agent follows instructions well with good completeness and accuracy.

   Prompt: Check for hallucination
   Response: The response shows minimal hallucination and sticks to provided context.

✅ Mock LLM testing successful
```

### Real Model Testing Results
```
🦙 Testing with Ollama (if available)
✅ Ollama is running with 4 models available
   📦 llama2:7b
   📦 mistral:7b
   📦 codellama:7b
   📦 phi:3b
```

## 🎯 Recommended Testing Strategy

1. **Start with Mock Testing**: Use `test_agentic_simple.py` to verify all components
2. **Add Mock LLM Testing**: Use `test_agentic_with_free_models.py` for LLM integration
3. **Set up Ollama**: For local testing with real models
4. **Configure Hugging Face**: For cloud-based testing
5. **Production Setup**: Configure real APIs for production use

## 🚀 Next Steps

1. **Run Simple Tests**: `python test_agentic_simple.py`
2. **Set up Ollama**: Follow the Ollama installation guide
3. **Test with Real Models**: Use the provided examples
4. **Customize for Your Use Case**: Modify configurations as needed
5. **Deploy for Production**: Set up production-ready model configurations

The framework is designed to work with any model provider, making it easy to test and deploy with free alternatives!
