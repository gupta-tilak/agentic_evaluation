import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from rich.progress import Progress, TaskID, TextColumn, BarColumn, TimeElapsedColumn

from .types import (
    Agent, AgentResult, AgenticEvaluationResult, EvaluationConfig,
    TestCaseType, AgentScores, DimensionScores
)
from .dimensions import EvaluationDimension, DimensionEvaluator
from .agent_registry import AgentRegistry


@dataclass
class BatchProgress:
    """Progress tracking for batch processing"""
    total_agents: int
    processed_agents: int
    successful_evaluations: int
    failed_evaluations: int
    current_agent: Optional[str] = None
    start_time: Optional[float] = None
    estimated_completion: Optional[float] = None


class AgenticBatchProcessor:
    """Batch processor for evaluating multiple agents"""
    
    def __init__(
        self,
        config: EvaluationConfig,
        agent_registry: AgentRegistry,
        dimension_evaluator: DimensionEvaluator
    ):
        self.config = config
        self.agent_registry = agent_registry
        self.dimension_evaluator = dimension_evaluator
        self.logger = logging.getLogger(__name__)
        
        # Progress tracking
        self._progress: Optional[BatchProgress] = None
        self._progress_callback: Optional[Callable[[BatchProgress], None]] = None
    
    def set_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """Set callback for progress updates"""
        self._progress_callback = callback
    
    def _update_progress(self, **kwargs):
        """Update progress and notify callback"""
        if self._progress:
            for key, value in kwargs.items():
                setattr(self._progress, key, value)
            
            if self._progress_callback:
                self._progress_callback(self._progress)
    
    async def process_agents_async(
        self,
        agents: List[Agent],
        test_cases: List[TestCaseType],
        show_progress: bool = True
    ) -> AgenticEvaluationResult:
        """Process agents asynchronously with progress tracking"""
        start_time = time.time()
        
        # Initialize progress tracking
        self._progress = BatchProgress(
            total_agents=len(agents),
            processed_agents=0,
            successful_evaluations=0,
            failed_evaluations=0,
            start_time=start_time
        )
        
        agent_results = []
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def evaluate_agent_with_semaphore(agent: Agent) -> AgentResult:
            async with semaphore:
                return await self._evaluate_agent_async(agent, test_cases)
        
        # Create tasks for all agents
        tasks = [evaluate_agent_with_semaphore(agent) for agent in agents]
        
        if show_progress:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=None
            ) as progress:
                task_id = progress.add_task(
                    f"Evaluating {len(agents)} agents...", 
                    total=len(agents)
                )
                
                # Process agents in batches
                for i in range(0, len(tasks), self.config.batch_size):
                    batch_tasks = tasks[i:i + self.config.batch_size]
                    batch_agents = agents[i:i + self.config.batch_size]
                    
                    # Wait for batch completion
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    
                    # Process results
                    for agent, result in zip(batch_agents, batch_results):
                        if isinstance(result, Exception):
                            self.logger.error(f"Error evaluating agent {agent.id}: {result}")
                            agent_results.append(AgentResult(
                                agent_id=agent.id,
                                agent_name=agent.name,
                                scores={},
                                overall_score=0.0,
                                passed=False,
                                reasoning={},
                                evaluation_time=0.0,
                                test_cases_processed=0,
                                errors=[str(result)]
                            ))
                            self._update_progress(failed_evaluations=self._progress.failed_evaluations + 1)
                        else:
                            agent_results.append(result)
                            if result.passed:
                                self._update_progress(successful_evaluations=self._progress.successful_evaluations + 1)
                            else:
                                self._update_progress(failed_evaluations=self._progress.failed_evaluations + 1)
                        
                        self._update_progress(processed_agents=self._progress.processed_agents + 1)
                        progress.update(task_id, advance=1)
        else:
            # Process without progress bar
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for agent, result in zip(agents, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error evaluating agent {agent.id}: {result}")
                    agent_results.append(AgentResult(
                        agent_id=agent.id,
                        agent_name=agent.name,
                        scores={},
                        overall_score=0.0,
                        passed=False,
                        reasoning={},
                        evaluation_time=0.0,
                        test_cases_processed=0,
                        errors=[str(result)]
                    ))
                else:
                    agent_results.append(result)
        
        evaluation_time = time.time() - start_time
        
        # Calculate metrics
        agent_metrics = self._calculate_agent_metrics(agent_results)
        
        return AgenticEvaluationResult(
            agent_results=agent_results,
            agent_metrics=agent_metrics,
            evaluation_config=self.config,
            evaluation_time=evaluation_time,
            total_test_cases=len(test_cases),
            successful_evaluations=len([r for r in agent_results if r.passed]),
            failed_evaluations=len([r for r in agent_results if not r.passed])
        )
    
    async def _evaluate_agent_async(
        self,
        agent: Agent,
        test_cases: List[TestCaseType]
    ) -> AgentResult:
        """Evaluate a single agent asynchronously"""
        start_time = time.time()
        scores = {}
        reasoning = {}
        errors = []
        total_evaluation_time = 0.0
        
        try:
            # Evaluate each test case
            for test_case in test_cases:
                try:
                    # Run dimension evaluation
                    dimension_results = self.dimension_evaluator.evaluate_agent(agent, test_case)
                    
                    # Aggregate scores
                    for dim_name, dim_result in dimension_results.items():
                        if dim_name not in scores:
                            scores[dim_name] = []
                        scores[dim_name].append(dim_result.score)
                        
                        if dim_name not in reasoning:
                            reasoning[dim_name] = []
                        reasoning[dim_name].append(dim_result.reasoning)
                        
                        total_evaluation_time += dim_result.evaluation_time
                
                except Exception as e:
                    error_msg = f"Error evaluating test case: {str(e)}"
                    errors.append(error_msg)
                    self.logger.warning(f"Agent {agent.id}: {error_msg}")
            
            # Calculate average scores
            avg_scores = {}
            for dim_name, score_list in scores.items():
                avg_scores[dim_name] = sum(score_list) / len(score_list) if score_list else 0.0
            
            # Calculate overall score
            overall_score = self.dimension_evaluator.calculate_weighted_score({
                name: type('obj', (object,), {'score': score})()
                for name, score in avg_scores.items()
            })
            
            # Determine if passed (all dimensions above threshold)
            passed = all(
                score >= self.dimension_evaluator.dimensions[i].threshold
                for i, (name, score) in enumerate(avg_scores.items())
                if i < len(self.dimension_evaluator.dimensions)
            )
            
            return AgentResult(
                agent_id=agent.id,
                agent_name=agent.name,
                scores=avg_scores,
                overall_score=overall_score,
                passed=passed,
                reasoning=reasoning,
                evaluation_time=total_evaluation_time,
                test_cases_processed=len(test_cases),
                errors=errors,
                metadata={
                    "model_name": agent.model_name,
                    "domain": agent.domain.value,
                    "evaluation_timestamp": time.time()
                }
            )
        
        except Exception as e:
            self.logger.error(f"Critical error evaluating agent {agent.id}: {e}")
            return AgentResult(
                agent_id=agent.id,
                agent_name=agent.name,
                scores={},
                overall_score=0.0,
                passed=False,
                reasoning={},
                evaluation_time=0.0,
                test_cases_processed=0,
                errors=[f"Critical error: {str(e)}"]
            )
    
    def _calculate_agent_metrics(self, agent_results: List[AgentResult]) -> 'AgentMetrics':
        """Calculate aggregated metrics across all agents"""
        from .types import AgentMetrics, AgentRanking, DomainType
        import statistics
        
        if not agent_results:
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
        
        # Basic statistics
        overall_scores = [result.overall_score for result in agent_results]
        average_score = statistics.mean(overall_scores)
        median_score = statistics.median(overall_scores)
        std_deviation = statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0.0
        
        # Create rankings
        rankings = []
        for i, result in enumerate(agent_results):
            ranking = AgentRanking(
                agent_id=result.agent_id,
                agent_name=result.agent_name,
                rank=i + 1,
                overall_score=result.overall_score,
                domain_scores=result.scores,
                percentile=(i / len(agent_results)) * 100,
                trend="stable"  # TODO: Implement trend analysis
            )
            rankings.append(ranking)
        
        # Sort by score (descending)
        rankings.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Update ranks
        for i, ranking in enumerate(rankings):
            ranking.rank = i + 1
            ranking.percentile = ((len(rankings) - i) / len(rankings)) * 100
        
        # Top and bottom performers
        top_count = min(5, len(rankings))
        top_performers = rankings[:top_count]
        bottom_performers = rankings[-top_count:] if len(rankings) > top_count else []
        
        # Domain breakdown
        domain_breakdown = {}
        for domain in DomainType:
            domain_results = [r for r in agent_results if r.metadata.get('domain') == domain.value]
            if domain_results:
                domain_scores = [r.overall_score for r in domain_results]
                domain_breakdown[domain] = {
                    'count': len(domain_results),
                    'average_score': statistics.mean(domain_scores),
                    'median_score': statistics.median(domain_scores),
                    'std_deviation': statistics.stdev(domain_scores) if len(domain_scores) > 1 else 0.0
                }
        
        # Performance distribution
        performance_distribution = {
            'excellent (0.9-1.0)': len([s for s in overall_scores if s >= 0.9]),
            'good (0.7-0.9)': len([s for s in overall_scores if 0.7 <= s < 0.9]),
            'fair (0.5-0.7)': len([s for s in overall_scores if 0.5 <= s < 0.7]),
            'poor (0.0-0.5)': len([s for s in overall_scores if s < 0.5])
        }
        
        return AgentMetrics(
            total_agents=len(agent_results),
            average_score=average_score,
            median_score=median_score,
            std_deviation=std_deviation,
            top_performers=top_performers,
            bottom_performers=bottom_performers,
            domain_breakdown=domain_breakdown,
            performance_distribution=performance_distribution
        )
    
    def process_agents_sync(
        self,
        agents: List[Agent],
        test_cases: List[TestCaseType],
        max_workers: Optional[int] = None
    ) -> AgenticEvaluationResult:
        """Process agents synchronously using thread pool"""
        start_time = time.time()
        
        if max_workers is None:
            max_workers = min(self.config.max_concurrent, len(agents))
        
        agent_results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all agent evaluations
            future_to_agent = {
                executor.submit(self._evaluate_agent_sync, agent, test_cases): agent
                for agent in agents
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result()
                    agent_results.append(result)
                except Exception as e:
                    self.logger.error(f"Error evaluating agent {agent.id}: {e}")
                    agent_results.append(AgentResult(
                        agent_id=agent.id,
                        agent_name=agent.name,
                        scores={},
                        overall_score=0.0,
                        passed=False,
                        reasoning={},
                        evaluation_time=0.0,
                        test_cases_processed=0,
                        errors=[str(e)]
                    ))
        
        evaluation_time = time.time() - start_time
        agent_metrics = self._calculate_agent_metrics(agent_results)
        
        return AgenticEvaluationResult(
            agent_results=agent_results,
            agent_metrics=agent_metrics,
            evaluation_config=self.config,
            evaluation_time=evaluation_time,
            total_test_cases=len(test_cases),
            successful_evaluations=len([r for r in agent_results if r.passed]),
            failed_evaluations=len([r for r in agent_results if not r.passed])
        )
    
    def _evaluate_agent_sync(
        self,
        agent: Agent,
        test_cases: List[TestCaseType]
    ) -> AgentResult:
        """Synchronous evaluation of a single agent"""
        # This is a simplified sync version - in practice, you'd want to
        # implement proper async-to-sync conversion or use a different approach
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._evaluate_agent_async(agent, test_cases))
        finally:
            loop.close()
