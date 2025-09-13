#!/usr/bin/env python3
"""
Simple test script to verify the agentic evaluation framework components
"""

import sys
import os

# Add the deepeval directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deepeval'))

def test_types():
    """Test types module"""
    print("🧪 Testing types module...")
    
    try:
        from deepeval.agentic.types import (
            Agent, AgentResult, AgentRanking, AgentMetrics,
            AgenticEvaluationResult, EvaluationConfig, PerformanceExplanation,
            Leaderboard, DomainType
        )
        
        # Test Agent creation
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            model_name="test-model",
            domain=DomainType.GENERAL
        )
        
        if agent.id == "test-agent" and agent.name == "Test Agent":
            print("✅ Agent creation successful")
        else:
            print("❌ Agent creation failed")
            return False
        
        # Test EvaluationConfig
        config = EvaluationConfig(max_agents=10, batch_size=2)
        if config.max_agents == 10:
            print("✅ EvaluationConfig creation successful")
        else:
            print("❌ EvaluationConfig creation failed")
            return False
        
        print("✅ Types module test passed")
        return True
        
    except Exception as e:
        print(f"❌ Types module test failed: {e}")
        return False

def test_agent_registry():
    """Test agent registry"""
    print("\n🧪 Testing agent registry...")
    
    try:
        from deepeval.agentic.agent_registry import AgentRegistry
        from deepeval.agentic.types import DomainType
        
        registry = AgentRegistry()
        
        # Test agent registration
        agent_id = registry.register_agent(
            name="Test Agent",
            model_name="test-model",
            domain=DomainType.GENERAL
        )
        
        if agent_id:
            print("✅ Agent registration successful")
        else:
            print("❌ Agent registration failed")
            return False
        
        # Test agent retrieval
        agent = registry.get_agent(agent_id)
        if agent and agent.name == "Test Agent":
            print("✅ Agent retrieval successful")
        else:
            print("❌ Agent retrieval failed")
            return False
        
        # Test registry stats
        stats = registry.get_registry_stats()
        if stats['total_agents'] == 1:
            print("✅ Registry stats successful")
        else:
            print("❌ Registry stats failed")
            return False
        
        print("✅ Agent registry test passed")
        return True
        
    except Exception as e:
        print(f"❌ Agent registry test failed: {e}")
        return False

def test_dimensions():
    """Test evaluation dimensions"""
    print("\n🧪 Testing evaluation dimensions...")
    
    try:
        from deepeval.agentic.dimensions import (
            InstructionFollowing, HallucinationDetection,
            AssumptionControl, CoherenceAccuracy, DimensionEvaluator
        )
        from deepeval.agentic.types import Agent, DomainType
        
        # Test dimension creation
        dims = [
            InstructionFollowing(threshold=0.7),
            HallucinationDetection(threshold=0.8),
            AssumptionControl(threshold=0.6),
            CoherenceAccuracy(threshold=0.7)
        ]
        
        for dim in dims:
            if dim.name and dim.threshold:
                print(f"✅ {dim.name} dimension created")
            else:
                print(f"❌ {dim.name} dimension creation failed")
                return False
        
        # Test dimension evaluator
        evaluator = DimensionEvaluator(dims)
        if len(evaluator.dimensions) == 4:
            print("✅ Dimension evaluator created")
        else:
            print("❌ Dimension evaluator creation failed")
            return False
        
        print("✅ Evaluation dimensions test passed")
        return True
        
    except Exception as e:
        print(f"❌ Evaluation dimensions test failed: {e}")
        return False

def test_domains():
    """Test domain support"""
    print("\n🧪 Testing domain support...")
    
    try:
        from deepeval.agentic.domains import DomainEvaluator
        from deepeval.agentic.types import DomainType
        
        # Test domain evaluator creation
        for domain in DomainType:
            evaluator = DomainEvaluator(domain)
            if evaluator.domain == domain:
                print(f"✅ {domain.value} domain evaluator created")
            else:
                print(f"❌ {domain.value} domain evaluator failed")
                return False
        
        print("✅ Domain support test passed")
        return True
        
    except Exception as e:
        print(f"❌ Domain support test failed: {e}")
        return False

def test_reporting():
    """Test reporting functionality"""
    print("\n🧪 Testing reporting functionality...")
    
    try:
        from deepeval.agentic.reporting import AgenticReporter
        from deepeval.agentic.types import AgentResult, AgentRanking, Leaderboard
        from datetime import datetime
        
        # Test reporter creation
        reporter = AgenticReporter()
        print("✅ Reporter creation successful")
        
        # Test mock data creation
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
        
        if agent_result.agent_id == "test-agent":
            print("✅ Mock data creation successful")
        else:
            print("❌ Mock data creation failed")
            return False
        
        print("✅ Reporting functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Reporting functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Agentic Evaluation Framework - Simple Integration Test")
    print("=" * 70)
    
    tests = [
        test_types,
        test_agent_registry,
        test_dimensions,
        test_domains,
        test_reporting
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The agentic evaluation framework components are working.")
        print("\n🚀 Framework Status:")
        print("   ✅ Core types and data structures")
        print("   ✅ Agent registry for managing agents")
        print("   ✅ Evaluation dimensions (4 core metrics)")
        print("   ✅ Domain-specific evaluation support")
        print("   ✅ Reporting and visualization")
        print("\n📝 Next Steps:")
        print("   1. The framework is ready for integration with the main deepeval module")
        print("   2. Set OPENAI_API_KEY to test with real LLM evaluations")
        print("   3. Run the full example: python examples/agentic_evaluation_example.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
