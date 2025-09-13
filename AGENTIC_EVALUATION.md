# Agentic Evaluation Framework

A comprehensive framework for evaluating AI agents across multiple dimensions, designed to address the challenges of large-scale agent evaluation as outlined in the e6data hackathon problem statement.

## 🎯 Problem Statement Alignment

This framework directly addresses the **Agentic Evaluation Framework** requirements:

### ✅ Core Requirements Met
- **Accepts prompts, responses, and metadata for 100s of agents** ✅
- **Scores responses across 4 key dimensions** ✅
  - Instruction Following
  - Hallucination Detection  
  - Assumption Control
  - Coherence & Accuracy
- **Outputs interpretable performance reports** ✅
- **Supports batch processing of thousands of responses** ✅
- **Clear evaluation outputs (scores, leaderboards, reports)** ✅

### 🚀 Stretch Goals Achieved
- **Explainability**: Detailed reasoning for low scores ✅
- **Integration with LLMs for "AI judges"** ✅
- **Visualization of evaluation trends** ✅
- **Support for multiple domains** ✅
- **Robustness and scalability** ✅

## 🏗️ Architecture

```
deepeval/agentic/
├── __init__.py              # Main exports
├── types.py                 # Core data structures
├── agent_registry.py        # Agent management
├── dimensions.py            # Evaluation dimensions
├── evaluator.py             # Main evaluator class
├── batch_processor.py       # Large-scale processing
├── reporting.py             # Reports and visualizations
└── domains.py               # Domain-specific evaluation
```

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/confident-ai/deepeval.git
cd deepeval

# Install dependencies
pip install -e .
```

### Basic Usage

```python
from deepeval import AgenticEvaluator, EvaluationConfig, DomainType
from deepeval.test_case import LLMTestCase

# 1. Create evaluation configuration
config = EvaluationConfig(
    max_agents=100,
    batch_size=10,
    max_concurrent=50,
    include_explanations=True
)

# 2. Initialize evaluator
evaluator = AgenticEvaluator(config=config)

# 3. Register agents
agent_ids = evaluator.register_agents_batch([
    {"name": "GPT-4 Agent", "model_name": "gpt-4", "domain": "general"},
    {"name": "Claude Agent", "model_name": "claude-3", "domain": "qa"},
    # ... register 100+ agents
])

# 4. Create test cases
test_cases = [
    LLMTestCase(
        input="What is the capital of France?",
        actual_output="The capital of France is Paris.",
        expected_output="Paris is the capital of France.",
        context=["France is a country in Europe. Its capital city is Paris."]
    ),
    # ... more test cases
]

# 5. Run evaluation
evaluation_result = evaluator.evaluate_agents(
    test_cases=test_cases,
    async_mode=True,
    show_progress=True
)

# 6. Generate reports
leaderboard = evaluator.generate_leaderboard(evaluation_result)
explanation = evaluator.explain_performance(agent_ids[0], evaluation_result)

# 7. Export results
evaluator.export_results(evaluation_result, "results.json", "json")
evaluator.export_results(evaluation_result, "results.csv", "csv")
```

## 📊 Evaluation Dimensions

### 1. Instruction Following
- **Purpose**: Evaluates how well agents follow given instructions
- **Criteria**: Completeness, accuracy, format compliance, constraint adherence
- **Threshold**: 0.7 (configurable)

### 2. Hallucination Detection
- **Purpose**: Measures how well agents avoid generating false information
- **Criteria**: Factual accuracy, evidence-based responses, context adherence
- **Threshold**: 0.8 (configurable)

### 3. Assumption Control
- **Purpose**: Evaluates how well agents avoid unwarranted assumptions
- **Criteria**: Factual accuracy, uncertainty handling, evidence-based responses
- **Threshold**: 0.6 (configurable)

### 4. Coherence & Accuracy
- **Purpose**: Measures response quality and accuracy
- **Criteria**: Logical consistency, clarity, completeness, relevance
- **Threshold**: 0.7 (configurable)

## 🌐 Domain Support

The framework supports multiple domains with specialized evaluation:

- **General**: General-purpose evaluation
- **QA**: Question answering with accuracy and consistency focus
- **Summarization**: Text summarization with quality and retention metrics
- **Reasoning**: Logical reasoning and problem-solving evaluation
- **Conversation**: Conversational AI with empathy and context awareness
- **Code Generation**: Code quality and correctness evaluation

## 📈 Reporting & Visualization

### Leaderboards
```python
leaderboard = evaluator.generate_leaderboard(evaluation_result)
evaluator.print_leaderboard(leaderboard, limit=20)
```

### Performance Explanations
```python
explanation = evaluator.explain_performance(agent_id, evaluation_result)
evaluator.print_performance_explanation(explanation)
```

### Domain Analysis
```python
domain_analysis = evaluator.get_domain_analysis(evaluation_result)
```

### Performance Insights
```python
insights = evaluator.get_performance_insights(evaluation_result)
```

## 🔧 Configuration

### EvaluationConfig Options
```python
config = EvaluationConfig(
    max_agents=100,           # Maximum number of agents
    batch_size=10,            # Batch size for processing
    max_concurrent=50,        # Maximum concurrent evaluations
    timeout_seconds=300,      # Timeout per evaluation
    retry_attempts=3,         # Retry attempts for failed evaluations
    include_explanations=True, # Include detailed explanations
    strict_mode=False,        # Strict evaluation mode
    cache_results=True,       # Cache evaluation results
    domains=[DomainType.GENERAL], # Domains to evaluate
    custom_metrics=[]         # Custom evaluation metrics
)
```

## 📊 Batch Processing

### Async Processing (Recommended)
```python
# Process 100+ agents asynchronously
evaluation_result = evaluator.evaluate_agents(
    test_cases=test_cases,
    async_mode=True,
    show_progress=True
)
```

### Sync Processing
```python
# Process agents synchronously
evaluation_result = evaluator.evaluate_agents(
    test_cases=test_cases,
    async_mode=False
)
```

## 📁 Export Formats

### JSON Export
```python
evaluator.export_results(evaluation_result, "results.json", "json")
```

### CSV Export
```python
evaluator.export_results(evaluation_result, "results.csv", "csv")
```

### Agent Registry Export
```python
evaluator.export_agents("agents.json")
```

## 🎯 Use Cases

### 1. Model Comparison
Compare different LLM models across multiple dimensions:
```python
# Register different models
evaluator.register_agent("GPT-4", "gpt-4", "general")
evaluator.register_agent("Claude-3", "claude-3", "general")
evaluator.register_agent("Gemini", "gemini-pro", "general")

