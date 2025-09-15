from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from deepeval.test_case import LLMTestCase, ConversationalTestCase, MLLMTestCase


class DomainType(Enum):
    """Supported domains for agentic evaluation"""
    QA = "qa"
    SUMMARIZATION = "summarization"
    REASONING = "reasoning"
    CONVERSATION = "conversation"
    CODE_GENERATION = "code_generation"
    GENERAL = "general"


@dataclass
class Agent:
    """Represents an AI agent for evaluation"""
    id: str
    name: str
    model_name: str
    domain: DomainType = DomainType.GENERAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("Agent ID cannot be empty")
        if not self.name:
            raise ValueError("Agent name cannot be empty")


@dataclass
class AgentResult:
    """Result of evaluating a single agent"""
    agent_id: str
    agent_name: str
    scores: Dict[str, float]  # dimension -> score
    overall_score: float
    passed: bool
    reasoning: Dict[str, str]  # dimension -> explanation
    evaluation_time: float
    test_cases_processed: int
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRanking:
    """Ranking information for an agent"""
    agent_id: str
    agent_name: str
    rank: int
    overall_score: float
    domain_scores: Dict[str, float]
    percentile: float
    trend: str  # "improving", "declining", "stable"


@dataclass
class AgentMetrics:
    """Aggregated metrics across all agents"""
    total_agents: int
    average_score: float
    median_score: float
    std_deviation: float
    top_performers: List[AgentRanking]
    bottom_performers: List[AgentRanking]
    domain_breakdown: Dict[DomainType, Dict[str, float]]
    performance_distribution: Dict[str, int]  # score_range -> count


@dataclass
class AgenticEvaluationResult:
    """Complete result of agentic evaluation"""
    agent_results: List[AgentResult]
    agent_metrics: AgentMetrics
    evaluation_config: 'EvaluationConfig'
    evaluation_time: float
    total_test_cases: int
    successful_evaluations: int
    failed_evaluations: int
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EvaluationConfig:
    """Configuration for agentic evaluation"""
    max_agents: int = 100
    batch_size: int = 10
    max_concurrent: int = 50
    timeout_seconds: int = 300
    retry_attempts: int = 3
    include_explanations: bool = True
    strict_mode: bool = False
    cache_results: bool = True
    domains: List[DomainType] = field(default_factory=lambda: [DomainType.GENERAL])
    custom_metrics: List[str] = field(default_factory=list)


@dataclass
class PerformanceExplanation:
    """Detailed explanation of agent performance"""
    agent_id: str
    overall_explanation: str
    dimension_explanations: Dict[str, str]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    benchmark_comparison: Dict[str, Any]
    trend_analysis: Dict[str, Any]


@dataclass
class Leaderboard:
    """Leaderboard for agent performance"""
    rankings: List[AgentRanking]
    domain_rankings: Dict[DomainType, List[AgentRanking]]
    top_performers: List[AgentRanking]
    most_improved: List[AgentRanking]
    most_declined: List[AgentRanking]
    created_at: datetime = field(default_factory=datetime.now)


# Type aliases for better readability
TestCaseType = Union["LLMTestCase", "ConversationalTestCase", "MLLMTestCase"]
AgentScores = Dict[str, Dict[str, float]]  # agent_id -> dimension -> score
DimensionScores = Dict[str, float]  # dimension -> score
