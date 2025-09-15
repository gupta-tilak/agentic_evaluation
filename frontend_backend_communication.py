#!/usr/bin/env python3
"""
Frontend-Backend Communication Example
=====================================

This example demonstrates the complete communication flow between
your frontend and the api_backend.py for agentic evaluation.

FLOW:
1. Frontend selects agents and provides custom test cases
2. Frontend sends POST request to /evaluate
3. Backend processes evaluation using DeepEval + Groq
4. Frontend polls for results
5. Backend returns responses in your required format
"""

import json
import time
import requests
from typing import List, Dict, Any

# ============================================================================
# FRONTEND DATA STRUCTURES (What your frontend will send)
# ============================================================================

class FrontendRequest:
    """Represents the request structure from your frontend"""
    
    def __init__(self):
        # Agents selected by user in frontend
        self.selected_agents = [
            {
                "name": "Expert AI Assistant",
                "type": "mock_high",
                "domain": "general"
            },
            {
                "name": "GPT-2 Model",
                "type": "huggingface", 
                "model_name": "gpt2",
                "domain": "general"
            },
            {
                "name": "Standard Assistant",
                "type": "mock_average",
                "domain": "general"
            }
        ]
        
        # Custom test cases provided by user (your responses.jsonl format)
        self.custom_test_cases = [
            {
                "test_case_id": 1,
                "prompt": "What is 2 + 2? Answer with a single number.",
                "reference": "4",
                "context": "",
                "domain": "math"
            },
            {
                "test_case_id": 2,
                "prompt": "Who wrote 'Pride and Prejudice'?",
                "reference": "Jane Austen",
                "context": "Context passage: Pride and Prejudice is a novel by Jane Austen, published in 1813.",
                "domain": "qa-rag"
            },
            {
                "test_case_id": 3,
                "prompt": "List three benefits of unit testing. Use bullet points only.",
                "reference": "- Catches regressions\n- Documents behavior\n- Enables refactoring",
                "context": "",
                "domain": "instruction-following"
            },
            {
                "test_case_id": 4,
                "prompt": "Answer using only the provided context.",
                "reference": "The 2024 Olympics took place in Paris, France.",
                "context": "The 2024 Paris Olympics took place in Paris, France. Many events were held along the River Seine.",
                "domain": "hallucination"
            },
            {
                "test_case_id": 5,
                "prompt": "Give a one-word synonym for 'quick'.",
                "reference": "fast",
                "context": "",
                "domain": "edge-empty-output"
            }
        ]
    
    def to_api_request(self) -> Dict[str, Any]:
        """Convert to API request format"""
        return {
            "agents": self.selected_agents,
            "test_cases": self.custom_test_cases,
            "batch_processing": True,
            "evaluation_id": f"frontend_eval_{int(time.time())}"
        }

# ============================================================================
# COMMUNICATION FUNCTIONS
# ============================================================================

