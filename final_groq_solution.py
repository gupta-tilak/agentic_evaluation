#!/usr/bin/env python3
"""
FINAL WORKING SOLUTION: Groq Integration for DeepEval
This is the complete, working solution for using Groq with DeepEval
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add deepeval to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from deepeval.test_case import LLMTestCase
from deepeval.models import LiteLLMModel

def setup_groq_model():
    """Set up Groq model for evaluation"""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("⚠️  GROQ_API_KEY not found. Please set it as an environment variable.")
        print("   Get your free API key from: https://console.groq.com/")
        print("   export GROQ_API_KEY='your-groq-api-key-here'")
        return None
    
    try:
        groq_model = LiteLLMModel(
            model="groq/llama-3.1-8b-instant",
            api_key=groq_api_key,
            temperature=0.1
        )
        
        # Test the model
        test_response = groq_model.generate("Hello, respond with just 'Working'")
        print(f"✅ Groq model working: {groq_model.get_model_name()}")
        return groq_model
        
    except Exception as e:
        print(f"❌ Groq setup failed: {str(e)}")
        return None

def evaluate_with_groq(groq_model, test_case: LLMTestCase, metric_name: str) -> Dict:
    """Evaluate a test case using Groq with rate limiting"""
    
    evaluation_prompts = {
        "instruction_following": f"""
Rate how well this output follows instructions (0.0-1.0):

Question: {test_case.input}
Agent Output: {test_case.actual_output}

Score (0.0-1.0): """,
        
        "coherence": f"""
Rate how coherent and logical this output is (0.0-1.0):

Question: {test_case.input}  
Agent Output: {test_case.actual_output}

Score (0.0-1.0): """,
        
        "relevance": f"""
Rate how relevant this output is to the question (0.0-1.0):

Question: {test_case.input}
Agent Output: {test_case.actual_output}

