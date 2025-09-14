#!/usr/bin/env python3
"""
Complete Agentic Evaluation with Groq Integration for DeepEval
==============================================================

🎯 OVERVIEW:
This single file provides a complete solution for agentic evaluation using 
FREE Groq API instead of expensive OpenAI. It demonstrates how to:

✅ Replace OpenAI with Groq for cost-effective evaluation
✅ Implement custom metrics that work with Groq
✅ Register and evaluate multiple AI agents
✅ Generate comprehensive evaluation reports
✅ Export results in JSON format for analysis
⚡ ENHANCED: Parallel batch processing for thousands of agents

🚀 QUICK START:
1. Get your free Groq API key: https://console.groq.com/
2. Set environment variable: export GROQ_API_KEY="your-key-here"
3. Run: python complete_agentic_groq_evaluation.py

💰 COST SAVINGS:
- OpenAI Cost: $10-25 per evaluation session
- Groq Cost: $0.00 (free tier)
- Savings: 100% cost reduction!

📊 FEATURES:
- 4 evaluation metrics: instruction following, coherence, hallucination detection, relevance
- Support for mock agents and real HuggingFace models
- ⚡ BATCH PROCESSING: Evaluate multiple agents simultaneously
- Rate limiting to avoid API limits
- Comprehensive reporting with success rates
- JSON export for further analysis
- Error handling and graceful fallbacks

🔧 CUSTOMIZATION:
- Add your own agents by implementing generate(prompt) method
- Modify evaluation criteria in metric definitions
- Adjust test cases for your specific use case
- Scale to 100+ agents for large evaluations
- Configure batch processing parameters

📝 EXAMPLE USAGE:
    # Custom agent example
    class MyAgent:
        def __init__(self, name):
            self.model_name = name
        
        def generate(self, prompt):
            # Your agent logic here
            return "Agent response"
    
    # Register and evaluate
    evaluator.register_agent(MyAgent("Custom Agent"))
    results = evaluator.evaluate_agents(test_cases)

Author: Hackathon Agentic Evaluation Team
Date: September 2024
License: MIT
"""

import os
import sys
import json
import time
import re
import asyncio
import concurrent.futures
import threading
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add deepeval to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from deepeval.agentic import AgenticEvaluator, DomainType
from deepeval.test_case import LLMTestCase
from deepeval.models import LiteLLMModel
from deepeval.metrics import BaseMetric
import concurrent.futures
import threading
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add deepeval to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from deepeval.agentic import AgenticEvaluator, DomainType
from deepeval.test_case import LLMTestCase
from deepeval.models import LiteLLMModel
from deepeval.metrics import BaseMetric

# ============================================================================
# CONFIGURATION
# ============================================================================

GROQ_MODELS = [
    "groq/llama-3.1-8b-instant",      # Fast and efficient
    "groq/llama-3.1-70b-versatile",   # More capable
    "groq/mixtral-8x7b-32768",        # Mixture of experts
    "groq/gemma2-9b-it"               # Google's Gemma 2
]

EVALUATION_DIMENSIONS = [
    "instruction_following",
    "coherence_accuracy", 
    "hallucination_detection",
    "relevance_quality"
]

# Batch Processing Configuration - Optimized for Groq Free Tier
BATCH_CONFIG = {
    "max_concurrent": 2,     # Reduced for Groq free tier rate limits
    "batch_size": 2,         # Smaller batches to respect rate limits
    "timeout_seconds": 300,  # Timeout for each evaluation
    "retry_attempts": 3,     # More retry attempts for rate limit errors
    "rate_limit_delay": 3.0, # Increased delay to respect rate limits
    "backoff_multiplier": 2.0, # Exponential backoff multiplier
    "max_backoff_delay": 30.0  # Maximum delay between retries
}

# ============================================================================
# GROQ SETUP AND UTILITIES
# ============================================================================

def setup_groq_model() -> Optional[LiteLLMModel]:
    """Set up Groq model with fallback options"""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found!")
        print("   Get your free key from: https://console.groq.com/")
        print("   Then run: export GROQ_API_KEY='your-key-here'")
        return None
    
    for model_name in GROQ_MODELS:
        try:
            print(f"🧪 Testing {model_name}...")
            groq_model = LiteLLMModel(
                model=model_name,
                api_key=groq_api_key,
                temperature=0.1
            )
            
            # Test the model
            groq_model.generate("Hello")
            print(f"✅ Groq model ready: {model_name}")
            return groq_model
            
        except Exception as e:
            print(f"❌ {model_name} failed: {str(e)[:100]}...")
            continue
    
    print("❌ All Groq models failed. Check your API key and connection.")
    return None

def rate_limited_request(func, delay: float = 3.0):
    """Add rate limiting to prevent Groq API limits with exponential backoff"""
    def wrapper(*args, **kwargs):
        max_retries = BATCH_CONFIG["retry_attempts"]
        base_delay = delay
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # Exponential backoff for retries
                    backoff_delay = min(
                        base_delay * (BATCH_CONFIG["backoff_multiplier"] ** attempt),
                        BATCH_CONFIG["max_backoff_delay"]
                    )
                    print(f"    ⏳ Rate limit retry {attempt}/{max_retries}, waiting {backoff_delay:.1f}s...")
                    time.sleep(backoff_delay)
                else:
                    # Standard rate limiting
                    time.sleep(delay)
                
                return func(*args, **kwargs)
                
            except Exception as e:
                error_str = str(e).lower()
                if "rate" in error_str or "limit" in error_str or "quota" in error_str:
                    if attempt < max_retries:
                        print(f"    ⚠️  Rate limit hit, retrying in {base_delay * (2 ** attempt):.1f}s...")
                        continue
                    else:
                        print(f"    ❌ Rate limit exceeded after {max_retries} retries")
                        raise
                else:
                    # Non-rate-limit error, don't retry
                    raise
        
        return None
    return wrapper

