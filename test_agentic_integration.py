#!/usr/bin/env python3
"""
Test script to verify the agentic evaluation framework integration
"""

import sys
import os

# Add the deepeval directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deepeval'))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        from deepeval.agentic import (
            AgenticEvaluator,
            AgentRegistry,
            Agent,
            InstructionFollowing,
            HallucinationDetection,
            AssumptionControl,
            CoherenceAccuracy,
            DomainEvaluator,
            DomainType,
            EvaluationConfig,
            AgenticEvaluationResult,
            AgentResult,
            Leaderboard,
            PerformanceExplanation
        )
        print("✅ All agentic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without API calls"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from deepeval.agentic import AgenticEvaluator, EvaluationConfig, DomainType
        
        # Test configuration
        config = EvaluationConfig(max_agents=10, batch_size=2)
        print("✅ Configuration creation successful")
        
        # Test evaluator initialization
        evaluator = AgenticEvaluator(config=config)
        print("✅ Evaluator initialization successful")
        
        # Test agent registration
        agent_id = evaluator.register_agent(
            name="Test Agent",
            model_name="test-model",
            domain="general"
        )
        print(f"✅ Agent registration successful: {agent_id}")
        
        # Test agent retrieval
        agent = evaluator.agent_registry.get_agent(agent_id)
        if agent and agent.name == "Test Agent":
            print("✅ Agent retrieval successful")
        else:
            print("❌ Agent retrieval failed")
            return False
        
        # Test registry stats
        stats = evaluator.get_agent_registry_stats()
        if stats['total_agents'] == 1:
            print("✅ Registry stats successful")
        else:
            print("❌ Registry stats failed")
            return False
        
        print("✅ All basic functionality tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_dimensions():
    """Test evaluation dimensions"""
    print("\n🧪 Testing evaluation dimensions...")
    
    try:
        from deepeval.agentic import (
            InstructionFollowing,
            HallucinationDetection,
            AssumptionControl,
            CoherenceAccuracy
        )
        
        # Test dimension creation
        dims = [
            InstructionFollowing(threshold=0.7),
            HallucinationDetection(threshold=0.8),
            AssumptionControl(threshold=0.6),
            CoherenceAccuracy(threshold=0.7)
        ]
        
        for dim in dims:
            if dim.name and dim.threshold:
                print(f"✅ {dim.name} dimension created successfully")
            else:
                print(f"❌ {dim.name} dimension creation failed")
                return False
        
        print("✅ All evaluation dimensions created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Dimensions test failed: {e}")
        return False

def test_domain_support():
    """Test domain support"""
    print("\n🧪 Testing domain support...")
    
    try:
        from deepeval.agentic import DomainEvaluator, DomainType
        
        # Test domain evaluator creation
        for domain in DomainType:
            evaluator = DomainEvaluator(domain)
            if evaluator.domain == domain:
                print(f"✅ {domain.value} domain evaluator created")
            else:
                print(f"❌ {domain.value} domain evaluator failed")
                return False
        
        print("✅ All domain evaluators created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Domain support test failed: {e}")
        return False

def test_reporting():
    """Test reporting functionality"""
    print("\n🧪 Testing reporting functionality...")
    
    try:
        from deepeval.agentic import AgenticReporter, AgentResult, AgentRanking, Leaderboard
        from datetime import datetime
        
        # Create mock agent result
        agent_result = AgentResult(
            agent_id="test-agent",
            agent_name="Test Agent",
            scores={"Instruction Following": 0.8, "Hallucination Detection": 0.9},
            overall_score=0.85,
            passed=True,
            reasoning={"Instruction Following": "Good", "Hallucination Detection": "Excellent"},
            evaluation_time=1.5,
            test_cases_processed=5
        )
        
        # Test reporter creation
        reporter = AgenticReporter()
        print("✅ Reporter creation successful")
        
        # Test performance explanation
        explanation = reporter.explain_performance("test-agent", type('obj', (object,), {
            'agent_results': [agent_result],
            'agent_metrics': type('obj', (object,), {
                'total_agents': 1,
                'average_score': 0.85,
                'median_score': 0.85,
                'std_deviation': 0.0,
                'top_performers': [],
                'bottom_performers': [],
                'domain_breakdown': {},
                'performance_distribution': {}
            })()
        })())
        
        if explanation.agent_id == "test-agent":
            print("✅ Performance explanation successful")
        else:
            print("❌ Performance explanation failed")
            return False
        
        print("✅ All reporting tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Reporting test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Agentic Evaluation Framework Integration Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_basic_functionality,
        test_dimensions,
        test_domain_support,
        test_reporting
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The agentic evaluation framework is ready to use.")
        print("\n🚀 Next steps:")
        print("   1. Set OPENAI_API_KEY environment variable")
        print("   2. Run: python examples/agentic_evaluation_example.py")
        print("   3. Start evaluating your agents!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
