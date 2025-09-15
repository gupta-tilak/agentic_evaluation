#!/usr/bin/env python3
"""
Agentic Evaluation Framework Example

This example demonstrates how to use the new agentic evaluation framework
to evaluate multiple AI agents across the four core dimensions:
1. Instruction Following
2. Hallucination Detection  
3. Assumption Control
4. Coherence & Accuracy

The framework supports:
- Batch processing of 100+ agents
- Domain-specific evaluation
- Detailed performance reporting
- Leaderboards and explanations
- Export capabilities
"""

import os
import asyncio
from typing import List, Dict, Any
from deepeval import AgenticEvaluator, EvaluationConfig, DomainType
from deepeval.test_case import LLMTestCase


def create_sample_test_cases() -> List[LLMTestCase]:
    """Create sample test cases for evaluation"""
    test_cases = [
        LLMTestCase(
            input="What is the capital of France?",
            actual_output="The capital of France is Paris.",
            expected_output="Paris is the capital of France.",
            context=["France is a country in Europe. Its capital city is Paris."]
        ),
        LLMTestCase(
            input="Explain the process of photosynthesis.",
            actual_output="Photosynthesis is the process by which plants convert sunlight, carbon dioxide, and water into glucose and oxygen. This occurs in the chloroplasts of plant cells.",
            expected_output="Photosynthesis converts light energy into chemical energy in plants.",
            context=["Photosynthesis is a process used by plants to convert light energy into chemical energy."]
        ),
        LLMTestCase(
            input="What are the benefits of renewable energy?",
            actual_output="Renewable energy sources like solar and wind power offer several benefits: they are environmentally friendly, reduce greenhouse gas emissions, create jobs, and provide energy security.",
            expected_output="Renewable energy reduces environmental impact and provides sustainable power.",
            context=["Renewable energy sources include solar, wind, and hydroelectric power."]
        ),
        LLMTestCase(
            input="How do you calculate the area of a circle?",
            actual_output="To calculate the area of a circle, you use the formula A = πr², where A is the area, π (pi) is approximately 3.14159, and r is the radius of the circle.",
            expected_output="The area of a circle is calculated using the formula A = πr².",
            context=["The area of a circle can be calculated using the mathematical formula involving pi and radius."]
        ),
        LLMTestCase(
            input="What is machine learning?",
            actual_output="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms to identify patterns in data.",
            expected_output="Machine learning is a method of data analysis that automates analytical model building.",
            context=["Machine learning is a branch of artificial intelligence focused on algorithms that can learn from data."]
        )
    ]
    return test_cases


def create_sample_agents_data() -> List[Dict[str, Any]]:
    """Create sample agent data for registration"""
    agents_data = [
        {
            "name": "GPT-4 Agent",
            "model_name": "gpt-4",
            "domain": "general",
            "metadata": {"version": "4.0", "provider": "OpenAI"}
        },
        {
            "name": "Claude Agent",
            "model_name": "claude-3",
            "domain": "general", 
            "metadata": {"version": "3.0", "provider": "Anthropic"}
        },
        {
            "name": "Gemini Agent",
            "model_name": "gemini-pro",
            "domain": "general",
            "metadata": {"version": "1.0", "provider": "Google"}
        },
        {
            "name": "QA Specialist",
            "model_name": "gpt-3.5-turbo",
            "domain": "qa",
            "metadata": {"specialization": "question-answering", "provider": "OpenAI"}
        },
        {
            "name": "Reasoning Expert",
            "model_name": "claude-2",
            "domain": "reasoning",
            "metadata": {"specialization": "logical-reasoning", "provider": "Anthropic"}
        },
        {
            "name": "Code Generator",
            "model_name": "gpt-4",
            "domain": "code_generation",
            "metadata": {"specialization": "code-generation", "provider": "OpenAI"}
        },
        {
            "name": "Conversation Bot",
            "model_name": "gpt-3.5-turbo",
            "domain": "conversation",
            "metadata": {"specialization": "conversational-ai", "provider": "OpenAI"}
        },
        {
            "name": "Summarization Expert",
            "model_name": "claude-3",
            "domain": "summarization",
            "metadata": {"specialization": "text-summarization", "provider": "Anthropic"}
        }
    ]
    return agents_data