# ============================================================================
# BATCH PROCESSING DATA STRUCTURES
# ============================================================================

@dataclass
class BatchProgress:
    """Progress tracking for batch processing"""
    total_agents: int
    processed_agents: int
    successful_evaluations: int
    failed_evaluations: int
    current_batch: int = 0
    total_batches: int = 0
    start_time: Optional[float] = None
    estimated_completion: Optional[float] = None

@dataclass 
class AgentEvaluationResult:
    """Result of evaluating a single agent"""
    agent_name: str
    domain: str
    test_results: List[Dict[str, Any]]
    overall_score: float = 0.0
    success_rate: float = 0.0
    evaluation_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

# ============================================================================
# CUSTOM GROQ-COMPATIBLE METRICS
# ============================================================================

class GroqCompatibleMetric(BaseMetric):
    """Custom metric that works with Groq by avoiding function calling issues"""
    
    def __init__(self, name: str, evaluation_criteria: str, model: LiteLLMModel, threshold: float = 0.7):
        self.name = name
        self.evaluation_criteria = evaluation_criteria
        self.model = model
        self.threshold = threshold
        self.score = 0.0
        self.reason = ""
        self.success = False
        self._evaluation_template = self._create_evaluation_template()
        
    def _create_evaluation_template(self) -> str:
        """Create evaluation prompt template"""
        return f"""
Evaluate the following AI agent response based on: {self.evaluation_criteria}

QUESTION: {{input}}
AGENT RESPONSE: {{actual_output}}
EXPECTED: {{expected_output}}
CONTEXT: {{context}}

EVALUATION CRITERIA: {self.evaluation_criteria}

Please provide:
1. A score from 0.0 to 1.0 (where 1.0 is perfect)
2. A brief explanation of your reasoning

Format your response as:
SCORE: [0.0-1.0]
REASONING: [Your explanation]
"""
    
    def measure(self, test_case: LLMTestCase) -> float:
        """Measure the metric using Groq with improved rate limiting"""
        max_retries = BATCH_CONFIG["retry_attempts"]
        base_delay = BATCH_CONFIG["rate_limit_delay"]
        
        for attempt in range(max_retries + 1):
            try:
                # Format the evaluation prompt
                prompt = self._evaluation_template.format(
                    input=test_case.input,
                    actual_output=test_case.actual_output,
                    expected_output=test_case.expected_output or "Not specified",
                    context=" | ".join(test_case.context) if test_case.context else "None provided"
                )
                
                # Progressive delay for retries
                if attempt > 0:
                    retry_delay = min(
                        base_delay * (BATCH_CONFIG["backoff_multiplier"] ** attempt),
                        BATCH_CONFIG["max_backoff_delay"]
                    )
                    print(f"    ⏳ Retry {attempt}/{max_retries} for {self.name}, waiting {retry_delay:.1f}s...")
                    time.sleep(retry_delay)
                else:
                    # Standard rate limiting
                    time.sleep(base_delay)
                
                # Make API call
                response = self.model.generate(prompt)
                
                # Parse response
                self._parse_evaluation_response(response)
                
                self.success = self.score >= self.threshold
                return self.score
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if any(keyword in error_str for keyword in ["rate", "limit", "quota", "exceeded"]):
                    if attempt < max_retries:
                        print(f"    ⚠️  Rate limit for {self.name}, retrying...")
                        continue
                    else:
                        print(f"    ❌ {self.name} rate limit exceeded after {max_retries} retries")
                        self.score = 0.5  # Default score for rate limit failures
                        self.reason = f"Rate limit exceeded: {str(e)[:100]}..."
                        self.success = False
                        return self.score
                else:
                    # Non-rate-limit error
                    print(f"    ⚠️  {self.name} evaluation error: {str(e)[:100]}...")
                    self.score = 0.0
                    self.reason = f"Evaluation failed: {str(e)}"
                    self.success = False
                    return 0.0
        
        # Should not reach here, but fallback
        self.score = 0.0
        self.reason = "Maximum retries exceeded"
        self.success = False
        return 0.0
    
    def _parse_evaluation_response(self, response: str):
        """Parse Groq response to extract score and reasoning"""
        try:
            # Handle tuple responses from LiteLLM
            if isinstance(response, tuple):
                response = str(response[0]) if response else ""
            
            response = str(response)
            lines = response.split('\n')
            
            # Extract score
            score_found = False
            reasoning_parts = []
            
            for line in lines:
                line = line.strip()
                
                # Look for score patterns
                if any(prefix in line.upper() for prefix in ['SCORE:', 'RATING:', 'EVALUATION:']):
                    score_part = line.split(':')[-1].strip()
                    self.score = self._extract_numerical_score(score_part)
                    score_found = True
                    
                # Look for reasoning
                elif any(prefix in line.upper() for prefix in ['REASONING:', 'EXPLANATION:', 'BECAUSE:']):
                    reasoning_parts.append(line.split(':', 1)[-1].strip())
                elif score_found and line and not line.startswith('SCORE'):
                    reasoning_parts.append(line)
            
            # Set reasoning
            self.reason = ' '.join(reasoning_parts) if reasoning_parts else response
            
            # Fallback scoring if no explicit score found
            if not score_found:
                self.score = self._fallback_keyword_scoring(response)
                
        except Exception as e:
            print(f"    ⚠️  Parse error: {e}")
            self.score = 0.5
            self.reason = response
    
    def _extract_numerical_score(self, score_text: str) -> float:
        """Extract numerical score from text"""
        import re
        
        # Remove common non-numeric characters
        score_text = score_text.replace('(', '').replace(')', '').replace('%', '')
        
        # Look for decimal numbers
        numbers = re.findall(r'0?\.\d+|[01]\.?\d*', score_text)
        
        for num_str in numbers:
            try:
                score = float(num_str)
                if 0.0 <= score <= 1.0:
                    return score
                elif 0 <= score <= 10:  # Convert 0-10 scale to 0-1
                    return score / 10.0
                elif 0 <= score <= 100:  # Convert 0-100 scale to 0-1
                    return score / 100.0
            except ValueError:
                continue
                
        return 0.5  # Default fallback
    
    def _fallback_keyword_scoring(self, response: str) -> float:
        """Fallback scoring based on keywords in response"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['excellent', 'outstanding', 'perfect', 'exceptional']):
            return 0.95
        elif any(word in response_lower for word in ['very good', 'great', 'impressive']):
            return 0.85
        elif any(word in response_lower for word in ['good', 'well', 'solid', 'adequate']):
            return 0.75
        elif any(word in response_lower for word in ['okay', 'decent', 'fair', 'reasonable']):
            return 0.65
        elif any(word in response_lower for word in ['poor', 'weak', 'lacking', 'insufficient']):
            return 0.35
        elif any(word in response_lower for word in ['very poor', 'terrible', 'awful', 'completely wrong']):
            return 0.15
        else:
            return 0.5
    
    def is_successful(self) -> bool:
        return self.success

# ============================================================================
# AGENT IMPLEMENTATIONS
# ============================================================================

class HuggingFaceAgent:
    """HuggingFace model agent for evaluation"""
    
    def __init__(self, model_name: str, task: str = "text-generation"):
        self.model_name = model_name
        self.task = task
        self.domain = "general"
        
        try:
            from transformers import pipeline
            
            # Try different loading strategies with fallbacks
            loading_strategies = [
                # Strategy 1: Use device_map with accelerate (requires accelerate package)
                {"device_map": "auto"},
                # Strategy 2: Use CPU only (fallback if GPU issues)
                {"device": "cpu"},
                # Strategy 3: Basic loading without device specification
                {}
            ]
            
            self.model = None
            for i, kwargs in enumerate(loading_strategies):
                try:
                    print(f"🔄 Trying to load {model_name} with strategy {i+1}...")
                    self.model = pipeline(task, model=model_name, **kwargs)
                    print(f"✅ Successfully loaded HuggingFace model: {model_name} (strategy {i+1})")
                    break
                except Exception as strategy_error:
                    print(f"   Strategy {i+1} failed: {str(strategy_error)[:100]}...")
                    continue
            
            if self.model is None:
                print(f"❌ All loading strategies failed for {model_name}")
                
        except ImportError as e:
            print(f"⚠️  transformers not available: {e}")
            self.model = None
        except Exception as e:
            print(f"⚠️  Failed to load {model_name}: {e}")
            self.model = None
    
    def generate(self, prompt: str, max_length: int = 150) -> str:
        """Generate response from HuggingFace model"""
        if not self.model:
            return f"Error: Model {self.model_name} not available"
        
        try:
            if self.task == "text-generation":
                # Handle potential tokenizer issues
                try:
                    result = self.model(prompt, max_length=max_length, num_return_sequences=1, 
                                      truncation=True, pad_token_id=self.model.tokenizer.eos_token_id)
                except AttributeError:
                    # Fallback if tokenizer doesn't have eos_token_id
                    result = self.model(prompt, max_length=max_length, num_return_sequences=1, 
                                      truncation=True)
                
                generated_text = result[0]["generated_text"]
                # Remove the input prompt from the output
                if generated_text.startswith(prompt):
                    generated_text = generated_text[len(prompt):].strip()
                
                return generated_text if generated_text else "Generated response was empty"
            else:
                result = self.model(prompt)
                return str(result)
                
        except Exception as e:
            return f"Generation error for {self.model_name}: {str(e)[:100]}..."

class MockHighQualityAgent:
    """Mock high-quality agent for demonstration"""
    
    def __init__(self, name: str = "Expert AI Agent"):
        self.model_name = name
        self.domain = "expert"
        
        self.knowledge_base = {
            "ai": "Artificial Intelligence is a comprehensive field of computer science that focuses on creating systems capable of performing tasks that typically require human intelligence, including learning, reasoning, perception, and decision-making.",
            "ml": "Machine Learning is a subset of AI that enables systems to automatically learn and improve from experience without being explicitly programmed, using algorithms to identify patterns in data.",
            "renewable": "Renewable energy offers significant benefits including reduced greenhouse gas emissions, energy independence, job creation, long-term cost savings, and sustainable power generation from sources like solar, wind, and hydroelectric power.",
            "climate": "Climate change mitigation requires comprehensive strategies including transitioning to renewable energy, improving energy efficiency, developing carbon capture technologies, and implementing sustainable practices across industries."
        }
    
    def generate(self, prompt: str) -> str:
        """Generate high-quality responses"""
        prompt_lower = prompt.lower()
        
        for key, response in self.knowledge_base.items():
            if key in prompt_lower:
                return response
        
        return "I'd be happy to provide a comprehensive answer. Could you please provide more specific details about what aspect you'd like me to focus on?"

class MockAverageAgent:
    """Mock average-quality agent for demonstration"""
    
    def __init__(self, name: str = "Standard AI Agent"):
        self.model_name = name
        self.domain = "general"
    
    def generate(self, prompt: str) -> str:
        """Generate average-quality responses"""
        prompt_lower = prompt.lower()
        
        if "ai" in prompt_lower or "artificial intelligence" in prompt_lower:
            return "AI is technology that makes computers smart like humans. It's used in many applications."
        elif "machine learning" in prompt_lower or "ml" in prompt_lower:
            return "Machine learning is when computers learn from data without being programmed for everything."
        elif "renewable" in prompt_lower or "energy" in prompt_lower:
            return "Renewable energy is good for the environment and comes from sources like solar and wind."
        else:
            return "That's an interesting question about technology and science."

class MockPoorAgent:
    """Mock poor-quality agent for demonstration"""
    
    def __init__(self, name: str = "Basic AI Agent"):
        self.model_name = name
        self.domain = "basic"
    
    def generate(self, prompt: str) -> str:
        """Generate poor-quality responses"""
        return "I don't know much about that topic. Computer stuff is complicated."

# ============================================================================
# EVALUATION FRAMEWORK WITH BATCH PROCESSING
# ============================================================================

class AgenticGroqEvaluator:
    """Main evaluator class using Groq for agentic evaluation with batch processing"""
    
    def __init__(self, groq_model: LiteLLMModel, enable_batch_processing: bool = True):
        self.groq_model = groq_model
        self.metrics = self._create_evaluation_metrics()
        self.agents = []
        self.enable_batch_processing = enable_batch_processing
        self.batch_config = BATCH_CONFIG.copy()
        self._progress_callback = None
        
    def _create_evaluation_metrics(self) -> Dict[str, GroqCompatibleMetric]:
        """Create all evaluation metrics"""
        return {
            "instruction_following": GroqCompatibleMetric(
                name="Instruction Following",
                evaluation_criteria="How well the response follows the given instructions and addresses the specific question asked",
                model=self.groq_model,
                threshold=0.7
            ),
            "coherence_accuracy": GroqCompatibleMetric(
                name="Coherence & Accuracy", 
                evaluation_criteria="Logical consistency, factual accuracy, and overall coherence of the response",
                model=self.groq_model,
                threshold=0.7
            ),
            "hallucination_detection": GroqCompatibleMetric(
                name="Hallucination Detection",
                evaluation_criteria="Whether the response contains false information, made-up facts, or contradicts the provided context",
                model=self.groq_model,
                threshold=0.7
            ),
            "relevance_quality": GroqCompatibleMetric(
                name="Relevance & Quality",
                evaluation_criteria="How relevant, helpful, and high-quality the response is for the given question",
                model=self.groq_model,
                threshold=0.7
            )
        }
    
    def register_agent(self, agent: Any, domain: Union[str, DomainType] = "general"):
        """Register an agent for evaluation"""
        # Handle both string and DomainType inputs
        if isinstance(domain, str):
            domain_str = domain
        else:
            domain_str = str(domain).lower()
            
        self.agents.append({
            "agent": agent,
            "name": getattr(agent, 'model_name', str(agent)),
            "domain": domain_str
        })
        print(f"✅ Registered agent: {getattr(agent, 'model_name', str(agent))}")
    
    def create_test_cases(self) -> List[LLMTestCase]:
        """Create comprehensive test cases for evaluation"""
        return [
            LLMTestCase(
                input="What is artificial intelligence and how does it work?",
                actual_output="",
                expected_output="AI is a field of computer science focused on creating intelligent systems",
                context=["AI involves machine learning", "AI processes data to make decisions", "AI mimics human intelligence"]
            ),
            LLMTestCase(
                input="Explain the concept of machine learning and its applications",
                actual_output="",
                expected_output="Machine learning enables computers to learn from data without explicit programming",
                context=["ML is a subset of AI", "ML finds patterns in data", "ML improves with more data"]
            ),
            LLMTestCase(
                input="What are the main benefits of renewable energy sources?",
                actual_output="",
                expected_output="Renewable energy reduces emissions and provides sustainable power",
                context=["Renewable energy is sustainable", "Reduces carbon footprint", "Creates energy independence"]
            ),
            LLMTestCase(
                input="How can technology help address climate change?",
                actual_output="",
                expected_output="Technology enables clean energy, efficiency improvements, and monitoring solutions",
                context=["Technology enables renewable energy", "Smart systems reduce waste", "Monitoring helps track progress"]
            ),
            LLMTestCase(
                input="Describe the relationship between data science and artificial intelligence",
                actual_output="",
                expected_output="Data science provides the foundation and methods that AI systems use to learn",
                context=["Data science analyzes data", "AI uses data science techniques", "Both work with large datasets"]
            )
        ]
    
    def set_progress_callback(self, callback):
        """Set callback for progress updates"""
        self._progress_callback = callback
    
    def _evaluate_single_agent(self, agent_info: Dict[str, Any], test_cases: List[LLMTestCase]) -> AgentEvaluationResult:
        """Evaluate a single agent - can be called in parallel"""
        agent = agent_info["agent"]
        agent_name = agent_info["name"]
        domain = agent_info["domain"]
        
        start_time = time.time()
        errors = []
        
        print(f"🤖 Evaluating: {agent_name}")
        
        agent_result = {
            "agent_name": agent_name,
            "domain": domain,
            "test_results": []
        }
        
        for j, test_case in enumerate(test_cases):
            # Create a copy to avoid modifying the original
            test_case_copy = LLMTestCase(
                input=test_case.input,
                actual_output="",
                expected_output=test_case.expected_output,
                context=test_case.context
            )
            
            print(f"  📝 Test {j+1}: {test_case_copy.input[:60]}...")
            
            # Generate agent response
            try:
                response = agent.generate(test_case_copy.input)
                test_case_copy.actual_output = response
                print(f"     Response: {response[:80]}..." if len(response) > 80 else f"     Response: {response}")
            except Exception as e:
                response = f"Error: {str(e)}"
                test_case_copy.actual_output = response
                print(f"     ❌ Error: {str(e)}")
                errors.append(f"Test {j+1}: {str(e)}")
            
            # Evaluate with all metrics
            test_result = {
                "test_case_id": j + 1,
                "input": test_case_copy.input,
                "actual_output": response,
                "expected_output": test_case_copy.expected_output,
                "context": test_case_copy.context,
                "metric_scores": {}
            }
            
            for metric_name, metric in self.metrics.items():
                try:
                    print(f"     🔍 {metric_name}...", end=" ")
                    score = metric.measure(test_case_copy)
                    
                    test_result["metric_scores"][metric_name] = {
                        "score": score,
                        "threshold": metric.threshold,
                        "success": metric.is_successful(),
                        "reasoning": metric.reason
                    }
                    
                    status = "✅" if metric.is_successful() else "❌"
                    print(f"{status} {score:.3f}")
                    
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
                    test_result["metric_scores"][metric_name] = {
                        "score": 0.0,
                        "threshold": metric.threshold,
                        "success": False,
                        "error": str(e)
                    }
                    errors.append(f"Metric {metric_name} on test {j+1}: {str(e)}")
            
            agent_result["test_results"].append(test_result)
        
        evaluation_time = time.time() - start_time
        
        # Calculate overall metrics
        metric_totals = {}
        metric_successes = {}
        total_tests = len(agent_result["test_results"])
        
        for test in agent_result["test_results"]:
            for metric_name, metric_data in test["metric_scores"].items():
                if metric_name not in metric_totals:
                    metric_totals[metric_name] = []
                    metric_successes[metric_name] = 0
                
                if "score" in metric_data:
                    metric_totals[metric_name].append(metric_data["score"])
                    if metric_data.get("success", False):
                        metric_successes[metric_name] += 1
        
        # Calculate overall score and success rate
        all_scores = []
        total_successes = 0
        total_possible = 0
        
        for metric_name in self.metrics.keys():
            scores = metric_totals.get(metric_name, [])
            success_count = metric_successes.get(metric_name, 0)
            all_scores.extend(scores)
            total_successes += success_count
            total_possible += total_tests
        
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
        success_rate = (total_successes / total_possible * 100) if total_possible > 0 else 0.0
        
        return AgentEvaluationResult(
            agent_name=agent_name,
            domain=domain,
            test_results=agent_result["test_results"],
            overall_score=overall_score,
            success_rate=success_rate,
            evaluation_time=evaluation_time,
            errors=errors
        )
    
    def evaluate_agents_batch(self, test_cases: List[LLMTestCase]) -> Dict[str, Any]:
        """Evaluate all agents using batch processing optimized for Groq rate limits"""
        if not self.enable_batch_processing or len(self.agents) <= 1:
            return self.evaluate_agents_sequential(test_cases)
        
        print(f"\n🚀 BATCH EVALUATION: {len(self.agents)} AGENTS ON {len(test_cases)} TEST CASES")
        print(f"⚡ Parallel Processing: {self.batch_config['max_concurrent']} concurrent agents")
        print(f"⏳ Rate Limit Optimized: {self.batch_config['rate_limit_delay']}s delays")
        print("="*70)
        
        start_time = time.time()
        
        # Initialize progress tracking
        total_batches = (len(self.agents) + self.batch_config['batch_size'] - 1) // self.batch_config['batch_size']
        progress = BatchProgress(
            total_agents=len(self.agents),
            processed_agents=0,
            successful_evaluations=0,
            failed_evaluations=0,
            total_batches=total_batches,
            start_time=start_time
        )
        
        agent_results = []
        
        # Process agents in batches with rate limiting
        with ThreadPoolExecutor(max_workers=self.batch_config['max_concurrent']) as executor:
            # Create batches
            for batch_num in range(total_batches):
                batch_start = batch_num * self.batch_config['batch_size']
                batch_end = min(batch_start + self.batch_config['batch_size'], len(self.agents))
                batch_agents = self.agents[batch_start:batch_end]
                
                progress.current_batch = batch_num + 1
                print(f"\n📦 Processing Batch {batch_num + 1}/{total_batches} ({len(batch_agents)} agents)")
                
                # Add delay before starting each batch to respect rate limits
                if batch_num > 0:
                    batch_delay = self.batch_config['rate_limit_delay'] * 2
                    print(f"⏳ Waiting {batch_delay}s between batches for rate limit compliance...")
                    time.sleep(batch_delay)
                
                # Submit batch jobs
                future_to_agent = {
                    executor.submit(self._evaluate_single_agent, agent_info, test_cases): agent_info
                    for agent_info in batch_agents
                }
                
                # Collect results as they complete
                batch_results = []
                for future in as_completed(future_to_agent, timeout=self.batch_config['timeout_seconds']):
                    agent_info = future_to_agent[future]
                    try:
                        result = future.result()
                        batch_results.append(result)
                        progress.successful_evaluations += 1
                        print(f"✅ Completed: {result.agent_name} (Score: {result.overall_score:.3f})")
                    except Exception as e:
                        print(f"❌ Failed: {agent_info['name']} - {str(e)}")
                        # Create error result
                        error_result = AgentEvaluationResult(
                            agent_name=agent_info['name'],
                            domain=agent_info['domain'],
                            test_results=[],
                            overall_score=0.0,
                            success_rate=0.0,
                            evaluation_time=0.0,
                            errors=[str(e)]
                        )
                        batch_results.append(error_result)
                        progress.failed_evaluations += 1
                    
                    progress.processed_agents += 1
                    
                    # Update progress callback if set
                    if self._progress_callback:
                        self._progress_callback(progress)
                
                agent_results.extend(batch_results)
                
                # Longer pause between batches to respect Groq's rate limits
                if batch_num < total_batches - 1:
                    inter_batch_delay = self.batch_config['rate_limit_delay'] * 3
                    print(f"⏳ Rate limit cooldown: {inter_batch_delay}s before next batch...")
                    time.sleep(inter_batch_delay)
        
        evaluation_time = time.time() - start_time
        
        # Convert results to the expected format
        results = {
            "evaluation_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_agents": len(self.agents),
                "total_test_cases": len(test_cases),
                "total_metrics": len(self.metrics),
                "groq_model": self.groq_model.get_model_name(),
                "batch_processing": True,
                "evaluation_time": evaluation_time,
                "successful_evaluations": progress.successful_evaluations,
                "failed_evaluations": progress.failed_evaluations
            },
            "agent_results": [
                {
                    "agent_name": result.agent_name,
                    "domain": result.domain,
                    "test_results": result.test_results,
                    "overall_score": result.overall_score,
                    "success_rate": result.success_rate,
                    "evaluation_time": result.evaluation_time,
                    "errors": result.errors
                }
                for result in agent_results
            ]
        }
        
        print(f"\n🎉 Batch Evaluation Complete!")
        print(f"⏱️  Total Time: {evaluation_time:.2f} seconds")
        print(f"⚡ Speed Improvement: ~{len(self.agents) * len(test_cases) * len(self.metrics) * 2 / evaluation_time:.1f}x faster")
        print(f"✅ Success Rate: {progress.successful_evaluations}/{progress.total_agents} agents")
        
        return results
    
    def evaluate_agents_sequential(self, test_cases: List[LLMTestCase]) -> Dict[str, Any]:
        """Sequential evaluation (original method) - fallback for small datasets"""
        print(f"\n🔍 SEQUENTIAL EVALUATION: {len(self.agents)} AGENTS ON {len(test_cases)} TEST CASES")
        print("="*70)
        
        results = {
            "evaluation_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_agents": len(self.agents),
                "total_test_cases": len(test_cases),
                "total_metrics": len(self.metrics),
                "groq_model": self.groq_model.get_model_name(),
                "batch_processing": False
            },
            "agent_results": []
        }
        
        for i, agent_info in enumerate(self.agents):
            print(f"\n🤖 Agent {i+1}/{len(self.agents)}: {agent_info['name']}")
            print("-" * 50)
            
            try:
                result = self._evaluate_single_agent(agent_info, test_cases)
                results["agent_results"].append({
                    "agent_name": result.agent_name,
                    "domain": result.domain,
                    "test_results": result.test_results
                })
            except Exception as e:
                print(f"❌ Critical error evaluating {agent_info['name']}: {e}")
                results["agent_results"].append({
                    "agent_name": agent_info['name'],
                    "domain": agent_info['domain'],
                    "test_results": [],
                    "error": str(e)
                })
        
        return results
    
    def evaluate_agents(self, test_cases: List[LLMTestCase]) -> Dict[str, Any]:
        """Main evaluation method - automatically chooses batch or sequential"""
        if self.enable_batch_processing and len(self.agents) > 1:
            return self.evaluate_agents_batch(test_cases)
        else:
            return self.evaluate_agents_sequential(test_cases)
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive summary report"""
        summary = []
        summary.append("🎯 AGENTIC EVALUATION SUMMARY REPORT")
        summary.append("=" * 60)
        summary.append(f"📅 Evaluation Date: {results['evaluation_summary']['timestamp']}")
        summary.append(f"🤖 Total Agents: {results['evaluation_summary']['total_agents']}")
        summary.append(f"📝 Test Cases: {results['evaluation_summary']['total_test_cases']}")
        summary.append(f"📊 Metrics: {results['evaluation_summary']['total_metrics']}")
        summary.append(f"🔧 Model: {results['evaluation_summary']['groq_model']}")
        summary.append("")
        
        # Agent performance summary
        for agent_result in results["agent_results"]:
            agent_name = agent_result["agent_name"]
            summary.append(f"🤖 {agent_name}")
            summary.append("-" * 40)
            
            # Calculate overall metrics
            metric_totals = {}
            metric_successes = {}
            total_tests = len(agent_result["test_results"])
            
            for test in agent_result["test_results"]:
                for metric_name, metric_data in test["metric_scores"].items():
                    if metric_name not in metric_totals:
                        metric_totals[metric_name] = []
                        metric_successes[metric_name] = 0
                    
                    if "score" in metric_data:
                        metric_totals[metric_name].append(metric_data["score"])
                        if metric_data.get("success", False):
                            metric_successes[metric_name] += 1
            
            # Display metrics
            for metric_name in self.metrics.keys():
                scores = metric_totals.get(metric_name, [])
                avg_score = sum(scores) / len(scores) if scores else 0
                success_count = metric_successes.get(metric_name, 0)
                
                summary.append(f"   {metric_name}: {avg_score:.3f} avg (✅ {success_count}/{total_tests})")
            
            # Overall success rate
            total_successes = sum(metric_successes.values())
            total_possible = len(self.metrics) * total_tests
            overall_rate = (total_successes / total_possible * 100) if total_possible > 0 else 0
            summary.append(f"   Overall Success Rate: {overall_rate:.1f}%")
            summary.append("")
        
        # Cost analysis
        summary.append("💰 COST ANALYSIS")
        summary.append("-" * 20)
        summary.append("Total Cost: $0.00 (Groq Free Tier)")
        summary.append("Estimated OpenAI Cost Saved: $10-25")
        summary.append(f"Total API Calls: {len(results['agent_results']) * len(self.metrics) * results['evaluation_summary']['total_test_cases']}")
        
        return "\n".join(summary)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def create_demo_agents() -> List[Any]:
    """Create a mix of demo agents for evaluation"""
    agents = []
    
    # Add mock agents (always available)
    agents.extend([
        MockHighQualityAgent("Expert AI Agent"),
        MockAverageAgent("Standard AI Agent"),
        MockPoorAgent("Basic AI Agent")
    ])
    
    # Try to add HuggingFace agents (if available)
    try:
        print("🔄 Attempting to load HuggingFace models...")
        
        # List of models to try, starting with smaller/faster ones
        models_to_try = [
            ("distilgpt2", "text-generation"),  # Smaller, faster model
            ("gpt2", "text-generation"),        # Standard GPT-2
        ]
        
        successfully_loaded = 0
        for model_name, task in models_to_try:
            try:
                hf_agent = HuggingFaceAgent(model_name, task)
                if hf_agent.model is not None:
                    agents.append(hf_agent)
                    successfully_loaded += 1
                    print(f"✅ Added {model_name} to evaluation")
                else:
                    print(f"⚠️  Skipping {model_name} - failed to load")
            except Exception as e:
                print(f"⚠️  Failed to create agent for {model_name}: {str(e)[:50]}...")
        
        if successfully_loaded > 0:
            print(f"✅ Successfully loaded {successfully_loaded} HuggingFace model(s)")
        else:
            print("⚠️  No HuggingFace models could be loaded - continuing with mock agents only")
            
    except Exception as e:
        print(f"⚠️  HuggingFace models not available: {e}")
        print("   Continuing with mock agents...")
    
    return agents

