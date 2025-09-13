"""
A comprehensive example of using the Agentic Evaluation Framework with Hugging Face models.
This example demonstrates:
1. Setting up multiple agents with different HuggingFace models
2. Creating test cases for different domains
3. Running evaluations
4. Generating and analyzing results
5. Exporting results in different formats
"""

import os
from datetime import datetime
from typing import List, Dict, Any
from transformers import pipeline
from deepeval.agentic import (
    AgenticEvaluator,
    EvaluationConfig,
    DomainType
)
from deepeval.test_case import LLMTestCase

class HuggingFaceModelWrapper:
    """Wrapper for HuggingFace models to ensure consistent interface."""
    
    def __init__(self, model_name: str, task: str = "text-generation"):
        self.model_name = model_name
        self.model = pipeline(task, model=model_name)
        
    def generate(self, prompt: str, max_length: int = 100) -> str:
        """Generate response for given prompt."""
        result = self.model(prompt, max_length=max_length, num_return_sequences=1)
        return result[0]["generated_text"]

def setup_huggingface_agents() -> List[Dict[str, Any]]:
    """Set up various HuggingFace models as agents for different domains."""
    return [
        # General purpose models
        {
            "name": "DialoGPT Agent",
            "model_name": "microsoft/DialoGPT-medium",
            "domain": DomainType.GENERAL,
            "metadata": {
                "description": "General-purpose conversational agent",
                "model_provider": "HuggingFace",
                "model_type": "DialoGPT"
            }
        },
        # QA specialized models
        {
            "name": "DistilBERT QA Agent",
            "model_name": "distilbert-base-cased-distilled-squad",
            "domain": DomainType.QA,
            "metadata": {
                "description": "Specialized for question answering",
                "model_provider": "HuggingFace",
                "model_type": "DistilBERT"
            }
        },
        # Summarization models
        {
            "name": "T5 Summarization Agent",
            "model_name": "t5-small",
            "domain": DomainType.SUMMARIZATION,
            "metadata": {
                "description": "Specialized for text summarization",
                "model_provider": "HuggingFace",
                "model_type": "T5"
            }
        },
        # Code generation models
        {
            "name": "CodeBERT Agent",
            "model_name": "microsoft/codebert-base",
            "domain": DomainType.CODE_GENERATION,
            "metadata": {
                "description": "Specialized for code-related tasks",
                "model_provider": "HuggingFace",
                "model_type": "CodeBERT"
            }
        }
    ]

def create_test_cases() -> List[LLMTestCase]:
    """Create diverse test cases for different domains."""
    return [
        # General domain test cases
        LLMTestCase(
            input="What is artificial intelligence?",
            actual_output="Artificial intelligence is the simulation of human intelligence by machines.",
            expected_output="Artificial intelligence refers to the development of computer systems capable of performing tasks that typically require human intelligence.",
            context=["AI involves machine learning, neural networks, and other computational approaches."],
            domain=DomainType.GENERAL
        ),
        
        # QA domain test cases
        LLMTestCase(
            input="Who wrote 'Romeo and Juliet'?",
            actual_output="William Shakespeare wrote Romeo and Juliet.",
            expected_output="William Shakespeare wrote Romeo and Juliet, a tragic play about two young lovers.",
            context=["Romeo and Juliet is a tragedy written by William Shakespeare early in his career."],
            domain=DomainType.QA
        ),
        
        # Summarization domain test cases
        LLMTestCase(
            input="Summarize the following text: The Industrial Revolution was a period of major industrialization and innovation during the late 18th and early 19th century. The Industrial Revolution began in Great Britain and quickly spread throughout Europe and the United States.",
            actual_output="The Industrial Revolution was a time of major industrial change that started in Britain and spread to Europe and the US.",
            expected_output="The Industrial Revolution was a period of significant industrialization in the late 18th and early 19th century, originating in Great Britain before spreading to Europe and the United States.",
            context=["Historical text about the Industrial Revolution and its impact."],
            domain=DomainType.SUMMARIZATION
        ),
        
        # Code generation test cases
        LLMTestCase(
            input="Write a Python function to calculate the factorial of a number.",
            actual_output="""def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)""",
            expected_output="""def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0:
        return 1
    return n * factorial(n-1)""",
            context=["Implementation should handle edge cases and use recursion."],
            domain=DomainType.CODE_GENERATION
        )
    ]

def main():
    """Main function to run the comprehensive evaluation."""
    print("🚀 Starting Comprehensive HuggingFace Agentic Evaluation")
    print("=" * 80)
    
    # 1. Configure the evaluation
    print("\n1️⃣ Configuring Evaluation Framework...")
    config = EvaluationConfig(
        max_agents=10,
        batch_size=2,
        max_concurrent=2,
        timeout_seconds=300,
        retry_attempts=3,
        include_explanations=True,
        strict_mode=False,
        cache_results=True
    )
    
    # 2. Initialize evaluator
    print("2️⃣ Initializing Evaluator...")
    evaluator = AgenticEvaluator(config=config)
    
    # 3. Register HuggingFace agents
    print("3️⃣ Registering HuggingFace Agents...")
    agents = setup_huggingface_agents()
    agent_ids = evaluator.register_agents_batch(agents)
    print(f"✅ Registered {len(agent_ids)} agents successfully")
    
    # 4. Create test cases
    print("\n4️⃣ Creating Test Cases...")
    test_cases = create_test_cases()
    print(f"✅ Created {len(test_cases)} test cases across different domains")
    
    # 5. Run evaluation
    print("\n5️⃣ Running Evaluation...")
    evaluation_result = evaluator.evaluate_agents(
        test_cases=test_cases,
        async_mode=True,
        show_progress=True
    )
    
    # 6. Generate reports
    print("\n6️⃣ Generating Reports...")
    
    # Generate leaderboard
    print("\n📊 Leaderboard:")
    leaderboard = evaluator.generate_leaderboard(evaluation_result)
    evaluator.print_leaderboard(leaderboard)
    
    # Generate performance explanations for each agent
    print("\n📝 Detailed Performance Analysis:")
    for agent_id in agent_ids:
        explanation = evaluator.explain_performance(agent_id, evaluation_result)
        print(f"\nAgent Performance Analysis for {agent_id}:")
        evaluator.print_performance_explanation(explanation)
    
    # Generate domain analysis
    print("\n🎯 Domain-specific Analysis:")
    domain_analysis = evaluator.get_domain_analysis(evaluation_result)
    print(domain_analysis)
    
    # 7. Export results
    print("\n7️⃣ Exporting Results...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export to JSON
    json_path = f"evaluation_results_{timestamp}.json"
    evaluator.export_results(evaluation_result, json_path, "json")
    print(f"✅ Results exported to {json_path}")
    
    # Export to CSV
    csv_path = f"evaluation_results_{timestamp}.csv"
    evaluator.export_results(evaluation_result, csv_path, "csv")
    print(f"✅ Results exported to {csv_path}")
    
    print("\n✨ Evaluation Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
