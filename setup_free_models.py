#!/usr/bin/env python3
"""
Setup script for using free models with the Agentic Evaluation Framework
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_ollama():
    """Check if Ollama is installed and running"""
    print("🦙 Checking Ollama...")
    
    try:
        # Check if Ollama is running
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            models = json.loads(result.stdout).get("models", [])
            print(f"✅ Ollama is running with {len(models)} models")
            for model in models[:3]:
                print(f"   📦 {model.get('name', 'Unknown')}")
            return True
        else:
            print("❌ Ollama is not running")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        print("❌ Ollama is not installed or not running")
        return False

def install_ollama():
    """Install Ollama"""
    print("🦙 Installing Ollama...")
    
    try:
        # Download and install Ollama
        subprocess.run([
            "curl", "-fsSL", "https://ollama.ai/install.sh"
        ], check=True)
        
        print("✅ Ollama installed successfully")
        print("   💡 Run 'ollama serve' to start the service")
        print("   💡 Then run 'ollama pull llama2:7b' to download a model")
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Failed to install Ollama")
        print("   💡 Please install manually from https://ollama.ai/")
        return False

def check_huggingface():
    """Check if Hugging Face is available"""
    print("🤗 Checking Hugging Face...")
    
    try:
        import transformers
        print(f"✅ Transformers library available (version: {transformers.__version__})")
        return True
    except ImportError:
        print("❌ Transformers library not available")
        return False

def install_huggingface():
    """Install Hugging Face transformers"""
    print("🤗 Installing Hugging Face transformers...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "transformers", "torch"
        ], check=True)
        
        print("✅ Hugging Face transformers installed successfully")
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Failed to install Hugging Face transformers")
        return False

def create_test_config():
    """Create a test configuration file"""
    print("📝 Creating test configuration...")
    
    config = {
        "free_models": {
            "ollama": {
                "enabled": True,
                "models": [
                    "llama2:7b",
                    "mistral:7b",
                    "codellama:7b",
                    "phi:3b"
                ],
                "api_url": "http://localhost:11434/api/generate"
            },
            "huggingface": {
                "enabled": True,
                "models": [
                    "distilgpt2",
                    "microsoft/DialoGPT-medium",
                    "gpt2"
                ]
            },
            "mock": {
                "enabled": True,
                "description": "Mock responses for testing without external APIs"
            }
        },
        "evaluation": {
            "max_agents": 50,
            "batch_size": 5,
            "max_concurrent": 10,
            "timeout_seconds": 300,
            "include_explanations": True
        },
        "domains": [
            "general",
            "qa", 
            "summarization",
            "reasoning",
            "conversation",
            "code_generation"
        ]
    }
    
    with open("agentic_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Test configuration created: agentic_config.json")
    return True

def create_demo_script():
    """Create a demo script for testing"""
    print("📝 Creating demo script...")
    
    demo_script = '''#!/usr/bin/env python3
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
    print("\\n🧪 Testing framework components...")
    
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
        
        print("\\n🎉 Demo completed successfully!")
        print("\\n📝 Next Steps:")
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
'''
    
    with open("demo_agentic.py", "w") as f:
        f.write(demo_script)
    
    # Make it executable
    os.chmod("demo_agentic.py", 0o755)
    
    print("✅ Demo script created: demo_agentic.py")
    return True

def main():
    """Main setup function"""
    print("🚀 Agentic Evaluation Framework - Free Models Setup")
    print("=" * 60)
    
    # Check current status
    ollama_available = check_ollama()
    huggingface_available = check_huggingface()
    
    print(f"\\n📊 Current Status:")
    print(f"   🦙 Ollama: {'✅ Available' if ollama_available else '❌ Not available'}")
    print(f"   🤗 Hugging Face: {'✅ Available' if huggingface_available else '❌ Not available'}")
    
    # Setup options
    print(f"\\n🔧 Setup Options:")
    print(f"   1. Install Ollama for local models")
    print(f"   2. Install Hugging Face for cloud models")
    print(f"   3. Use mock models for testing")
    print(f"   4. Create configuration and demo")
    
    # Create configuration and demo
    create_test_config()
    create_demo_script()
    
    # Installation recommendations
    print(f"\\n💡 Recommendations:")
    
    if not ollama_available:
        print(f"   🦙 Install Ollama for local testing:")
        print(f"      curl -fsSL https://ollama.ai/install.sh | sh")
        print(f"      ollama serve")
        print(f"      ollama pull llama2:7b")
    
    if not huggingface_available:
        print(f"   🤗 Install Hugging Face for cloud testing:")
        print(f"      pip install transformers torch")
    
    print(f"   🧪 Test with mock models:")
    print(f"      python test_agentic_standalone_final.py")
    
    print(f"   🎬 Run demo:")
    print(f"      python demo_agentic.py")
    
    print(f"\\n🎉 Setup complete!")
    print(f"   The framework is ready to use with free models.")
    print(f"   Check the created files:")
    print(f"   • agentic_config.json - Configuration")
    print(f"   • demo_agentic.py - Demo script")

if __name__ == "__main__":
    main()