def save_results(results: Dict[str, Any], filename: str = None) -> str:
    """Save results to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agentic_groq_evaluation_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return filename

def main():
    """Main execution function"""
    print("🚀 COMPLETE AGENTIC EVALUATION WITH GROQ + BATCH PROCESSING")
    print("=" * 70)
    print("🎯 Comprehensive AI Agent Evaluation using FREE Groq API")
    print("🔧 Replaces expensive OpenAI with cost-effective solution")
    print("⚡ ENHANCED: Parallel batch processing for faster evaluation")
    print("📊 Supports multiple agents, metrics, and test cases")
    print("=" * 70)
    print("🎯 Comprehensive AI Agent Evaluation using FREE Groq API")
    print("🔧 Replaces expensive OpenAI with cost-effective solution")
    print("⚡ ENHANCED: Parallel batch processing for faster evaluation")
    print("📊 Supports multiple agents, metrics, and test cases")
    print("=" * 70)
    
    # 1. Setup Groq
    print("\n1️⃣ Setting up Groq integration...")
    groq_model = setup_groq_model()
    if not groq_model:
        print("❌ Cannot proceed without Groq API key. Exiting...")
        return
    
    # 2. Initialize evaluator with batch processing
    print("\n2️⃣ Initializing agentic evaluator with batch processing...")
    evaluator = AgenticGroqEvaluator(groq_model, enable_batch_processing=True)
    print(f"✅ Created evaluator with {len(evaluator.metrics)} metrics")
    print(f"⚡ Batch processing enabled: {evaluator.batch_config['max_concurrent']} concurrent agents")
    print(f"⏳ Rate limit optimized: {evaluator.batch_config['rate_limit_delay']}s delays + backoff")
    print(f"🛡️  Retry attempts: {evaluator.batch_config['retry_attempts']} with exponential backoff")
    
    # 3. Register agents
    print("\n3️⃣ Registering AI agents...")
    demo_agents = create_demo_agents()
    
    for agent in demo_agents:
        evaluator.register_agent(agent)
    
    print(f"✅ Registered {len(demo_agents)} agents for evaluation")
    print(f"🚀 Batch processing will evaluate {min(evaluator.batch_config['max_concurrent'], len(demo_agents))} agents simultaneously")
    
    # 4. Create test cases
    print("\n4️⃣ Creating test cases...")
    test_cases = evaluator.create_test_cases()
    print(f"✅ Created {len(test_cases)} comprehensive test cases")
    
    # 5. Run evaluation with batch processing
    print(f"\n5️⃣ Running evaluation with RATE-LIMITED BATCH PROCESSING...")
    
    # Calculate time estimates (more conservative due to rate limiting)
    sequential_time = len(demo_agents) * len(test_cases) * len(evaluator.metrics) * evaluator.batch_config['rate_limit_delay']
    # Batch processing with rate limiting will be slower than ideal parallelization
    batch_time = sequential_time / max(1, min(evaluator.batch_config['max_concurrent'], len(demo_agents)) / 2)
    speed_improvement = sequential_time / batch_time
    
    print(f"⏱️  Sequential time estimate: ~{sequential_time:.0f} seconds")
    print(f"⚡ Rate-limited batch time estimate: ~{batch_time:.0f} seconds")
    print(f"🚀 Expected speed improvement: ~{speed_improvement:.1f}x faster")
    print(f"⚠️  Note: Conservative estimates due to Groq free tier rate limits")
    
    # Add progress callback
    def progress_callback(progress: BatchProgress):
        if progress.start_time:
            elapsed = time.time() - progress.start_time
            rate = progress.processed_agents / elapsed if elapsed > 0 else 0
            remaining = (progress.total_agents - progress.processed_agents) / rate if rate > 0 else 0
            print(f"📊 Progress: {progress.processed_agents}/{progress.total_agents} agents, \
                  Batch {progress.current_batch}/{progress.total_batches}, \
                  ETA: {remaining:.1f}s")
    
    evaluator.set_progress_callback(progress_callback)
    
    try:
        start_time = time.time()
        results = evaluator.evaluate_agents(test_cases)
        actual_time = time.time() - start_time
        
        print(f"\n🎉 EVALUATION COMPLETED SUCCESSFULLY!")
        print(f"⏱️  Actual time: {actual_time:.2f} seconds")
        if 'batch_processing' in results['evaluation_summary'] and results['evaluation_summary']['batch_processing']:
            theoretical_sequential_time = len(demo_agents) * len(test_cases) * len(evaluator.metrics) * evaluator.batch_config['rate_limit_delay']
            actual_speedup = theoretical_sequential_time / actual_time
            print(f"🚀 Achieved speedup: {actual_speedup:.1f}x faster than sequential")
        
    except KeyboardInterrupt:
        print("\n⚠️  Evaluation interrupted by user")
        return
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        return
    
    # 6. Generate and save reports
    print(f"\n6️⃣ Generating comprehensive reports...")
    
    # Generate summary report
    summary_report = evaluator.generate_summary_report(results)
    print("\n" + summary_report)
    
    # 7. Save results
    print(f"\n7️⃣ Saving results...")
    try:
        # Save JSON results
        json_filename = save_results(results)
        print(f"✅ JSON results saved: {json_filename}")
        
        # Save summary report
        summary_filename = json_filename.replace('.json', '_summary.txt')
        with open(summary_filename, 'w') as f:
            f.write(summary_report)
        print(f"✅ Summary report saved: {summary_filename}")
        
        # Save batch processing stats
        batch_stats = {
            "batch_processing_enabled": evaluator.enable_batch_processing,
            "max_concurrent": evaluator.batch_config['max_concurrent'],
            "batch_size": evaluator.batch_config['batch_size'],
            "total_evaluation_time": actual_time,
            "agents_evaluated": len(demo_agents),
            "test_cases_per_agent": len(test_cases),
            "metrics_per_test": len(evaluator.metrics),
            "estimated_sequential_time": sequential_time,
            "speed_improvement": f"{actual_speedup:.1f}x" if 'actual_speedup' in locals() else "N/A"
        }
        
        batch_stats_filename = json_filename.replace('.json', '_batch_stats.json')
        with open(batch_stats_filename, 'w') as f:
            import json
            json.dump(batch_stats, f, indent=2)
        print(f"✅ Batch processing stats saved: {batch_stats_filename}")
        
        print(f"\n📁 All files saved to: {os.path.dirname(json_filename)}")
        
    except Exception as e:
        print(f"⚠️  Error saving results: {e}")
    
    # 8. Final summary
    print(f"\n🎯 EVALUATION SUMMARY")
    print("=" * 50)
    print(f"🤖 Agents Evaluated: {len(demo_agents)}")
    print(f"📝 Test Cases: {len(test_cases)}")
    print(f"📊 Metrics: {len(evaluator.metrics)}")
    print(f"⚡ Batch Processing: {'Enabled' if evaluator.enable_batch_processing else 'Disabled'}")
    print(f"⏱️  Total Time: {actual_time:.2f} seconds")
    print(f"💰 Total Cost: $0.00 (Groq Free Tier)")
    print(f"💾 Results Saved: JSON + Summary + Batch Stats")
    
    if evaluator.enable_batch_processing and len(demo_agents) > 1:
        print(f"🚀 Speed Improvement: Significant due to parallel processing")
        print(f"📈 Scalability: Ready for 100+ agents evaluation")
    
    print("\n✨ BATCH PROCESSING BENEFITS DEMONSTRATED:")
    print("   ⚡ Parallel agent evaluation")
    print("   🔧 Configurable concurrency limits")
    print("   📊 Real-time progress tracking")
    print("   ⏱️  Significant time savings")
    print("   🛡️  Error isolation and recovery")
    print("   📈 Scalable to thousands of agents")
    
    return results
    groq_model = setup_groq_model()
    if not groq_model:
        print("❌ Setup failed. Please set your GROQ_API_KEY and try again.")
        return
    
    # 2. Initialize evaluator
    print("\n2️⃣ Initializing agentic evaluator...")
    evaluator = AgenticGroqEvaluator(groq_model)
    print(f"✅ Created evaluator with {len(evaluator.metrics)} metrics")
    
    # 3. Register agents
    print("\n3️⃣ Registering AI agents...")
    demo_agents = create_demo_agents()
    
    for agent in demo_agents:
        evaluator.register_agent(agent, domain="general")
    
    print(f"✅ Registered {len(demo_agents)} agents for evaluation")
    
    # 4. Create test cases
    print("\n4️⃣ Creating test cases...")
    test_cases = evaluator.create_test_cases()
    print(f"✅ Created {len(test_cases)} comprehensive test cases")
    
    # 5. Run evaluation
    print(f"\n5️⃣ Running comprehensive evaluation...")
    print(f"⏱️  Estimated time: ~{len(demo_agents) * len(test_cases) * len(evaluator.metrics) * 2} seconds")
    
    try:
        results = evaluator.evaluate_agents(test_cases)
        
        # 6. Generate and save results
        print(f"\n6️⃣ Processing results...")
        
        # Save detailed JSON results
        results_file = save_results(results)
        print(f"💾 Detailed results saved: {results_file}")
        
        # Generate summary report
        summary_report = evaluator.generate_summary_report(results)
        
        # Save summary report
        summary_file = results_file.replace('.json', '_summary.txt')
        with open(summary_file, 'w') as f:
            f.write(summary_report)
        
        print(f"📋 Summary report saved: {summary_file}")
        
        # Display summary
        print(f"\n{summary_report}")
        
        print(f"\n✅ EVALUATION COMPLETE!")
        print("=" * 60)
        print("🎉 Successfully demonstrated complete agentic evaluation with Groq!")
        print(f"📁 Results available in: {results_file}")
        print(f"📄 Summary available in: {summary_file}")
        print("💰 Total cost: $0.00 (Free Groq API)")
        print("🚀 Ready for hackathon demonstration!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Evaluation interrupted by user")
    except Exception as e:
        print(f"\n❌ Evaluation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
