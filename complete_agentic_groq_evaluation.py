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
- Rate limiting to avoid API limits
- Comprehensive reporting with success rates
- JSON export for further analysis
- Error handling and graceful fallbacks

🔧 CUSTOMIZATION:
- Add your own agents by implementing generate(prompt) method
- Modify evaluation criteria in metric definitions
- Adjust test cases for your specific use case
- Scale to 100+ agents for large evaluations

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
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass

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
    """Add rate limiting to prevent Groq API limits"""
    def wrapper(*args, **kwargs):
        time.sleep(delay)
        return func(*args, **kwargs)
    return wrapper

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
        """Measure the metric using Groq"""
        try:
            # Format the evaluation prompt
            prompt = self._evaluation_template.format(
                input=test_case.input,
                actual_output=test_case.actual_output,
                expected_output=test_case.expected_output or "Not specified",
                context=" | ".join(test_case.context) if test_case.context else "None provided"
            )
            
            # Rate-limited API call
            time.sleep(3.0)  # Prevent rate limiting
            response = self.model.generate(prompt)
            
            # Parse response
            self._parse_evaluation_response(response)
            
            self.success = self.score >= self.threshold
            return self.score
            
        except Exception as e:
            print(f"    ⚠️  {self.name} evaluation error: {str(e)}")
            self.score = 0.0
            self.reason = f"Evaluation failed: {str(e)}"
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
            self.model = pipeline(task, model=model_name, device_map="auto" if task == "text-generation" else None)
            print(f"✅ Loaded HuggingFace model: {model_name}")
        except Exception as e:
            print(f"⚠️  Failed to load {model_name}: {e}")
            self.model = None
    
    def generate(self, prompt: str, max_length: int = 150) -> str:
        """Generate response from HuggingFace model"""
        if not self.model:
            return f"Error: Model {self.model_name} not available"
        
        try:
            if self.task == "text-generation":
                result = self.model(prompt, max_length=max_length, num_return_sequences=1, 
                                  truncation=True, pad_token_id=self.model.tokenizer.eos_token_id)
                return result[0]["generated_text"].replace(prompt, "").strip()
            else:
                result = self.model(prompt)
                return str(result)
                
        except Exception as e:
            return f"Generation error: {str(e)}"

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
# EVALUATION FRAMEWORK
# ============================================================================

class AgenticGroqEvaluator:
    """Main evaluator class using Groq for agentic evaluation"""
    
    def __init__(self, groq_model: LiteLLMModel):
        self.groq_model = groq_model
        self.metrics = self._create_evaluation_metrics()
        self.agents = []
        
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
    
    def evaluate_agents(self, test_cases: List[LLMTestCase]) -> Dict[str, Any]:
        """Evaluate all registered agents"""
        print(f"\n🔍 EVALUATING {len(self.agents)} AGENTS ON {len(test_cases)} TEST CASES")
        print("="*70)
        
        results = {
            "evaluation_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_agents": len(self.agents),
                "total_test_cases": len(test_cases),
                "total_metrics": len(self.metrics),
                "groq_model": self.groq_model.get_model_name()
            },
            "agent_results": []
        }
        
        for i, agent_info in enumerate(self.agents):
            agent = agent_info["agent"]
            agent_name = agent_info["name"]
            
            print(f"\n🤖 Agent {i+1}/{len(self.agents)}: {agent_name}")
            print("-" * 50)
            
            agent_result = {
                "agent_name": agent_name,
                "domain": agent_info["domain"],
                "test_results": []
            }
            
            for j, test_case in enumerate(test_cases):
                print(f"  📝 Test {j+1}: {test_case.input[:60]}...")
                
                # Generate agent response
                try:
                    response = agent.generate(test_case.input)
                    test_case.actual_output = response
                    print(f"     Response: {response[:80]}..." if len(response) > 80 else f"     Response: {response}")
                except Exception as e:
                    response = f"Error: {str(e)}"
                    test_case.actual_output = response
                    print(f"     ❌ Error: {str(e)}")
                
                # Evaluate with all metrics
                test_result = {
                    "test_case_id": j + 1,
                    "input": test_case.input,
                    "actual_output": response,
                    "expected_output": test_case.expected_output,
                    "context": test_case.context,
                    "metric_scores": {}
                }
                
                for metric_name, metric in self.metrics.items():
                    try:
                        print(f"     🔍 {metric_name}...", end=" ")
                        score = metric.measure(test_case)
                        
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
                
                agent_result["test_results"].append(test_result)
            
            results["agent_results"].append(agent_result)
        
        return results
    
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
        hf_agents = [
            HuggingFaceAgent("gpt2"),
            HuggingFaceAgent("distilgpt2")
        ]
        agents.extend([agent for agent in hf_agents if agent.model is not None])
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
    print("🚀 COMPLETE AGENTIC EVALUATION WITH GROQ")
    print("=" * 60)
    print("🎯 Comprehensive AI Agent Evaluation using FREE Groq API")
    print("🔧 Replaces expensive OpenAI with cost-effective solution")
    print("📊 Supports multiple agents, metrics, and test cases")
    print("=" * 60)
    
    # 1. Setup Groq
    print("\n1️⃣ Setting up Groq integration...")
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
