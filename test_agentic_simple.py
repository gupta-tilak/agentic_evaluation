#!/usr/bin/env python3
"""
Simple test script for the Agentic Evaluation Framework
Tests all components without requiring external APIs
"""

import sys
import os
import json
from datetime import datetime

# Add the deepeval directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deepeval'))

def test_basic_imports():
    """Test basic imports"""
    print("🧪 Testing basic imports...")
    
    try:
        # Test importing core types
        from deepeval.agentic.types import (
            Agent, AgentResult, AgenticEvaluationResult, EvaluationConfig,
            DomainType, AgentRanking, Leaderboard, PerformanceExplanation
        )
        print("✅ Core types imported successfully")
        
        # Test importing agent registry
        from deepeval.agentic.agent_registry import AgentRegistry
        print("✅ Agent registry imported successfully")
        
        # Test importing dimensions
        from deepeval.agentic.dimensions import (
            InstructionFollowing, HallucinationDetection, AssumptionControl,
            CoherenceAccuracy, DimensionEvaluator
        )
        print("✅ Evaluation dimensions imported successfully")
        
        # Test importing reporting
        from deepeval.agentic.reporting import AgenticReporter
        print("✅ Reporting system imported successfully")
        
        # Test importing domains
        from deepeval.agentic.domains import DomainEvaluator
        print("✅ Domain support imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_agent_registry():
    """Test agent registry functionality"""
    print("\n🧪 Testing agent registry...")
    
    try:
        from deepeval.agentic.agent_registry import AgentRegistry
        from deepeval.agentic.types import DomainType
        
        # Create registry
        registry = AgentRegistry()
        print("✅ Registry created successfully")
        
        # Register test agents
        test_agents = [
            {"name": "Test Agent 1", "model_name": "test-model-1", "domain": "general"},
            {"name": "Test Agent 2", "model_name": "test-model-2", "domain": "qa"},
            {"name": "Test Agent 3", "model_name": "test-model-3", "domain": "reasoning"},
        ]
        
        agent_ids = []
        for agent_data in test_agents:
            agent_id = registry.register_agent(
                name=agent_data["name"],
                model_name=agent_data["model_name"],
                domain=agent_data["domain"]
            )
            agent_ids.append(agent_id)
            print(f"   ✅ Registered: {agent_data['name']} (ID: {agent_id})")
        
        # Test retrieval
        for agent_id in agent_ids:
            agent = registry.get_agent(agent_id)
            if agent:
                print(f"   ✅ Retrieved: {agent.name}")
            else:
                print(f"   ❌ Failed to retrieve agent {agent_id}")
                return False
        
        # Test stats
        stats = registry.get_registry_stats()
        print(f"   ✅ Registry stats: {stats['total_agents']} agents")
        
        # Test domain filtering
        general_agents = registry.get_agents_by_domain(DomainType.GENERAL)
        print(f"   ✅ General domain agents: {len(general_agents)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent registry test failed: {e}")
        return False

def test_evaluation_dimensions():
    """Test evaluation dimensions"""
    print("\n🧪 Testing evaluation dimensions...")
    
    try:
        from deepeval.agentic.dimensions import (
            InstructionFollowing, HallucinationDetection, AssumptionControl,
            CoherenceAccuracy, DimensionEvaluator
        )
        from deepeval.agentic.types import Agent, DomainType
        
        # Create test agent
        test_agent = Agent(
            id="test-agent",
            name="Test Agent",
            model_name="test-model",
            domain=DomainType.GENERAL
        )
        
        # Create dimensions
        dimensions = [
            InstructionFollowing(threshold=0.7),
            HallucinationDetection(threshold=0.8),
            AssumptionControl(threshold=0.6),
            CoherenceAccuracy(threshold=0.7)
        ]
        
        print(f"✅ Created {len(dimensions)} evaluation dimensions")
        
        # Test dimension evaluator
        evaluator = DimensionEvaluator(dimensions)
        print(f"✅ Dimension evaluator created with {len(evaluator.dimensions)} dimensions")
        print(f"   Weights: {evaluator.dimension_weights}")
        
        # Test weighted score calculation
        mock_results = {
            "Instruction Following": type('obj', (object,), {'score': 0.8})(),
            "Hallucination Detection": type('obj', (object,), {'score': 0.9})(),
            "Assumption Control": type('obj', (object,), {'score': 0.7})(),
            "Coherence & Accuracy": type('obj', (object,), {'score': 0.8})()
        }
        
        weighted_score = evaluator.calculate_weighted_score(mock_results)
        print(f"✅ Weighted score calculation: {weighted_score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Evaluation dimensions test failed: {e}")
        return False

def test_domain_support():
    """Test domain support"""
    print("\n🧪 Testing domain support...")
    
    try:
        from deepeval.agentic.domains import DomainEvaluator
        from deepeval.agentic.types import DomainType
        
        # Test all domain types
        for domain in DomainType:
            evaluator = DomainEvaluator(domain)
            print(f"   ✅ {domain.value} domain evaluator created")
            
            # Test domain requirements
            requirements = evaluator.get_domain_requirements()
            print(f"      Description: {requirements['description']}")
            print(f"      Key requirements: {len(requirements['key_requirements'])} items")
        
        print(f"✅ All {len(DomainType)} domain types supported")
        
        return True
        
    except Exception as e:
        print(f"❌ Domain support test failed: {e}")
        return False

def test_reporting_system():
    """Test reporting system"""
    print("\n🧪 Testing reporting system...")
    
    try:
        from deepeval.agentic.reporting import AgenticReporter
        from deepeval.agentic.types import (
            AgentResult, AgentRanking, Leaderboard, PerformanceExplanation
        )
        
        # Create reporter
        reporter = AgenticReporter()
        print("✅ Reporter created successfully")
        
        # Create mock agent results
        mock_results = []
        for i in range(5):
            result = AgentResult(
                agent_id=f"agent-{i}",
                agent_name=f"Test Agent {i+1}",
                scores={
                    "Instruction Following": 0.7 + (i * 0.05),
                    "Hallucination Detection": 0.8 + (i * 0.03),
                    "Assumption Control": 0.6 + (i * 0.04),
                    "Coherence & Accuracy": 0.7 + (i * 0.06)
                },
                overall_score=0.7 + (i * 0.05),
                passed=True,
                reasoning={
                    "Instruction Following": f"Good performance for agent {i+1}",
                    "Hallucination Detection": f"Excellent performance for agent {i+1}",
                    "Assumption Control": f"Fair performance for agent {i+1}",
                    "Coherence & Accuracy": f"Good performance for agent {i+1}"
                },
                evaluation_time=1.0 + (i * 0.1),
                test_cases_processed=5,
                metadata={"test": True, "agent_id": i}
            )
            mock_results.append(result)
        
        print(f"✅ Created {len(mock_results)} mock agent results")
        
        # Test leaderboard generation
        mock_evaluation_result = type('obj', (object,), {
            'agent_results': mock_results,
            'agent_metrics': type('obj', (object,), {
                'total_agents': len(mock_results),
                'average_score': sum(r.overall_score for r in mock_results) / len(mock_results),
                'median_score': sorted([r.overall_score for r in mock_results])[len(mock_results)//2],
                'std_deviation': 0.1,
                'top_performers': [],
                'bottom_performers': [],
                'domain_breakdown': {},
                'performance_distribution': {}
            })()
        })()
        
        leaderboard = reporter.generate_leaderboard(mock_evaluation_result)
        print(f"✅ Leaderboard generated with {len(leaderboard.rankings)} rankings")
        
        # Test performance explanation
        if mock_results:
            explanation = reporter.explain_performance(mock_results[0].agent_id, mock_evaluation_result)
            print(f"✅ Performance explanation generated for {explanation.agent_id}")
            print(f"   Strengths: {len(explanation.strengths)}")
            print(f"   Weaknesses: {len(explanation.weaknesses)}")
            print(f"   Recommendations: {len(explanation.recommendations)}")
        
        # Test export functionality
        json_file = "test_results.json"
        if reporter.export_results(mock_evaluation_result, json_file, "json"):
            print(f"✅ JSON export successful: {json_file}")
        
        csv_file = "test_results.csv"
        if reporter.export_results(mock_evaluation_result, csv_file, "csv"):
            print(f"✅ CSV export successful: {csv_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Reporting system test failed: {e}")
        return False

def test_configuration():
    """Test configuration system"""
    print("\n🧪 Testing configuration system...")
    
    try:
        from deepeval.agentic.types import EvaluationConfig
        
        # Test default configuration
        default_config = EvaluationConfig()
        print(f"✅ Default config created")
        print(f"   Max agents: {default_config.max_agents}")
        print(f"   Batch size: {default_config.batch_size}")
        print(f"   Max concurrent: {default_config.max_concurrent}")
        
        # Test custom configuration
        custom_config = EvaluationConfig(
            max_agents=200,
            batch_size=20,
            max_concurrent=100,
            timeout_seconds=600,
            include_explanations=True,
            strict_mode=True
        )
        print(f"✅ Custom config created")
        print(f"   Max agents: {custom_config.max_agents}")
        print(f"   Batch size: {custom_config.batch_size}")
        print(f"   Strict mode: {custom_config.strict_mode}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def create_demo_workflow():
    """Create a complete demo workflow"""
    print("\n🎬 Creating complete demo workflow...")
    
    try:
        from deepeval.agentic.types import (
            AgenticEvaluator, EvaluationConfig, DomainType
        )
        from deepeval.agentic.agent_registry import AgentRegistry
        from deepeval.agentic.dimensions import (
            InstructionFollowing, HallucinationDetection, AssumptionControl,
            CoherenceAccuracy
        )
        
        # Step 1: Create configuration
        config = EvaluationConfig(
            max_agents=10,
            batch_size=3,
            max_concurrent=5,
            include_explanations=True
        )
        print("✅ Step 1: Configuration created")
        
        # Step 2: Create evaluator
        evaluator = AgenticEvaluator(config=config)
        print("✅ Step 2: Evaluator created")
        
        # Step 3: Register agents
        agents_data = [
            {"name": "Demo Agent 1", "model_name": "demo-model-1", "domain": "general"},
            {"name": "Demo Agent 2", "model_name": "demo-model-2", "domain": "qa"},
            {"name": "Demo Agent 3", "model_name": "demo-model-3", "domain": "reasoning"},
        ]
        
        agent_ids = evaluator.register_agents_batch(agents_data)
        print(f"✅ Step 3: Registered {len(agent_ids)} agents")
        
        # Step 4: Get registry stats
        stats = evaluator.get_agent_registry_stats()
        print(f"✅ Step 4: Registry stats - {stats['total_agents']} agents")
        
        # Step 5: Test domain analysis
        domain_analysis = evaluator.get_domain_analysis(type('obj', (object,), {
            'agent_metrics': type('obj', (object,), {
                'domain_breakdown': {
                    DomainType.GENERAL: {'count': 1, 'average_score': 0.8},
                    DomainType.QA: {'count': 1, 'average_score': 0.85},
                    DomainType.REASONING: {'count': 1, 'average_score': 0.75}
                }
            })()
        })())
        print(f"✅ Step 5: Domain analysis completed")
        
        print("🎉 Complete demo workflow successful!")
        return True
        
    except Exception as e:
        print(f"❌ Demo workflow failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Agentic Evaluation Framework - Simple Testing")
    print("=" * 60)
    print("This script tests the framework without requiring external APIs")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Agent Registry", test_agent_registry),
        ("Evaluation Dimensions", test_evaluation_dimensions),
        ("Domain Support", test_domain_support),
        ("Reporting System", test_reporting_system),
        ("Configuration", test_configuration),
        ("Demo Workflow", create_demo_workflow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = "PASSED" if result else "FAILED"
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = "ERROR"
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    for test_name, result in results.items():
        status_icon = "✅" if result == "PASSED" else "❌" if result == "FAILED" else "⚠️"
        print(f"{status_icon} {test_name}: {result}")
    
    passed = sum(1 for r in results.values() if r == "PASSED")
    total = len(results)
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The agentic evaluation framework is working correctly.")
        print("\n🚀 Framework Status:")
        print("   ✅ Core components functional")
        print("   ✅ Agent management working")
        print("   ✅ Evaluation dimensions ready")
        print("   ✅ Domain support operational")
        print("   ✅ Reporting system functional")
        print("   ✅ Configuration system working")
        print("   ✅ Complete workflow operational")
        
        print("\n📝 Next Steps:")
        print("   1. The framework is ready for use with mock data")
        print("   2. To test with real models, set up Ollama or Hugging Face")
        print("   3. For production use, configure real LLM APIs")
        print("   4. Run the comprehensive example: python examples/agentic_evaluation_example.py")
        
    elif passed > 0:
        print("⚠️ Some tests passed. The framework is partially functional.")
        print("   Check the failed tests above for issues.")
    else:
        print("❌ No tests passed. Please check the setup and dependencies.")
    
    print(f"\n📁 Files created during testing:")
    print(f"   • test_results.json - Mock evaluation results")
    print(f"   • test_results.csv - Mock evaluation results (CSV)")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