# Evaluate and compare
result = evaluator.evaluate_agents(test_cases)
comparison = evaluator.compare_agents(["GPT-4", "Claude-3"], result)
```

### 2. Domain-Specific Evaluation
Evaluate agents specialized for specific domains:
```python
# Register domain-specific agents
evaluator.register_agent("QA Expert", "gpt-4", "qa")
evaluator.register_agent("Code Gen", "claude-3", "code_generation")

# Evaluate by domain
qa_result = evaluator.evaluate_agents(test_cases, domain="qa")
```

### 3. Performance Monitoring
Track agent performance over time:
```python
# Run regular evaluations
result = evaluator.evaluate_agents(test_cases)
evaluator.export_results(result, f"evaluation_{datetime.now().isoformat()}.json")
```

## 🔍 Advanced Features

### Custom Dimensions
```python
from deepeval.agentic.dimensions import EvaluationDimension

class CustomDimension(EvaluationDimension):
    def evaluate(self, agent, test_case):
        # Custom evaluation logic
        pass

evaluator.add_custom_dimension(CustomDimension("Custom", 1.0, 0.7))
```

### Agent Registry Management
```python
# Get registry statistics
stats = evaluator.get_agent_registry_stats()

# Search agents
agents = evaluator.agent_registry.search_agents(
    name_pattern="GPT",
    domain=DomainType.GENERAL
)

# Export/Import registry
evaluator.export_agents("agents.json")
evaluator.import_agents("agents.json")
```

## 📊 Example Output

### Leaderboard
```
Agent Performance Leaderboard
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Rank┃ Agent Name           ┃ Overall Score┃ Percentile ┃ Status ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━┩
│   1 │ GPT-4 Agent          │        0.892 │      95.0% │ ✅ Pass│
│   2 │ Claude Agent         │        0.856 │      90.0% │ ✅ Pass│
│   3 │ Gemini Agent         │        0.823 │      85.0% │ ✅ Pass│
└──────┴──────────────────────┴───────────────┴─────────────┴────────┘
```

### Performance Explanation
```
Agent GPT-4 Agent
┌─────────────────────────────────────────────────────────────────┐
│ Overall Performance:                                           │
│ Agent 'GPT-4 Agent' achieved an overall score of 0.892        │
│ (excellent performance), placing it in the 95.0th percentile.  │
│ The agent passed the evaluation criteria.                      │
└─────────────────────────────────────────────────────────────────┘

Strengths
┌─────────────────────────────────────────────────────────────────┐
│ • Strong performance in Instruction Following (score: 0.923)   │
│ • Strong performance in Coherence & Accuracy (score: 0.901)    │
│ • Fast response time                                           │
│ • No evaluation errors                                         │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Getting Started

1. **Set up environment**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **Run the example**:
   ```bash
   python examples/agentic_evaluation_example.py
   ```

3. **Customize for your use case**:
   - Modify test cases
   - Add your agents
   - Adjust evaluation criteria
   - Configure reporting

## 🤝 Contributing

The agentic evaluation framework is designed to be extensible. You can:

- Add new evaluation dimensions
- Create domain-specific metrics
- Implement custom reporting formats
- Add new visualization types

## 📚 Documentation

For more detailed documentation, see:
- [API Reference](docs/api-reference.md)
- [Evaluation Dimensions](docs/evaluation-dimensions.md)
- [Domain Support](docs/domain-support.md)
- [Reporting Guide](docs/reporting-guide.md)

## 🎉 Hackathon Submission

This framework directly addresses the e6data hackathon requirements:

✅ **Scoring pipeline**: Hybrid rule-based and ML-based evaluation  
✅ **Batch processing**: Supports thousands of responses  
✅ **Clear outputs**: Comprehensive reports and leaderboards  
✅ **Documentation**: Complete methodology documentation  
✅ **Explainability**: Detailed performance explanations  
✅ **LLM integration**: Uses LLMs as "AI judges"  
✅ **Visualization**: Rich console output and export formats  
✅ **Multi-domain**: Support for various evaluation domains  
✅ **Robustness**: Error handling and retry mechanisms  
✅ **Scalability**: Async processing for large-scale evaluation  

The framework is production-ready and can be immediately used for evaluating AI agents at scale!
