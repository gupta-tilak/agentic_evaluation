#!/usr/bin/env python3
"""
Demo script for testing the Agentic Evaluation Framework with free models
"""

import json
import sys
import os

# Add the deepeval directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deepeval'))

def run_demo():
    """Run the agentic evaluation demo"""
    print("🚀 Agentic Evaluation Framework Demo")
    print("=" * 50)
    
    # Load configuration
    try:
        with open("agentic_config.json", "r") as f:
            config = json.load(f)
        print("✅ Configuration loaded")
    except FileNotFoundError:
        print("❌ Configuration file not found. Run setup_free_models.py first.")
        return False
    
    # Test framework components
    print("\n🧪 Testing framework components...")
    
    try:
        # Test basic functionality
        from deepeval.agentic.types import Agent, AgentResult, EvaluationConfig, DomainType
        from deepeval.agentic.agent_registry import AgentRegistry
        
        # Create configuration
        eval_config = EvaluationConfig(
            max_agents=config["evaluation"]["max_agents"],
            batch_size=config["evaluation"]["batch_size"],
            max_concurrent=config["evaluation"]["max_concurrent"]
        )
        print("✅ Evaluation configuration created")
        
        # Create agent registry
        registry = AgentRegistry()
        print("✅ Agent registry created")
        
        # Register demo agents
        demo_agents = [
            {"name": "Demo Agent 1", "model_name": "mock-model-1", "domain": "general"},
            {"name": "Demo Agent 2", "model_name": "mock-model-2", "domain": "qa"},
            {"name": "Demo Agent 3", "model_name": "mock-model-3", "domain": "reasoning"},
        ]
        
        agent_ids = []
        for agent_data in demo_agents:
            agent_id = registry.register_agent(
                name=agent_data["name"],
                model_name=agent_data["model_name"],
                domain=agent_data["domain"]
            )
            agent_ids.append(agent_id)
        
        print(f"✅ Registered {len(agent_ids)} demo agents")
        
        # Get registry stats
        stats = registry.get_registry_stats()
        print(f"✅ Registry stats: {stats['total_agents']} agents")
        
        print("\n🎉 Demo completed successfully!")
        print("\n📝 Next Steps:")
        print("   1. Set up Ollama: ollama serve && ollama pull llama2:7b")
        print("   2. Install Hugging Face: pip install transformers torch")
        print("   3. Run real evaluations with: python examples/agentic_evaluation_example.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)