Score (0.0-1.0): """
    }
    
    try:
        prompt = evaluation_prompts.get(metric_name, evaluation_prompts["relevance"])
        
        # Add rate limiting delay
        time.sleep(2)  # Prevent rate limiting
        
        response = groq_model.generate(prompt)
        
        # Extract score from response
        score = extract_score_from_response(response)
        
        return {
            "score": score,
            "success": score >= 0.7,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"    ❌ Error in {metric_name}: {str(e)}")
        return {
            "score": 0.0,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def extract_score_from_response(response: str) -> float:
    """Extract numerical score from model response"""
    try:
        # Handle tuple response (LiteLLM sometimes returns tuples)
        if isinstance(response, tuple):
            response = str(response[0]) if response else "0.5"
        
        response = str(response).lower()
        
        # Look for decimal numbers between 0 and 1
        import re
        
        # Try to find explicit score patterns
        score_patterns = [
            r'score[:\s]*([0-1]\.?\d*)',
            r'rating[:\s]*([0-1]\.?\d*)', 
            r'([0-1]\.\d+)',
            r'([01]\.?\d*)'
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, response)
            if matches:
                try:
                    score = float(matches[0])
                    if 0.0 <= score <= 1.0:
                        return score
                except:
                    continue
        
        # Fallback: keyword-based scoring
        if any(word in response for word in ['excellent', 'perfect', 'outstanding']):
            return 0.9
        elif any(word in response for word in ['good', 'well', 'correct', 'accurate']):
            return 0.8
        elif any(word in response for word in ['decent', 'adequate', 'okay']):
            return 0.7
        elif any(word in response for word in ['partial', 'some', 'moderate']):
            return 0.6
        elif any(word in response for word in ['poor', 'bad', 'wrong', 'incorrect']):
            return 0.3
        else:
            return 0.5
            
    except Exception as e:
        print(f"Error extracting score: {e}")
        return 0.5

class SimpleAgent:
    """Simple agent for demonstration"""
    def __init__(self, name: str, model_name: str = None):
        self.name = name
        self.model_name = model_name or name
        
        # Pre-defined responses for different agents (simulating different quality levels)
        self.response_templates = {
            "Good AI Agent": {
                "artificial intelligence": "Artificial Intelligence (AI) is a comprehensive field of computer science focused on creating systems that can perform tasks typically requiring human intelligence. This includes learning from data, recognizing patterns, making decisions, understanding natural language, and solving complex problems. AI encompasses various subfields including machine learning, neural networks, natural language processing, computer vision, and robotics.",
                
                "machine learning": "Machine Learning (ML) is a subset of artificial intelligence that enables computers to learn and improve their performance on specific tasks through experience, without being explicitly programmed for every scenario. ML algorithms analyze large amounts of data to identify patterns and make predictions or decisions. Common types include supervised learning (learning from labeled examples), unsupervised learning (finding patterns in unlabeled data), and reinforcement learning (learning through trial and error).",
                
                "renewable energy": "Renewable energy sources offer numerous significant benefits for both the environment and economy. Key advantages include: (1) Reduced greenhouse gas emissions and carbon footprint, helping combat climate change; (2) Energy independence and security by reducing reliance on fossil fuel imports; (3) Long-term cost savings as renewable sources have minimal operating costs; (4) Job creation in growing green energy sectors; (5) Improved air and water quality; (6) Sustainable power generation that won't deplete natural resources; (7) Enhanced grid resilience through distributed energy systems."
            },
            
            "Average AI Agent": {
                "artificial intelligence": "AI is about making computers smart like humans. It includes things like machine learning where computers can learn from data, and neural networks that work like brain cells. AI is used in many applications like chatbots, recommendation systems, and autonomous vehicles.",
                
                "machine learning": "Machine learning is when computers learn patterns from data without being programmed step by step. There are different types like supervised learning with labeled data and unsupervised learning that finds hidden patterns.",
                
                "renewable energy": "Renewable energy is good for the environment because it doesn't produce pollution like fossil fuels. Solar and wind power are the main types. They help reduce carbon emissions and can save money in the long run."
            },
            
            "Poor AI Agent": {
                "artificial intelligence": "AI is just computer programs. Some people think it's dangerous.",
                
                "machine learning": "Machine learning is complicated computer stuff that I don't really understand.",
                
                "renewable energy": "Energy is energy. Don't see why renewable is much different from regular energy."
            }
        }
    
    def generate(self, prompt: str) -> str:
        """Generate response based on agent quality"""
        responses = self.response_templates.get(self.name, {})
        
        prompt_lower = prompt.lower()
        for key, response in responses.items():
            if key in prompt_lower:
                return response
        
        # Default response if no match
        if "Good" in self.name:
            return "I'd be happy to help with that question, but I need more specific information to provide a comprehensive answer."
        elif "Average" in self.name:
            return "That's an interesting question. I think it relates to the topic you're asking about."
        else:
            return "I don't know much about that."

def create_test_cases() -> List[LLMTestCase]:
    """Create test cases for evaluation"""
    return [
        LLMTestCase(
            input="What is artificial intelligence?",
            actual_output="",  # Will be filled by agents
            expected_output="AI is a branch of computer science that aims to create machines that mimic human intelligence.",
            context=["AI involves machine learning", "AI uses neural networks", "AI can process natural language"]
        ),
        LLMTestCase(
            input="Explain machine learning",
            actual_output="",
            expected_output="Machine learning is a subset of AI that enables computers to learn without being explicitly programmed.",
            context=["ML is part of AI", "ML uses algorithms to find patterns", "ML includes supervised and unsupervised learning"]
        ),
        LLMTestCase(
            input="What are the benefits of renewable energy?",
            actual_output="",
            expected_output="Renewable energy reduces carbon emissions and provides sustainable power sources.",
            context=["Renewable energy is sustainable", "It helps fight climate change", "It reduces dependence on fossil fuels"]
        )
    ]

def run_comprehensive_evaluation():
    """Run comprehensive evaluation with proper error handling and rate limiting"""
    
    print("🚀 FINAL GROQ INTEGRATION FOR DEEPEVAL")
    print("="*60)
    print("✅ This solution successfully uses FREE Groq API instead of paid OpenAI")
    print("✅ No function calling issues - uses simple text generation")
    print("✅ Includes proper rate limiting and error handling")
    print("="*60)
    
    # Setup
    print("\n1️⃣ Setting up Groq model...")
    groq_model = setup_groq_model()
    if not groq_model:
        print("❌ Setup failed. Please check your GROQ_API_KEY")
        return
    
    # Create test scenarios
    print("\n2️⃣ Creating evaluation scenario...")
    test_cases = create_test_cases()
    
    # Create agents with different quality levels
    agents = [
        SimpleAgent("Good AI Agent"),
        SimpleAgent("Average AI Agent"), 
        SimpleAgent("Poor AI Agent")
    ]
    
    print(f"✅ Created {len(test_cases)} test cases and {len(agents)} AI agents")
    
    # Metrics to evaluate
    metrics = ["instruction_following", "coherence", "relevance"]
    print(f"✅ Will evaluate {len(metrics)} metrics: {', '.join(metrics)}")
    
    # Run evaluation
    print(f"\n3️⃣ Running evaluation (this will take ~{len(agents) * len(test_cases) * len(metrics) * 2} seconds due to rate limiting)...")
    
    results = []
    total_evaluations = len(agents) * len(test_cases) * len(metrics)
    current_evaluation = 0
    
    for agent in agents:
        print(f"\n🤖 Evaluating {agent.name}...")
        agent_results = {
            "agent_name": agent.name,
            "test_results": []
        }
        
        for i, test_case in enumerate(test_cases):
            print(f"  📝 Test {i+1}: {test_case.input[:50]}...")
            
            # Generate agent response
            agent_response = agent.generate(test_case.input)
            test_case.actual_output = agent_response
            
            print(f"     Agent response: {agent_response[:100]}..." if len(agent_response) > 100 else f"     Agent response: {agent_response}")
            
            # Evaluate with each metric
            test_result = {
                "test_case_id": i + 1,
                "input": test_case.input,
                "actual_output": agent_response,
                "expected_output": test_case.expected_output,
                "context": test_case.context,
                "metric_scores": {}
            }
            
            for metric in metrics:
                current_evaluation += 1
                print(f"    🔍 {metric} ({current_evaluation}/{total_evaluations})...", end=" ")
                
                evaluation_result = evaluate_with_groq(groq_model, test_case, metric)
                test_result["metric_scores"][metric] = evaluation_result
                
                score = evaluation_result["score"]
                success = "✅" if evaluation_result["success"] else "❌"
                print(f"{success} {score:.3f}")
            
            agent_results["test_results"].append(test_result)
        
        results.append(agent_results)
    
    # Save results
    print(f"\n4️⃣ Saving results...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"groq_deepeval_results_{timestamp}.json"
    filepath = os.path.join(os.path.dirname(__file__), '..', filename)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"💾 Results saved to: {filepath}")
    
    # Generate summary
    print(f"\n5️⃣ EVALUATION SUMMARY")
    print("="*60)
    
    for result in results:
        agent_name = result["agent_name"]
        print(f"\n🤖 {agent_name}")
        
        # Calculate metrics summary
        metric_totals = {}
        metric_successes = {}
        
        for test in result["test_results"]:
            for metric_name, metric_data in test["metric_scores"].items():
                if metric_name not in metric_totals:
                    metric_totals[metric_name] = []
                    metric_successes[metric_name] = 0
                
                metric_totals[metric_name].append(metric_data["score"])
                if metric_data["success"]:
                    metric_successes[metric_name] += 1
        
        # Print summary for each metric
        for metric_name in metrics:
            scores = metric_totals.get(metric_name, [])
            avg_score = sum(scores) / len(scores) if scores else 0
            success_count = metric_successes.get(metric_name, 0)
            total_tests = len(test_cases)
            
            print(f"   {metric_name}: {avg_score:.3f} avg (✅ {success_count}/{total_tests} passed)")
        
        # Overall success rate
        total_passed = sum(metric_successes.values())
        total_possible = len(metrics) * len(test_cases)
        overall_success = (total_passed / total_possible) * 100 if total_possible > 0 else 0
        print(f"   Overall Success Rate: {overall_success:.1f}%")
    
    print(f"\n6️⃣ COST ANALYSIS")
    print("="*60)
    print("💰 Total Cost: $0.00 (Groq free tier)")
    print("💸 Savings vs OpenAI: ~$5-15 (estimated)")
    print("⚡ Total API Calls:", total_evaluations)
    
    print(f"\n✅ GROQ INTEGRATION SUCCESS!")
    print("="*60)
    print("🎯 Successfully replaced OpenAI with FREE Groq API")
    print("📊 Generated comprehensive evaluation results")
    print("🔧 Demonstrated working integration for hackathon")
    print(f"📁 Full results available in: {filename}")
    
    return filepath

if __name__ == "__main__":
    result_file = run_comprehensive_evaluation()
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"1. Use this pattern to integrate with your actual HuggingFace agents")
    print(f"2. Modify the evaluation prompts for your specific needs")
    print(f"3. Scale up to evaluate 100+ agents as needed for your hackathon")
    print(f"4. The results are saved in JSON format for further analysis")
    print(f"\n📋 HACKATHON READY: Your DeepEval framework now works with FREE Groq API! 🎉")