async def main():
    """Main example function"""
    print("🚀 Agentic Evaluation Framework Example")
    print("=" * 50)
    
    # Set up OpenAI API key (required for evaluation)
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # 1. Create evaluation configuration
    print("\n📋 Setting up evaluation configuration...")
    config = EvaluationConfig(
        max_agents=100,
        batch_size=5,
        max_concurrent=10,
        timeout_seconds=300,
        include_explanations=True,
        strict_mode=False,
        cache_results=True
    )
    
    # 2. Initialize the agentic evaluator
    print("🔧 Initializing AgenticEvaluator...")
    evaluator = AgenticEvaluator(config=config)
    
    # 3. Register sample agents
    print("👥 Registering sample agents...")
    agents_data = create_sample_agents_data()
    agent_ids = evaluator.register_agents_batch(agents_data)
    
    print(f"✅ Registered {len(agent_ids)} agents:")
    for i, agent_id in enumerate(agent_ids):
        agent = evaluator.agent_registry.get_agent(agent_id)
        print(f"   {i+1}. {agent.name} ({agent.model_name}) - {agent.domain.value}")
    
    # 4. Create test cases
    print("\n📝 Creating test cases...")
    test_cases = create_sample_test_cases()
    print(f"✅ Created {len(test_cases)} test cases")
    
    # 5. Run evaluation
    print("\n🔍 Running agentic evaluation...")
    print("   This may take a few minutes depending on the number of agents...")
    
    try:
        evaluation_result = evaluator.evaluate_agents(
            test_cases=test_cases,
            async_mode=True,
            show_progress=True
        )
        
        print(f"\n✅ Evaluation completed!")
        print(f"   ⏱️  Time: {evaluation_result.evaluation_time:.2f} seconds")
        print(f"   ✅ Successful: {evaluation_result.successful_evaluations}")
        print(f"   ❌ Failed: {evaluation_result.failed_evaluations}")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return
    
    # 6. Generate and display leaderboard
    print("\n🏆 Generating leaderboard...")
    leaderboard = evaluator.generate_leaderboard(evaluation_result)
    
    print("\n📊 TOP PERFORMERS:")
    print("-" * 60)
    for i, ranking in enumerate(leaderboard.top_performers[:5]):
        status = "✅" if ranking.overall_score >= 0.7 else "❌"
        print(f"{i+1:2d}. {ranking.agent_name:<20} | Score: {ranking.overall_score:.3f} | {status}")
    
    # 7. Show detailed performance for top agent
    if leaderboard.top_performers:
        top_agent = leaderboard.top_performers[0]
        print(f"\n🔍 Detailed analysis for top performer: {top_agent.agent_name}")
        
        explanation = evaluator.explain_performance(top_agent.agent_id, evaluation_result)
        
        print(f"\n📈 Overall Performance:")
        print(f"   {explanation.overall_explanation}")
        
        if explanation.strengths:
            print(f"\n💪 Strengths:")
            for strength in explanation.strengths:
                print(f"   • {strength}")
        
        if explanation.weaknesses:
            print(f"\n⚠️  Areas for Improvement:")
            for weakness in explanation.weaknesses:
                print(f"   • {weakness}")
        
        if explanation.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in explanation.recommendations:
                print(f"   • {rec}")
    
    # 8. Domain analysis
    print(f"\n🌐 Domain Analysis:")
    domain_analysis = evaluator.get_domain_analysis(evaluation_result)
    
    for domain, analysis in domain_analysis.items():
        print(f"\n   {domain.upper()}:")
        print(f"   • Agents: {analysis['agent_count']}")
        print(f"   • Average Score: {analysis['average_score']:.3f}")
        print(f"   • Grade: {analysis['performance_grade']}")
    
    # 9. Performance insights
    print(f"\n📊 Performance Insights:")
    insights = evaluator.get_performance_insights(evaluation_result)
    
    overall = insights['overall_performance']
    print(f"   • Total Agents: {overall['total_agents']}")
    print(f"   • Average Score: {overall['average_score']:.3f}")
    print(f"   • Pass Rate: {overall['pass_rate']:.1%}")
    
    # 10. Export results
    print(f"\n💾 Exporting results...")
    
    # Export to JSON
    json_file = "agentic_evaluation_results.json"
    if evaluator.export_results(evaluation_result, json_file, "json"):
        print(f"   ✅ JSON export: {json_file}")
    
    # Export to CSV
    csv_file = "agentic_evaluation_results.csv"
    if evaluator.export_results(evaluation_result, csv_file, "csv"):
        print(f"   ✅ CSV export: {csv_file}")
    
    # Export agent registry
    registry_file = "agent_registry.json"
    if evaluator.export_agents(registry_file):
        print(f"   ✅ Agent registry: {registry_file}")
    
    # 11. Summary
    print(f"\n🎉 Agentic Evaluation Complete!")
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"   • Agents Evaluated: {evaluation_result.agent_metrics.total_agents}")
    print(f"   • Test Cases: {evaluation_result.total_test_cases}")
    print(f"   • Evaluation Time: {evaluation_result.evaluation_time:.2f}s")
    print(f"   • Success Rate: {evaluation_result.successful_evaluations/evaluation_result.agent_metrics.total_agents:.1%}")
    print(f"   • Top Performer: {leaderboard.top_performers[0].agent_name if leaderboard.top_performers else 'N/A'}")
    
    print(f"\n📁 Files Generated:")
    print(f"   • {json_file} - Detailed results in JSON format")
    print(f"   • {csv_file} - Results summary in CSV format")
    print(f"   • {registry_file} - Agent registry backup")
    
    print(f"\n🚀 Next Steps:")
    print(f"   • Review the exported files for detailed analysis")
    print(f"   • Use the insights to improve underperforming agents")
    print(f"   • Run evaluations regularly to track performance trends")
    print(f"   • Add more test cases for comprehensive evaluation")


