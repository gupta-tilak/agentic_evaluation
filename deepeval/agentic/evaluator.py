from typing import List, Dict, Any, Optional, Union
import time
import logging
from dataclasses import dataclass

from .types import (
    Agent, AgenticEvaluationResult, EvaluationConfig, TestCaseType,
    AgentResult, AgentRanking, Leaderboard, PerformanceExplanation
)
from .agent_registry import AgentRegistry
from .dimensions import (
    EvaluationDimension, InstructionFollowing, HallucinationDetection,
    AssumptionControl, CoherenceAccuracy, DimensionEvaluator
)
from .batch_processor import AgenticBatchProcessor
from .reporting import AgenticReporter


class AgenticEvaluator:
    """Main evaluator for agentic evaluation framework"""
    
    def __init__(
        self,
        config: Optional[EvaluationConfig] = None,
        agent_registry: Optional[AgentRegistry] = None,
        dimensions: Optional[List[EvaluationDimension]] = None
    ):
        self.config = config or EvaluationConfig()
        self.agent_registry = agent_registry or AgentRegistry()
        self.logger = logging.getLogger(__name__)
        
        # Set up default dimensions if none provided
        if dimensions is None:
            self.dimensions = [
                InstructionFollowing(weight=1.0, threshold=0.7),
                HallucinationDetection(weight=1.0, threshold=0.8),
                AssumptionControl(weight=1.0, threshold=0.6),
                CoherenceAccuracy(weight=1.0, threshold=0.7)
            ]
        else:
            self.dimensions = dimensions
        
        self.dimension_evaluator = DimensionEvaluator(self.dimensions)
        self.batch_processor = AgenticBatchProcessor(
            self.config, self.agent_registry, self.dimension_evaluator
        )
        self.reporter = AgenticReporter()
    
    def register_agent(
        self,
        name: str,
        model_name: str,
        domain: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new agent for evaluation"""
        from .types import DomainType
        
        try:
            domain_enum = DomainType(domain.lower())
        except ValueError:
            domain_enum = DomainType.GENERAL
            self.logger.warning(f"Unknown domain '{domain}', using 'general'")
        
        return self.agent_registry.register_agent(
            name=name,
            model_name=model_name,
            domain=domain_enum,
            metadata=metadata
        )
    
    def register_agents_batch(
        self,
        agents_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Register multiple agents at once"""
        agent_ids = []
        
        for agent_data in agents_data:
            agent_id = self.register_agent(
                name=agent_data.get('name', 'Unnamed Agent'),
                model_name=agent_data.get('model_name', 'unknown'),
                domain=agent_data.get('domain', 'general'),
                metadata=agent_data.get('metadata', {})
            )
            agent_ids.append(agent_id)
        
        return agent_ids
    
    def evaluate_agents(
        self,
        test_cases: List[TestCaseType],
        agent_ids: Optional[List[str]] = None,
        domain: Optional[str] = None,
        async_mode: bool = True,
        show_progress: bool = True
    ) -> AgenticEvaluationResult:
        """Evaluate agents against test cases"""
        start_time = time.time()
        
        # Get agents to evaluate
        if agent_ids:
            agents = [self.agent_registry.get_agent(aid) for aid in agent_ids]
            agents = [a for a in agents if a is not None]
        elif domain:
            from .types import DomainType
            try:
                domain_enum = DomainType(domain.lower())
                agents = self.agent_registry.get_agents_by_domain(domain_enum)
            except ValueError:
                self.logger.error(f"Unknown domain '{domain}'")
                agents = []
        else:
            agents = self.agent_registry.get_all_agents()
        
        if not agents:
            self.logger.warning("No agents found for evaluation")
            return AgenticEvaluationResult(
                agent_results=[],
                agent_metrics=self._create_empty_metrics(),
                evaluation_config=self.config,
                evaluation_time=0.0,
                total_test_cases=len(test_cases),
                successful_evaluations=0,
                failed_evaluations=0
            )
        
        self.logger.info(f"Evaluating {len(agents)} agents against {len(test_cases)} test cases")
        
        # Run evaluation
        if async_mode:
            result = self._run_async_evaluation(agents, test_cases, show_progress)
        else:
            result = self._run_sync_evaluation(agents, test_cases)
        
        evaluation_time = time.time() - start_time
        result.evaluation_time = evaluation_time
        
        self.logger.info(
            f"Evaluation completed in {evaluation_time:.2f}s. "
            f"Success: {result.successful_evaluations}, "
            f"Failed: {result.failed_evaluations}"
        )
        
        return result
    
    def _run_async_evaluation(
        self,
        agents: List[Agent],
        test_cases: List[TestCaseType],
        show_progress: bool
    ) -> AgenticEvaluationResult:
        """Run asynchronous evaluation"""
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.batch_processor.process_agents_async(agents, test_cases, show_progress)
            )
        finally:
            loop.close()
    
    def _run_sync_evaluation(
        self,
        agents: List[Agent],
        test_cases: List[TestCaseType]
    ) -> AgenticEvaluationResult:
        """Run synchronous evaluation"""
        return self.batch_processor.process_agents_sync(agents, test_cases)
    
    def generate_leaderboard(
        self,
        evaluation_result: AgenticEvaluationResult,
        domain: Optional[str] = None
    ) -> Leaderboard:
        """Generate leaderboard from evaluation results"""
        return self.reporter.generate_leaderboard(evaluation_result, domain)
    
    def explain_performance(
        self,
        agent_id: str,
        evaluation_result: AgenticEvaluationResult
    ) -> PerformanceExplanation:
        """Generate detailed performance explanation for an agent"""
        return self.reporter.explain_performance(agent_id, evaluation_result)
    
    def compare_agents(
        self,
        agent_ids: List[str],
        evaluation_result: AgenticEvaluationResult
    ) -> Dict[str, Any]:
        """Compare specific agents"""
        return self.reporter.compare_agents(agent_ids, evaluation_result)
    
    def get_agent_rankings(
        self,
        evaluation_result: AgenticEvaluationResult,
        limit: Optional[int] = None
    ) -> List[AgentRanking]:
        """Get agent rankings from evaluation result"""
        rankings = []
        
        for i, result in enumerate(evaluation_result.agent_results):
            ranking = AgentRanking(
                agent_id=result.agent_id,
                agent_name=result.agent_name,
                rank=i + 1,
                overall_score=result.overall_score,
                domain_scores=result.scores,
                percentile=((len(evaluation_result.agent_results) - i) / 
                          len(evaluation_result.agent_results)) * 100,
                trend="stable"  # TODO: Implement trend analysis
            )
            rankings.append(ranking)
        
        # Sort by score (descending)
        rankings.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Update ranks
        for i, ranking in enumerate(rankings):
            ranking.rank = i + 1
            ranking.percentile = ((len(rankings) - i) / len(rankings)) * 100
        
        return rankings[:limit] if limit else rankings
    
    def export_results(
        self,
        evaluation_result: AgenticEvaluationResult,
        filepath: str,
        format: str = "json"
    ) -> bool:
        """Export evaluation results to file"""
        return self.reporter.export_results(evaluation_result, filepath, format)
    
    def get_domain_analysis(
        self,
        evaluation_result: AgenticEvaluationResult
    ) -> Dict[str, Any]:
        """Get analysis by domain"""
        return self.reporter.get_domain_analysis(evaluation_result)
    
    def get_performance_insights(
        self,
        evaluation_result: AgenticEvaluationResult
    ) -> Dict[str, Any]:
        """Get performance insights and recommendations"""
        return self.reporter.get_performance_insights(evaluation_result)
    
    def _create_empty_metrics(self):
        """Create empty metrics for when no agents are evaluated"""
        from .types import AgentMetrics
        
        return AgentMetrics(
            total_agents=0,
            average_score=0.0,
            median_score=0.0,
            std_deviation=0.0,
            top_performers=[],
            bottom_performers=[],
            domain_breakdown={},
            performance_distribution={}
        )
    
    def get_evaluation_summary(self, evaluation_result: AgenticEvaluationResult) -> Dict[str, Any]:
        """Get a summary of the evaluation results"""
        return {
            "total_agents": evaluation_result.agent_metrics.total_agents,
            "successful_evaluations": evaluation_result.successful_evaluations,
            "failed_evaluations": evaluation_result.failed_evaluations,
            "average_score": evaluation_result.agent_metrics.average_score,
            "median_score": evaluation_result.agent_metrics.median_score,
            "evaluation_time": evaluation_result.evaluation_time,
            "total_test_cases": evaluation_result.total_test_cases,
            "top_performer": (
                evaluation_result.agent_metrics.top_performers[0].agent_name
                if evaluation_result.agent_metrics.top_performers
                else "N/A"
            ),
            "performance_distribution": evaluation_result.agent_metrics.performance_distribution
        }
    
    def add_custom_dimension(self, dimension: EvaluationDimension):
        """Add a custom evaluation dimension"""
        self.dimensions.append(dimension)
        self.dimension_evaluator = DimensionEvaluator(self.dimensions)
        self.batch_processor = AgenticBatchProcessor(
            self.config, self.agent_registry, self.dimension_evaluator
        )
    
    def get_agent_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent registry"""
        return self.agent_registry.get_registry_stats()
    
    def clear_agents(self):
        """Clear all agents from registry"""
        for agent in self.agent_registry.get_all_agents():
            self.agent_registry.remove_agent(agent.id)
    
    def export_agents(self, filepath: str) -> bool:
        """Export agent registry to file"""
        return self.agent_registry.export_agents(filepath)
    
    def import_agents(self, filepath: str) -> bool:
        """Import agent registry from file"""
        return self.agent_registry.import_agents(filepath)
