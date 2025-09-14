#!/usr/bin/env python3
"""
FastAPI Backend for Agentic Evaluation System
==============================================

🚀 OVERVIEW:
This FastAPI backend provides REST API endpoints for the agentic evaluation system.
It connects your frontend to the existing evaluation infrastructure and provides
standardized response formats.

✅ FEATURES:
- RESTful API endpoints for evaluation
- Compatible with existing evaluation system
- Standardized JSON responses
- Error handling and validation
- CORS support for frontend integration
- Real-time evaluation progress
- Batch processing support

🔧 ENDPOINTS:
- POST /evaluate - Run evaluation on agents
- GET /agents - List available agents
- GET /results/{evaluation_id} - Get evaluation results
- GET /health - Health check

🚀 QUICK START:
1. Install: pip install fastapi uvicorn
2. Set GROQ_API_KEY environment variable
3. Run: uvicorn api_backend:app --reload --port 8000
4. Access: http://localhost:8000/docs for API documentation
"""

import os
import sys
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import logging

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Add deepeval to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Import evaluation system
from complete_agentic_groq_evaluation import (
    AgenticGroqEvaluator,
    setup_groq_model,
    create_demo_agents,
    MockHighQualityAgent,
    MockAverageAgent,
    MockPoorAgent,
    HuggingFaceAgent,
    save_results
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
    type: str = Field(..., description="Type: 'mock_high', 'mock_average', 'mock_poor', 'huggingface'")
    model_name: Optional[str] = Field(None, description="For HuggingFace agents")
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
    version: str = "1.0.0"

# ============================================================================
# GLOBAL STATE MANAGEMENT
# ============================================================================

class EvaluationManager:
    """Manages ongoing evaluations"""
    
    def __init__(self):
        self.evaluations: Dict[str, Dict[str, Any]] = {}
        self.groq_model = None
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def initialize(self):
        """Initialize the evaluation system"""
        try:
            self.groq_model = setup_groq_model()
            if not self.groq_model:
                logger.error("Failed to initialize Groq model")
                return False
            logger.info("✅ Groq model initialized successfully")
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
            logger.info(f"🚀 Starting evaluation {evaluation_id}")
            
            # Update status
            self.evaluations[evaluation_id]["status"] = "initializing"
            self.evaluations[evaluation_id]["progress"] = 10
            
            # Initialize evaluator
            evaluator = AgenticGroqEvaluator(self.groq_model, enable_batch_processing=request.batch_processing)
            
            # Register agents
            self.evaluations[evaluation_id]["status"] = "registering_agents"
            self.evaluations[evaluation_id]["progress"] = 20
            
            agents = []
            for agent_config in request.agents:
                try:
                    agent = self._create_agent(agent_config)
                    agents.append(agent)
                    evaluator.register_agent(agent, domain=agent_config.domain)
                except Exception as e:
                    logger.error(f"Failed to create agent {agent_config.name}: {e}")
                    continue
            
            # Create test cases
            self.evaluations[evaluation_id]["status"] = "creating_test_cases"
            self.evaluations[evaluation_id]["progress"] = 30
            
            if request.test_cases:
                # Convert custom test cases from frontend to LLMTestCase objects
                test_cases = self._convert_custom_test_cases(request.test_cases)
            else:
                # Use default test cases
                test_cases = evaluator.create_test_cases()
            
            # Run evaluation
            self.evaluations[evaluation_id]["status"] = "evaluating"
            self.evaluations[evaluation_id]["progress"] = 40
            
            def progress_callback(progress):
                if evaluation_id in self.evaluations:
                    # Calculate progress percentage from BatchProgress object
                    if progress.total_agents > 0:
                        progress_percentage = (progress.processed_agents / progress.total_agents) * 100
                    else:
                        progress_percentage = 0
                    self.evaluations[evaluation_id]["progress"] = 40 + (progress_percentage * 0.5)
            
            evaluator.set_progress_callback(progress_callback)
            results = evaluator.evaluate_agents(test_cases)
            
            # Convert results to responses.jsonl format
            self.evaluations[evaluation_id]["status"] = "formatting_results"
            self.evaluations[evaluation_id]["progress"] = 90
            
            formatted_results = self._format_results_to_responses(results)
            
            # Save results
            results_filename = save_results(results, f"{evaluation_id}.json")
            responses_filename = self._save_responses_jsonl(formatted_results, f"{evaluation_id}_responses.jsonl")
            
            # Update final status
            self.evaluations[evaluation_id].update({
                "status": "completed",
                "progress": 100,
                "end_time": datetime.now().isoformat(),
                "results": results,
                "formatted_results": formatted_results,
                "results_file": results_filename,
                "responses_file": responses_filename
            })
            
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
            return MockHighQualityAgent(config.name)
        elif config.type == "mock_average":
            return MockAverageAgent(config.name)
        elif config.type == "mock_poor":
            return MockPoorAgent(config.name)
        elif config.type == "huggingface":
            if not config.model_name:
                raise ValueError("model_name required for HuggingFace agents")
            return HuggingFaceAgent(config.model_name)
        else:
            raise ValueError(f"Unknown agent type: {config.type}")
    
    def _convert_custom_test_cases(self, custom_test_cases: List[CustomTestCase]):
        """Convert custom test cases from frontend to LLMTestCase objects"""
        from deepeval.test_case import LLMTestCase
        
        test_cases = []
        for custom_test in custom_test_cases:
            # Create LLMTestCase object with frontend data
            test_case = LLMTestCase(
                input=custom_test.prompt,
                actual_output="",  # Will be filled by agent during evaluation
                expected_output=custom_test.reference,
                context=[custom_test.context] if custom_test.context else []
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def _format_results_to_responses(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert evaluation results to responses.jsonl format"""
        responses = []
        
        for agent_result in results.get("agent_results", []):
            agent_name = agent_result["agent_name"]
            domain = agent_result["domain"]
            
            for test_result in agent_result.get("test_results", []):
                response_entry = {
                    "agent": agent_name,
                    "domain": domain,
                    "prompt": test_result["input"],
                    "response": test_result["actual_output"],
                    "reference": test_result["expected_output"],
                    "context": " ".join(test_result.get("context", [])),
                    "evaluation_id": results["evaluation_summary"]["timestamp"],
                    "test_case_id": test_result["test_case_id"],
                    "metric_scores": test_result.get("metric_scores", {}),
                    "timestamp": datetime.now().isoformat()
                }
                responses.append(response_entry)
        
        return responses
    
    def _save_responses_jsonl(self, responses: List[Dict[str, Any]], filename: str) -> str:
        """Save responses in JSONL format"""
        with open(filename, 'w') as f:
            for response in responses:
                f.write(json.dumps(response) + '\n')
        return filename

# Initialize global manager
evaluation_manager = EvaluationManager()

# ============================================================================
# LIFESPAN EVENT HANDLER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("🚀 Starting Agentic Evaluation API...")
    success = await evaluation_manager.initialize()
    if not success:
        logger.error("❌ Failed to initialize evaluation system")
    else:
        logger.info("✅ API ready to serve requests")
    
    yield
    
    # Shutdown (if needed)
    logger.info("🛑 Shutting down Agentic Evaluation API...")

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Agentic Evaluation API",
    description="REST API for AI Agent Evaluation using Groq",
    version="1.0.0",
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
    groq_configured = bool(os.getenv("GROQ_API_KEY"))
    
    return HealthResponse(
        status="healthy" if groq_configured else "warning",
        timestamp=datetime.now().isoformat(),
        groq_api_key_configured=groq_configured
    )

@app.get("/agents", response_model=List[AgentInfo])
async def list_available_agents():
    """List available agent types"""
    agents = [
        AgentInfo(name="High Quality Mock Agent", type="mock_high", domain="general"),
        AgentInfo(name="Average Quality Mock Agent", type="mock_average", domain="general"),
        AgentInfo(name="Poor Quality Mock Agent", type="mock_poor", domain="general"),
        AgentInfo(name="DistilGPT-2", type="huggingface", domain="general"),
        AgentInfo(name="GPT-2", type="huggingface", domain="general"),
    ]
    return agents

@app.post("/evaluate", response_model=EvaluationResponse)
async def start_evaluation(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """Start a new evaluation"""
    try:
        # Validate request
        if not request.agents:
            raise HTTPException(status_code=400, detail="At least one agent is required")
        
        # Check if Groq is configured
        if not evaluation_manager.groq_model:
            raise HTTPException(status_code=503, detail="Groq API not configured")
        
        # Generate evaluation ID
        evaluation_id = request.evaluation_id or evaluation_manager.create_evaluation_id()
        
        # Start evaluation
        evaluation_info = evaluation_manager.start_evaluation(evaluation_id, request)
        
        # Estimate time
        estimated_time = len(request.agents) * 60  # Rough estimate
        
        return EvaluationResponse(
            evaluation_id=evaluation_id,
            status="started",
            message=f"Evaluation started with {len(request.agents)} agents",
            results_url=f"/results/{evaluation_id}",
            estimated_time=estimated_time
        )
        
    except Exception as e:
        logger.error(f"Failed to start evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{evaluation_id}")
async def get_evaluation_results(evaluation_id: str):
    """Get evaluation results"""
    try:
        evaluation_info = evaluation_manager.get_evaluation_status(evaluation_id)
        
        if evaluation_info["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        return evaluation_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{evaluation_id}/responses")
async def get_evaluation_responses(evaluation_id: str):
    """Get evaluation results in responses.jsonl format"""
    try:
        evaluation_info = evaluation_manager.get_evaluation_status(evaluation_id)
        
        if evaluation_info["status"] == "not_found":
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        if evaluation_info["status"] != "completed":
            return {
                "status": evaluation_info["status"],
                "progress": evaluation_info.get("progress", 0),
                "message": "Evaluation still in progress"
            }
        
        # Return formatted results
        return {
            "status": "completed",
            "responses": evaluation_info.get("formatted_results", []),
            "summary": evaluation_info.get("results", {}).get("evaluation_summary", {}),
            "total_responses": len(evaluation_info.get("formatted_results", []))
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
            # Cancel if running
            evaluation_info = evaluation_manager.evaluations[evaluation_id]
            if "future" in evaluation_info and not evaluation_info["future"].done():
                evaluation_info["future"].cancel()
            
            # Remove from memory
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
        "message": "Agentic Evaluation API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "evaluate": "POST /evaluate",
            "agents": "GET /agents", 
            "results": "GET /results/{evaluation_id}",
            "responses": "GET /results/{evaluation_id}/responses"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Agentic Evaluation API Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("💡 Make sure GROQ_API_KEY is set in environment")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