def run_sync_example():
    """Synchronous version of the example"""
    print("🚀 Agentic Evaluation Framework - Synchronous Example")
    print("=" * 60)
    
    # Set up OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        return
    
    # Initialize evaluator
    config = EvaluationConfig(max_agents=50, batch_size=3, max_concurrent=5)
    evaluator = AgenticEvaluator(config=config)
    
    # Register a few agents
    agent_ids = evaluator.register_agents_batch([
        {"name": "Test Agent 1", "model_name": "gpt-3.5-turbo", "domain": "general"},
        {"name": "Test Agent 2", "model_name": "gpt-4", "domain": "qa"},
    ])
    
    # Create test cases
    test_cases = create_sample_test_cases()[:3]  # Use fewer test cases for demo
    
    # Run synchronous evaluation
    print("🔍 Running synchronous evaluation...")
    evaluation_result = evaluator.evaluate_agents(
        test_cases=test_cases,
        async_mode=False  # Use synchronous mode
    )
    
    # Display results
    print(f"\n✅ Evaluation completed in {evaluation_result.evaluation_time:.2f}s")
    print(f"   Successful: {evaluation_result.successful_evaluations}")
    print(f"   Failed: {evaluation_result.failed_evaluations}")
    
    # Show leaderboard
    leaderboard = evaluator.generate_leaderboard(evaluation_result)
    print(f"\n🏆 Results:")
    for ranking in leaderboard.rankings:
        status = "✅" if ranking.overall_score >= 0.7 else "❌"
        print(f"   {ranking.agent_name}: {ranking.overall_score:.3f} {status}")


if __name__ == "__main__":
    print("Choose an example to run:")
    print("1. Async evaluation (recommended)")
    print("2. Sync evaluation (simpler)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(main())
    elif choice == "2":
        run_sync_example()
    else:
        print("Invalid choice. Running async example...")
        asyncio.run(main())
