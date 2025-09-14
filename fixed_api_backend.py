#!/usr/bin/env python3
"""
FIXED Agentic Evaluation API Backend
====================================

This fixed version addresses the poor scoring issues by:
1. Integrating improved mock agents with realistic score variations
2. Properly implementing metric calculations
3. Ensuring proper response format with metric_scores
4. Adding debugging and validation
"""

import os
import sys
import json
import uuid
import time
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Add deepeval to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Import improved mock agents
from fixed_mock_agents import (
    ImprovedMockHighQualityAgent,
    ImprovedMockAverageAgent, 
    ImprovedMockPoorAgent,
    MockMetric
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS FOR API
# ============================================================================

class AgentConfig(BaseModel):
    """Configuration for an agent"""
    name: str
    type: str = Field(..., description="Type: 'mock_high', 'mock_average', 'mock_poor'")
    model_name: Optional[str] = Field(None, description="For real models")
    domain: str = Field(default="general", description="Evaluation domain")

class CustomTestCase(BaseModel):
    """Custom test case from frontend"""
    test_case_id: int
    prompt: str
    reference: str
    context: str = Field(default="", description="Additional context for the prompt")
    domain: str = Field(default="general", description="Domain for this test case")

class EvaluationRequest(BaseModel):
    """Request model for evaluation"""
    agents: List[AgentConfig]
    test_cases: Optional[List[CustomTestCase]] = Field(None, description="Custom test cases from frontend")
    batch_processing: bool = Field(default=True, description="Enable batch processing")
    evaluation_id: Optional[str] = Field(default=None, description="Custom evaluation ID")

class EvaluationResponse(BaseModel):
    """Response model for evaluation results"""
    evaluation_id: str
    status: str
    message: str
    results_url: Optional[str] = None
    estimated_time: Optional[float] = None

class AgentInfo(BaseModel):
    """Agent information model"""
    name: str
    type: str
    domain: str
    available: bool = True

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    groq_api_key_configured: bool
    version: str = "2.0.0-fixed"

# ============================================================================
# ENHANCED EVALUATION MANAGER
# ============================================================================

class FixedEvaluationManager:
    """Enhanced evaluation manager with proper metric calculations"""
    
    def __init__(self):
        self.evaluations: Dict[str, Dict[str, Any]] = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.metrics = [
            MockMetric("instruction_following", 0.7),
            MockMetric("coherence_accuracy", 0.7), 
            MockMetric("hallucination_detection", 0.7),
            MockMetric("relevance_quality", 0.7)
        ]
    
    async def initialize(self):
        """Initialize the evaluation system"""
        try:
            logger.info("✅ Fixed evaluation system initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize: {e}")
            return False
    
    def create_evaluation_id(self) -> str:
        """Generate unique evaluation ID"""
        return f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    def get_evaluation_status(self, evaluation_id: str) -> Dict[str, Any]:
        """Get evaluation status"""
        return self.evaluations.get(evaluation_id, {"status": "not_found"})
    
    def start_evaluation(self, evaluation_id: str, request: EvaluationRequest) -> Dict[str, Any]:
        """Start evaluation in background"""
        self.evaluations[evaluation_id] = {
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "request": request.dict(),
            "progress": 0,
            "results": None,
            "error": None
        }
        
        # Submit to thread pool
        future = self.executor.submit(self._run_evaluation, evaluation_id, request)
        self.evaluations[evaluation_id]["future"] = future
        
        return self.evaluations[evaluation_id]
    
    def _run_evaluation(self, evaluation_id: str, request: EvaluationRequest):
        """Run evaluation in background thread"""
        try:
            logger.info(f"🚀 Starting fixed evaluation {evaluation_id}")
            
            # Update status
            self.evaluations[evaluation_id]["status"] = "processing"
            self.evaluations[evaluation_id]["progress"] = 10
            
            # Create agents
            logger.info("Creating agents...")
            agents = []
            for agent_config in request.agents:
                agent = self._create_agent(agent_config)
                agents.append((agent, agent_config))
            
            self.evaluations[evaluation_id]["progress"] = 30
            
            # Get test cases
            if request.test_cases:
                test_cases = request.test_cases
            else:
                # Default test cases if none provided
                test_cases = self._get_default_test_cases()
            
            logger.info(f"Running evaluation on {len(agents)} agents with {len(test_cases)} test cases")
            self.evaluations[evaluation_id]["progress"] = 50
            
            # Run evaluation for each agent
            all_responses = []
            for i, (agent, agent_config) in enumerate(agents):
                logger.info(f"Evaluating agent {i+1}/{len(agents)}: {agent_config.name}")
                
                for test_case in test_cases:
                    # Generate response with context
                    response = agent.generate(test_case.prompt, test_case.context)
                    
                    # Calculate metric scores
                    metric_scores = {}
                    for metric in self.metrics:
                        result = metric.evaluate(
                            test_case.prompt,
                            response,
                            test_case.reference,
                            test_case.context
                        )
                        metric_scores[metric.name] = {
                            "score": result["score"],
                            "success": result["success"],
                            "reason": result["reasoning"]
                        }
                    
                    # Create response entry
                    response_entry = {
                        "agent": agent_config.name,
                        "domain": test_case.domain,
                        "prompt": test_case.prompt,
                        "response": response,
                        "reference": test_case.reference,
                        "context": test_case.context,
                        "test_case_id": test_case.test_case_id,
                        "metric_scores": metric_scores,
                        "timestamp": datetime.now().isoformat()
                    }
                    all_responses.append(response_entry)
                
                # Update progress
                progress = 50 + (40 * (i + 1) / len(agents))
                self.evaluations[evaluation_id]["progress"] = int(progress)
            
            # Save results
            results = {
                "evaluation_id": evaluation_id,
                "total_responses": len(all_responses),
                "agents_evaluated": len(agents),
                "test_cases_count": len(test_cases),
                "responses": all_responses,
                "summary": self._generate_summary(all_responses),
                "timestamp": datetime.now().isoformat()
            }
            
            # Update evaluation status
            self.evaluations[evaluation_id].update({
                "status": "completed",
                "progress": 100,
                "results": results,
                "end_time": datetime.now().isoformat()
            })
            
            # Save to file
            filename = f"eval_{evaluation_id}_responses.jsonl"
            self._save_responses_jsonl(all_responses, filename)
            
            logger.info(f"✅ Evaluation {evaluation_id} completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Evaluation {evaluation_id} failed: {e}")
            self.evaluations[evaluation_id].update({
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now().isoformat()
            })
    
    def _create_agent(self, config: AgentConfig):
        """Create agent based on configuration"""
        if config.type == "mock_high":
            return ImprovedMockHighQualityAgent(config.name)
        elif config.type == "mock_average":
            return ImprovedMockAverageAgent(config.name)
        elif config.type == "mock_poor":
            return ImprovedMockPoorAgent(config.name)
        else:
            raise ValueError(f"Unknown agent type: {config.type}")
    
    def _get_default_test_cases(self) -> List[CustomTestCase]:
        """Get default test cases if none provided"""
        return [
            CustomTestCase(
                test_case_id=1,
                prompt="What is 2 + 2? Answer with a single number.",
                reference="4",
                context="",
                domain="math"
            ),
            CustomTestCase(
                test_case_id=2,
                prompt="Who wrote 'Pride and Prejudice'?",
                reference="Jane Austen",
                context="Context passage: Pride and Prejudice is a novel by Jane Austen, published in 1813.",
                domain="qa-rag"
            ),
            CustomTestCase(
                test_case_id=3,
                prompt="List three benefits of unit testing. Use bullet points only.",
                reference="- Catches regressions\n- Documents behavior\n- Enables refactoring",
                context="",
                domain="instruction-following"
            ),
            CustomTestCase(
                test_case_id=4,
                prompt="Summarize the following in one sentence.",
                reference="Cats are small, agile and independent pets.",
                context="Cats are small carnivorous mammals. They are popular pets and known for agility and independence.",
                domain="summarization"
            ),
            CustomTestCase(
                test_case_id=5,
                prompt="When is Alice's birthday? If unknown, say you don't know.",
                reference="I don't know.",
                context="",
                domain="assumption-control"
            )
        ]
    
    def _generate_summary(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate evaluation summary"""
        if not responses:
            return {}
        
        # Calculate averages by agent
        agent_scores = {}
        for response in responses:
            agent = response["agent"]
            if agent not in agent_scores:
                agent_scores[agent] = []
            
            # Average score across all metrics for this response
            metric_scores = response.get("metric_scores", {})
            if metric_scores:
                avg_score = sum(m["score"] for m in metric_scores.values()) / len(metric_scores)
                agent_scores[agent].append(avg_score)
        
        # Calculate final averages
        agent_averages = {}
        for agent, scores in agent_scores.items():
            agent_averages[agent] = {
                "average_score": sum(scores) / len(scores),
                "total_responses": len(scores),
                "scores": scores
            }
        
        return {
            "agent_performance": agent_averages,
            "total_responses": len(responses),
            "evaluation_completed_at": datetime.now().isoformat()
        }
    
    def _save_responses_jsonl(self, responses: List[Dict[str, Any]], filename: str) -> str:
        """Save responses in JSONL format"""
        with open(filename, 'w') as f:
            for response in responses:
                f.write(json.dumps(response) + '\n')
        return filename

# Initialize global manager
evaluation_manager = FixedEvaluationManager()

# ============================================================================
# LIFESPAN EVENT HANDLER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("🚀 Starting FIXED Agentic Evaluation API...")
    success = await evaluation_manager.initialize()
    if not success:
        logger.error("❌ Failed to initialize evaluation system")
    else:
        logger.info("✅ FIXED API ready to serve requests with improved scoring")
    
    yield
    
    # Shutdown (if needed)
    logger.info("🛑 Shutting down FIXED Agentic Evaluation API...")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="FIXED Agentic Evaluation API",
    description="Fixed REST API for AI Agent Evaluation with improved scoring",
    version="2.0.0-fixed",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        groq_api_key_configured=True,  # Always true for mock agents
        version="2.0.0-fixed"
    )

@app.get("/agents", response_model=List[AgentInfo])
async def list_available_agents():
    """List available agent types"""
    agents = [
        AgentInfo(name="Expert AI Agent", type="mock_high", domain="general"),
        AgentInfo(name="Standard AI Agent", type="mock_average", domain="general"),
        AgentInfo(name="Basic AI Agent", type="mock_poor", domain="general"),
    ]
    return agents

@app.post("/evaluate", response_model=EvaluationResponse)
async def start_evaluation(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """Start a new evaluation"""
    try:
        # Generate evaluation ID
        evaluation_id = request.evaluation_id or evaluation_manager.create_evaluation_id()
        
        # Validate request
        if not request.agents:
            raise HTTPException(
                status_code=400,
                detail="At least one agent must be specified"
            )
        
        # Start evaluation
        evaluation_manager.start_evaluation(evaluation_id, request)
        
        return EvaluationResponse(
            evaluation_id=evaluation_id,
            status="started",
            message=f"Evaluation started with {len(request.agents)} agents",
            results_url=f"/results/{evaluation_id}",
            estimated_time=len(request.agents) * 2.0  # Estimate 2 seconds per agent
        )
        
    except Exception as e:
        logger.error(f"Failed to start evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{evaluation_id}")
async def get_evaluation_results(evaluation_id: str):
    """Get evaluation results"""
    try:
        status_info = evaluation_manager.get_evaluation_status(evaluation_id)
        
        if status_info["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        return {
            "evaluation_id": evaluation_id,
            "status": status_info["status"],
            "progress": status_info.get("progress", 0),
            "results": status_info.get("results"),
            "error": status_info.get("error"),
            "start_time": status_info.get("start_time"),
            "end_time": status_info.get("end_time")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{evaluation_id}/responses")
async def get_evaluation_responses(evaluation_id: str):
    """Get evaluation results in responses.jsonl format"""
    try:
        status_info = evaluation_manager.get_evaluation_status(evaluation_id)
        
        if status_info["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        if status_info["status"] == "running":
            return {
                "status": "running",
                "progress": status_info.get("progress", 0),
                "message": "Evaluation in progress..."
            }
        elif status_info["status"] == "failed":
            return {
                "status": "failed",
                "error": status_info.get("error", "Unknown error")
            }
        elif status_info["status"] == "completed":
            results = status_info.get("results", {})
            return {
                "status": "completed",
                "responses": results.get("responses", []),
                "summary": results.get("summary", {}),
                "total_responses": results.get("total_responses", 0)
            }
        else:
            return {
                "status": status_info["status"],
                "message": "Unknown status"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get responses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/results/{evaluation_id}")
async def delete_evaluation(evaluation_id: str):
    """Delete evaluation results"""
    try:
        if evaluation_id in evaluation_manager.evaluations:
            del evaluation_manager.evaluations[evaluation_id]
            return {"message": f"Evaluation {evaluation_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Evaluation not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "FIXED Agentic Evaluation API",
        "version": "2.0.0-fixed",
        "docs": "/docs",
        "health": "/health",
        "improvements": [
            "Fixed mock agent scoring with realistic variations",
            "Proper metric score calculations",
            "Enhanced response format with detailed metrics",
            "Better error handling and validation"
        ],
        "endpoints": {
            "evaluate": "POST /evaluate",
            "agents": "GET /agents", 
            "results": "GET /results/{evaluation_id}",
            "responses": "GET /results/{evaluation_id}/responses"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting FIXED Agentic Evaluation API Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🎯 Fixed scoring with realistic agent variations!")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
