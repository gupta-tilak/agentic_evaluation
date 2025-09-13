import json
import csv
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import statistics
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .types import (
    AgenticEvaluationResult, AgentResult, AgentRanking, Leaderboard,
    PerformanceExplanation, AgentMetrics, DomainType
)


class AgenticReporter:
    """Reporter for generating evaluation reports and visualizations"""
    
    def __init__(self):
        self.console = Console()
    
    def generate_leaderboard(
        self,
        evaluation_result: AgenticEvaluationResult,
        domain: Optional[str] = None
    ) -> Leaderboard:
        """Generate leaderboard from evaluation results"""
        # Get rankings
        rankings = self._create_rankings(evaluation_result.agent_results)
        
        # Filter by domain if specified
        if domain:
            try:
                domain_enum = DomainType(domain.lower())
                rankings = [r for r in rankings if r.agent_id in [
                    result.agent_id for result in evaluation_result.agent_results
                    if result.metadata.get('domain') == domain_enum.value
                ]]
            except ValueError:
                pass  # Invalid domain, use all rankings
        
        # Sort by overall score (descending)
        rankings.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Update ranks
        for i, ranking in enumerate(rankings):
            ranking.rank = i + 1
            ranking.percentile = ((len(rankings) - i) / len(rankings)) * 100
        
        # Create domain-specific rankings
        domain_rankings = self._create_domain_rankings(evaluation_result.agent_results)
        
        # Identify top performers, most improved, etc.
        top_performers = rankings[:min(10, len(rankings))]
        most_improved = self._identify_most_improved(rankings)
        most_declined = self._identify_most_declined(rankings)
        
        return Leaderboard(
            rankings=rankings,
            domain_rankings=domain_rankings,
            top_performers=top_performers,
            most_improved=most_improved,
            most_declined=most_declined
        )
    
    def explain_performance(
        self,
        agent_id: str,
        evaluation_result: AgenticEvaluationResult
    ) -> PerformanceExplanation:
        """Generate detailed performance explanation for an agent"""
        # Find agent result
        agent_result = None
        for result in evaluation_result.agent_results:
            if result.agent_id == agent_id:
                agent_result = result
                break
        
        if not agent_result:
            raise ValueError(f"Agent {agent_id} not found in evaluation results")
        
        # Generate explanations
        overall_explanation = self._generate_overall_explanation(agent_result, evaluation_result)
        dimension_explanations = self._generate_dimension_explanations(agent_result)
        strengths = self._identify_strengths(agent_result)
        weaknesses = self._identify_weaknesses(agent_result)
        recommendations = self._generate_recommendations(agent_result, evaluation_result)
        benchmark_comparison = self._generate_benchmark_comparison(agent_result, evaluation_result)
        trend_analysis = self._generate_trend_analysis(agent_result, evaluation_result)
        
        return PerformanceExplanation(
            agent_id=agent_id,
            overall_explanation=overall_explanation,
            dimension_explanations=dimension_explanations,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            benchmark_comparison=benchmark_comparison,
            trend_analysis=trend_analysis
        )
    
    def compare_agents(
        self,
        agent_ids: List[str],
        evaluation_result: AgenticEvaluationResult
    ) -> Dict[str, Any]:
        """Compare specific agents"""
        agent_results = []
        for agent_id in agent_ids:
            for result in evaluation_result.agent_results:
                if result.agent_id == agent_id:
                    agent_results.append(result)
                    break
        
        if len(agent_results) != len(agent_ids):
            missing = set(agent_ids) - {r.agent_id for r in agent_results}
            raise ValueError(f"Agents not found: {missing}")
        
        # Create comparison data
        comparison = {
            "agents": [],
            "dimension_comparison": {},
            "overall_ranking": [],
            "summary": {}
        }
        
        # Agent details
        for result in agent_results:
            comparison["agents"].append({
                "agent_id": result.agent_id,
                "agent_name": result.agent_name,
                "overall_score": result.overall_score,
                "passed": result.passed,
                "evaluation_time": result.evaluation_time,
                "test_cases_processed": result.test_cases_processed
            })
        
        # Dimension comparison
        all_dimensions = set()
        for result in agent_results:
            all_dimensions.update(result.scores.keys())
        
        for dimension in all_dimensions:
            comparison["dimension_comparison"][dimension] = {
                "scores": {result.agent_id: result.scores.get(dimension, 0.0) for result in agent_results},
                "average": statistics.mean([result.scores.get(dimension, 0.0) for result in agent_results]),
                "best_performer": max(agent_results, key=lambda r: r.scores.get(dimension, 0.0)).agent_id
            }
        
        # Overall ranking
        sorted_results = sorted(agent_results, key=lambda x: x.overall_score, reverse=True)
        comparison["overall_ranking"] = [
            {"rank": i + 1, "agent_id": result.agent_id, "score": result.overall_score}
            for i, result in enumerate(sorted_results)
        ]
        
        # Summary
        comparison["summary"] = {
            "total_agents": len(agent_results),
            "average_score": statistics.mean([r.overall_score for r in agent_results]),
            "score_range": {
                "min": min(r.overall_score for r in agent_results),
                "max": max(r.overall_score for r in agent_results)
            },
            "pass_rate": len([r for r in agent_results if r.passed]) / len(agent_results)
        }
        
        return comparison
    
    def export_results(
        self,
        evaluation_result: AgenticEvaluationResult,
        filepath: str,
        format: str = "json"
    ) -> bool:
        """Export evaluation results to file"""
        try:
            if format.lower() == "json":
                return self._export_json(evaluation_result, filepath)
            elif format.lower() == "csv":
                return self._export_csv(evaluation_result, filepath)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            print(f"Error exporting results: {e}")
            return False
    
    def get_domain_analysis(
        self,
        evaluation_result: AgenticEvaluationResult
    ) -> Dict[str, Any]:
        """Get analysis by domain"""
        domain_analysis = {}
        
        for domain, metrics in evaluation_result.agent_metrics.domain_breakdown.items():
            domain_analysis[domain.value] = {
                "agent_count": metrics["count"],
                "average_score": metrics["average_score"],
                "median_score": metrics["median_score"],
                "std_deviation": metrics["std_deviation"],
                "performance_grade": self._calculate_performance_grade(metrics["average_score"])
            }
        
        return domain_analysis
    
    def get_performance_insights(
        self,
        evaluation_result: AgenticEvaluationResult
    ) -> Dict[str, Any]:
        """Get performance insights and recommendations"""
        insights = {
            "overall_performance": self._analyze_overall_performance(evaluation_result),
            "dimension_analysis": self._analyze_dimensions(evaluation_result),
            "recommendations": self._generate_system_recommendations(evaluation_result),
            "trends": self._analyze_trends(evaluation_result)
        }
        
        return insights
    
    def print_leaderboard(self, leaderboard: Leaderboard, limit: int = 20):
        """Print leaderboard to console"""
        table = Table(title="Agent Performance Leaderboard")
        table.add_column("Rank", style="cyan", no_wrap=True)
        table.add_column("Agent Name", style="magenta")
        table.add_column("Overall Score", style="green")
        table.add_column("Percentile", style="blue")
        table.add_column("Status", style="yellow")
        
        for ranking in leaderboard.rankings[:limit]:
            status = "✅ Pass" if ranking.overall_score >= 0.7 else "❌ Fail"
            table.add_row(
                str(ranking.rank),
                ranking.agent_name,
                f"{ranking.overall_score:.3f}",
                f"{ranking.percentile:.1f}%",
                status
            )
        
        self.console.print(table)
    
    def print_performance_explanation(self, explanation: PerformanceExplanation):
        """Print performance explanation to console"""
        # Overall explanation
        self.console.print(Panel(
            f"[bold]Overall Performance:[/bold]\n{explanation.overall_explanation}",
            title=f"Agent {explanation.agent_id}",
            border_style="blue"
        ))
        
        # Strengths and weaknesses
        if explanation.strengths:
            self.console.print(Panel(
                "\n".join(f"• {strength}" for strength in explanation.strengths),
                title="Strengths",
                border_style="green"
            ))
        
        if explanation.weaknesses:
            self.console.print(Panel(
                "\n".join(f"• {weakness}" for weakness in explanation.weaknesses),
                title="Areas for Improvement",
                border_style="red"
            ))
        
        # Recommendations
        if explanation.recommendations:
            self.console.print(Panel(
                "\n".join(f"• {rec}" for rec in explanation.recommendations),
                title="Recommendations",
                border_style="yellow"
            ))
    
    def _create_rankings(self, agent_results: List[AgentResult]) -> List[AgentRanking]:
        """Create rankings from agent results"""
        rankings = []
        
        for result in agent_results:
            ranking = AgentRanking(
                agent_id=result.agent_id,
                agent_name=result.agent_name,
                rank=0,  # Will be set later
                overall_score=result.overall_score,
                domain_scores=result.scores,
                percentile=0.0,  # Will be calculated later
                trend="stable"
            )
            rankings.append(ranking)
        
        return rankings
    
    def _create_domain_rankings(self, agent_results: List[AgentResult]) -> Dict[DomainType, List[AgentRanking]]:
        """Create domain-specific rankings"""
        domain_rankings = {}
        
        for domain in DomainType:
            domain_results = [
                r for r in agent_results 
                if r.metadata.get('domain') == domain.value
            ]
            
            if domain_results:
                rankings = self._create_rankings(domain_results)
                rankings.sort(key=lambda x: x.overall_score, reverse=True)
                
                for i, ranking in enumerate(rankings):
                    ranking.rank = i + 1
                    ranking.percentile = ((len(rankings) - i) / len(rankings)) * 100
                
                domain_rankings[domain] = rankings
        
        return domain_rankings
    
    def _identify_most_improved(self, rankings: List[AgentRanking]) -> List[AgentRanking]:
        """Identify most improved agents (placeholder for trend analysis)"""
        # TODO: Implement trend analysis
        return []
    
    def _identify_most_declined(self, rankings: List[AgentRanking]) -> List[AgentRanking]:
        """Identify most declined agents (placeholder for trend analysis)"""
        # TODO: Implement trend analysis
        return []
    
    def _generate_overall_explanation(
        self,
        agent_result: AgentResult,
        evaluation_result: AgenticEvaluationResult
    ) -> str:
        """Generate overall performance explanation"""
        score = agent_result.overall_score
        percentile = self._calculate_percentile(agent_result, evaluation_result)
        
        if score >= 0.9:
            performance_level = "excellent"
        elif score >= 0.7:
            performance_level = "good"
        elif score >= 0.5:
            performance_level = "fair"
        else:
            performance_level = "poor"
        
        return (
            f"Agent '{agent_result.agent_name}' achieved an overall score of {score:.3f} "
            f"({performance_level} performance), placing it in the {percentile:.1f}th percentile. "
            f"The agent {'passed' if agent_result.passed else 'failed'} the evaluation criteria."
        )
    
    def _generate_dimension_explanations(self, agent_result: AgentResult) -> Dict[str, str]:
        """Generate explanations for each dimension"""
        explanations = {}
        
        for dimension, score in agent_result.scores.items():
            if score >= 0.8:
                level = "excellent"
            elif score >= 0.6:
                level = "good"
            elif score >= 0.4:
                level = "fair"
            else:
                level = "poor"
            
            explanations[dimension] = (
                f"Scored {score:.3f} ({level}) on {dimension}. "
                f"{agent_result.reasoning.get(dimension, 'No detailed reasoning available.')}"
            )
        
        return explanations
    
    def _identify_strengths(self, agent_result: AgentResult) -> List[str]:
        """Identify agent strengths"""
        strengths = []
        
        for dimension, score in agent_result.scores.items():
            if score >= 0.8:
                strengths.append(f"Strong performance in {dimension} (score: {score:.3f})")
        
        if agent_result.evaluation_time < 5.0:  # Fast evaluation
            strengths.append("Fast response time")
        
        if not agent_result.errors:
            strengths.append("No evaluation errors")
        
        return strengths
    
    def _identify_weaknesses(self, agent_result: AgentResult) -> List[str]:
        """Identify agent weaknesses"""
        weaknesses = []
        
        for dimension, score in agent_result.scores.items():
            if score < 0.5:
                weaknesses.append(f"Poor performance in {dimension} (score: {score:.3f})")
        
        if agent_result.evaluation_time > 30.0:  # Slow evaluation
            weaknesses.append("Slow response time")
        
        if agent_result.errors:
            weaknesses.append(f"Evaluation errors: {len(agent_result.errors)} issues")
        
        return weaknesses
    
    def _generate_recommendations(
        self,
        agent_result: AgentResult,
        evaluation_result: AgenticEvaluationResult
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Dimension-specific recommendations
        for dimension, score in agent_result.scores.items():
            if score < 0.6:
                if dimension == "Instruction Following":
                    recommendations.append("Improve instruction following by being more precise and complete")
                elif dimension == "Hallucination Detection":
                    recommendations.append("Reduce hallucination by sticking to provided context")
                elif dimension == "Assumption Control":
                    recommendations.append("Avoid making unwarranted assumptions")
                elif dimension == "Coherence & Accuracy":
                    recommendations.append("Improve response coherence and factual accuracy")
        
        # General recommendations
        if agent_result.overall_score < 0.5:
            recommendations.append("Consider retraining or fine-tuning the model")
        
        if agent_result.evaluation_time > 20.0:
            recommendations.append("Optimize model for faster inference")
        
        return recommendations
    
    def _generate_benchmark_comparison(
        self,
        agent_result: AgentResult,
        evaluation_result: AgenticEvaluationResult
    ) -> Dict[str, Any]:
        """Generate benchmark comparison"""
        all_scores = [r.overall_score for r in evaluation_result.agent_results]
        
        return {
            "agent_score": agent_result.overall_score,
            "average_score": statistics.mean(all_scores),
            "median_score": statistics.median(all_scores),
            "percentile": self._calculate_percentile(agent_result, evaluation_result),
            "better_than": len([s for s in all_scores if s < agent_result.overall_score]) / len(all_scores) * 100
        }
    
    def _generate_trend_analysis(
        self,
        agent_result: AgentResult,
        evaluation_result: AgenticEvaluationResult
    ) -> Dict[str, Any]:
        """Generate trend analysis (placeholder)"""
        # TODO: Implement trend analysis with historical data
        return {
            "trend": "stable",
            "change": 0.0,
            "period": "N/A"
        }
    
    def _calculate_percentile(
        self,
        agent_result: AgentResult,
        evaluation_result: AgenticEvaluationResult
    ) -> float:
        """Calculate agent percentile"""
        all_scores = [r.overall_score for r in evaluation_result.agent_results]
        better_scores = len([s for s in all_scores if s < agent_result.overall_score])
        return (better_scores / len(all_scores)) * 100 if all_scores else 0.0
    
    def _calculate_performance_grade(self, score: float) -> str:
        """Calculate performance grade"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.6:
            return "C"
        elif score >= 0.5:
            return "D"
        else:
            return "F"
    
    def _analyze_overall_performance(self, evaluation_result: AgenticEvaluationResult) -> Dict[str, Any]:
        """Analyze overall performance"""
        metrics = evaluation_result.agent_metrics
        
        return {
            "total_agents": metrics.total_agents,
            "average_score": metrics.average_score,
            "median_score": metrics.median_score,
            "std_deviation": metrics.std_deviation,
            "pass_rate": evaluation_result.successful_evaluations / evaluation_result.total_agents if evaluation_result.total_agents > 0 else 0,
            "performance_distribution": metrics.performance_distribution
        }
    
    def _analyze_dimensions(self, evaluation_result: AgenticEvaluationResult) -> Dict[str, Any]:
        """Analyze performance by dimension"""
        dimension_analysis = {}
        
        # Get all unique dimensions
        all_dimensions = set()
        for result in evaluation_result.agent_results:
            all_dimensions.update(result.scores.keys())
        
        for dimension in all_dimensions:
            scores = [result.scores.get(dimension, 0.0) for result in evaluation_result.agent_results]
            dimension_analysis[dimension] = {
                "average_score": statistics.mean(scores),
                "median_score": statistics.median(scores),
                "std_deviation": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                "min_score": min(scores),
                "max_score": max(scores)
            }
        
        return dimension_analysis
    
    def _generate_system_recommendations(self, evaluation_result: AgenticEvaluationResult) -> List[str]:
        """Generate system-wide recommendations"""
        recommendations = []
        
        metrics = evaluation_result.agent_metrics
        
        if metrics.average_score < 0.6:
            recommendations.append("Overall system performance is below expectations. Consider model improvements.")
        
        if metrics.std_deviation > 0.3:
            recommendations.append("High variance in agent performance. Consider standardizing training or evaluation.")
        
        if evaluation_result.failed_evaluations > evaluation_result.successful_evaluations:
            recommendations.append("More agents failed than passed. Review evaluation criteria and model quality.")
        
        return recommendations
    
    def _analyze_trends(self, evaluation_result: AgenticEvaluationResult) -> Dict[str, Any]:
        """Analyze trends (placeholder)"""
        # TODO: Implement trend analysis with historical data
        return {
            "trend_analysis_available": False,
            "message": "Trend analysis requires historical data"
        }
    
    def _export_json(self, evaluation_result: AgenticEvaluationResult, filepath: str) -> bool:
        """Export results to JSON"""
        export_data = {
            "evaluation_summary": {
                "total_agents": evaluation_result.agent_metrics.total_agents,
                "successful_evaluations": evaluation_result.successful_evaluations,
                "failed_evaluations": evaluation_result.failed_evaluations,
                "average_score": evaluation_result.agent_metrics.average_score,
                "evaluation_time": evaluation_result.evaluation_time,
                "total_test_cases": evaluation_result.total_test_cases
            },
            "agent_results": [
                {
                    "agent_id": result.agent_id,
                    "agent_name": result.agent_name,
                    "scores": result.scores,
                    "overall_score": result.overall_score,
                    "passed": result.passed,
                    "reasoning": result.reasoning,
                    "evaluation_time": result.evaluation_time,
                    "test_cases_processed": result.test_cases_processed,
                    "errors": result.errors,
                    "metadata": result.metadata
                }
                for result in evaluation_result.agent_results
            ],
            "exported_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return True
    
    def _export_csv(self, evaluation_result: AgenticEvaluationResult, filepath: str) -> bool:
        """Export results to CSV"""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            all_dimensions = set()
            for result in evaluation_result.agent_results:
                all_dimensions.update(result.scores.keys())
            
            header = [
                "agent_id", "agent_name", "overall_score", "passed",
                "evaluation_time", "test_cases_processed", "errors_count"
            ] + list(all_dimensions)
            
            writer.writerow(header)
            
            # Data rows
            for result in evaluation_result.agent_results:
                row = [
                    result.agent_id,
                    result.agent_name,
                    result.overall_score,
                    result.passed,
                    result.evaluation_time,
                    result.test_cases_processed,
                    len(result.errors)
                ] + [result.scores.get(dim, 0.0) for dim in all_dimensions]
                
                writer.writerow(row)
        
        return True