class AgenticEvaluationClient:
    """Client that handles frontend-backend communication"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url.rstrip('/')
        self.session = requests.Session()
    
    def send_evaluation_request(self, frontend_request: FrontendRequest) -> Dict[str, Any]:
        """Step 1: Send evaluation request from frontend to backend"""
        print("📤 STEP 1: Frontend sending evaluation request to backend...")
        
        api_request = frontend_request.to_api_request()
        
        print(f"   📋 Selected Agents: {len(api_request['agents'])}")
        for agent in api_request['agents']:
            print(f"      - {agent['name']} ({agent['type']})")
        
        print(f"   📝 Custom Test Cases: {len(api_request['test_cases'])}")
        for test in api_request['test_cases']:
            print(f"      - Test {test['test_case_id']}: {test['prompt'][:50]}...")
        
        # Send POST request to backend
        response = self.session.post(
            f"{self.api_base_url}/evaluate",
            json=api_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Evaluation started: {result['evaluation_id']}")
            print(f"   ⏱️  Estimated time: {result.get('estimated_time', 'unknown')} seconds")
            return result
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
            raise Exception(f"Failed to start evaluation: {response.text}")
    
    def poll_for_results(self, evaluation_id: str, timeout: int = 600) -> Dict[str, Any]:
        """Step 2: Poll backend for evaluation results"""
        print(f"\n⏳ STEP 2: Polling backend for results (evaluation_id: {evaluation_id})...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check evaluation status
            response = self.session.get(f"{self.api_base_url}/results/{evaluation_id}/responses")
            
            if response.status_code == 200:
                result = response.json()
                
                if result["status"] == "completed":
                    print(f"   ✅ Evaluation completed!")
                    print(f"   📊 Total responses: {result['total_responses']}")
                    return result
                elif result["status"] == "failed":
                    print(f"   ❌ Evaluation failed: {result.get('message', 'Unknown error')}")
                    raise Exception(f"Evaluation failed: {result.get('message', 'Unknown error')}")
                else:
                    # Still in progress
                    progress = result.get("progress", 0)
                    print(f"   🔄 Status: {result['status']}, Progress: {progress}%")
                    time.sleep(5)  # Wait 5 seconds before next poll
            else:
                print(f"   ❌ Error checking status: {response.status_code}")
                time.sleep(5)
        
        raise TimeoutError(f"Evaluation did not complete within {timeout} seconds")
    
    def process_backend_response(self, backend_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Step 3: Process backend response for frontend display"""
        print(f"\n📊 STEP 3: Processing backend response for frontend...")
        
        responses = backend_results["responses"]
        
        print(f"   📈 Processing {len(responses)} agent responses...")
        
        # Group responses by agent for frontend display
        agents_results = {}
        for response in responses:
            agent_name = response["agent"]
            if agent_name not in agents_results:
                agents_results[agent_name] = []
            agents_results[agent_name].append(response)
        
        # Calculate summary statistics for frontend
        summary_stats = {
            "total_agents": len(agents_results),
            "total_responses": len(responses),
            "average_scores": self._calculate_average_scores(responses),
            "agent_rankings": self._rank_agents(agents_results)
        }
        
        print(f"   📊 Summary calculated:")
        print(f"      - Total Agents: {summary_stats['total_agents']}")
        print(f"      - Total Responses: {summary_stats['total_responses']}")
        print(f"      - Top Agent: {summary_stats['agent_rankings'][0]['agent']}")
        
        return {
            "responses": responses,
            "summary": summary_stats,
            "agents_results": agents_results
        }
    
    def _calculate_average_scores(self, responses: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average scores across all responses"""
        metrics = ["instruction_following", "coherence_accuracy", "hallucination_detection", "relevance_quality"]
        totals = {metric: 0.0 for metric in metrics}
        counts = {metric: 0 for metric in metrics}
        
        for response in responses:
            metric_scores = response.get("metric_scores", {})
            for metric in metrics:
                if metric in metric_scores:
                    totals[metric] += metric_scores[metric]
                    counts[metric] += 1
        
        return {metric: totals[metric] / counts[metric] if counts[metric] > 0 else 0.0 
                for metric in metrics}
    
    def _rank_agents(self, agents_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Rank agents by average performance"""
        agent_scores = []
        
        for agent_name, agent_responses in agents_results.items():
            avg_scores = self._calculate_average_scores(agent_responses)
            overall_score = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0.0
            
            agent_scores.append({
                "agent": agent_name,
                "overall_score": overall_score,
                "avg_scores": avg_scores,
                "total_responses": len(agent_responses)
            })
        
        # Sort by overall score (descending)
        agent_scores.sort(key=lambda x: x["overall_score"], reverse=True)
        return agent_scores

# ============================================================================
# COMPLETE DEMO
# ============================================================================

def main():
    """Complete demo of frontend-backend communication"""
    print("🚀 FRONTEND-BACKEND COMMUNICATION DEMO")
    print("=" * 60)
    print("This demonstrates the complete flow:")
    print("Frontend → POST /evaluate → Backend Processing → GET /results → Frontend")
    print("=" * 60)
    
    # Initialize client
    client = AgenticEvaluationClient()
    
    # Check if backend is running
    try:
        health = client.session.get(f"{client.api_base_url}/health", timeout=5)
        if health.status_code != 200:
            print(f"❌ Backend not accessible. Start the API server first:")
            print(f"   cd /Users/guptatilak/Desktop/deepeval")
            print(f"   python3 api_backend.py")
            return
        print(f"✅ Backend is running at {client.api_base_url}")
    except requests.exceptions.RequestException:
        print(f"❌ Backend not accessible. Start the API server first:")
        print(f"   cd /Users/guptatilak/Desktop/deepeval")
        print(f"   python3 api_backend.py")
        return
    
    try:
        # Step 1: Create frontend request (this is what your frontend will send)
        frontend_request = FrontendRequest()
        
        # Step 2: Send to backend
        evaluation_result = client.send_evaluation_request(frontend_request)
        evaluation_id = evaluation_result["evaluation_id"]
        
        # Step 3: Poll for results
        backend_results = client.poll_for_results(evaluation_id)
        
        # Step 4: Process for frontend display
        frontend_data = client.process_backend_response(backend_results)
        
        # Step 5: Display results (this is what your frontend will receive)
        print(f"\n✨ STEP 4: Final results ready for frontend display!")
        print("=" * 60)
        
        # Show summary
        summary = frontend_data["summary"]
        print(f"📊 EVALUATION SUMMARY:")
        print(f"   • Total Agents Evaluated: {summary['total_agents']}")
        print(f"   • Total Responses Generated: {summary['total_responses']}")
        print(f"   • Average Instruction Following: {summary['average_scores']['instruction_following']:.2f}")
        print(f"   • Average Coherence: {summary['average_scores']['coherence_accuracy']:.2f}")
        
        # Show top 3 agents
        print(f"\n🏆 TOP PERFORMING AGENTS:")
        for i, agent in enumerate(summary["agent_rankings"][:3], 1):
            print(f"   {i}. {agent['agent']}: {agent['overall_score']:.2f}")
        
        # Show sample responses (first 3)
        print(f"\n📝 SAMPLE RESPONSES (first 3):")
        for i, response in enumerate(frontend_data["responses"][:3], 1):
            print(f"\n   Response {i}:")
            print(f"      Agent: {response['agent']}")
            print(f"      Prompt: {response['prompt'][:80]}...")
            print(f"      Response: {response['response'][:80]}...")
            print(f"      Reference: {response['reference'][:80]}...")
            print(f"      Scores: {response['metric_scores']}")
        
        # Save for frontend reference
        output_file = f"frontend_results_{evaluation_id}.json"
        with open(output_file, 'w') as f:
            json.dump(frontend_data, f, indent=2)
        
        print(f"\n💾 Complete results saved to: {output_file}")
        print(f"🎯 This JSON structure is ready for your frontend to consume!")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")

if __name__ == "__main__":
    main()

# ============================================================================
# FRONTEND INTEGRATION EXAMPLES
# ============================================================================

"""
JAVASCRIPT/REACT EXAMPLE:
=========================

// Frontend component example
async function runEvaluation() {
  // Step 1: Prepare request (from user selections)
  const evaluationRequest = {
    agents: [
      {name: "Expert AI", type: "mock_high", domain: "general"},
      {name: "GPT-2", type: "huggingface", model_name: "gpt2", domain: "general"}
    ],
    test_cases: [
      {
        test_case_id: 1,
        prompt: "What is artificial intelligence?",
        reference: "AI is a field of computer science...",
        context: "Context about AI",
        domain: "general"
      }
    ],
    batch_processing: true
  };

  // Step 2: Send to backend
  const startResponse = await fetch('/api/evaluate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(evaluationRequest)
  });
  
  const {evaluation_id} = await startResponse.json();
  
  // Step 3: Poll for results
  let completed = false;
  while (!completed) {
    const resultResponse = await fetch(`/api/results/${evaluation_id}/responses`);
    const result = await resultResponse.json();
    
    if (result.status === 'completed') {
      completed = true;
      // Step 4: Display results in frontend
      displayResults(result.responses);
    } else {
      // Show progress
      updateProgress(result.progress);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
}

CURL EXAMPLES:
==============

# Step 1: Start evaluation
curl -X POST "http://localhost:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "agents": [
      {"name": "Expert AI", "type": "mock_high", "domain": "general"}
    ],
    "test_cases": [
      {
        "test_case_id": 1,
        "prompt": "What is 2+2?",
        "reference": "4",
        "context": "",
        "domain": "math"
      }
    ]
  }'

# Step 2: Check results
curl "http://localhost:8000/results/{evaluation_id}/responses"
"""
