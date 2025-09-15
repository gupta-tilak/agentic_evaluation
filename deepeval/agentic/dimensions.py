from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass
from .types import Agent, DomainType

if TYPE_CHECKING:
    from deepeval.test_case import LLMTestCase, ConversationalTestCase, MLLMTestCase


@dataclass
class DimensionResult:
    """Result of evaluating a single dimension"""
    dimension_name: str
    score: float
    passed: bool
    reasoning: str
    details: Dict[str, Any]
    evaluation_time: float


class EvaluationDimension(ABC):
    """Base class for evaluation dimensions"""
    
    def __init__(
        self,
        name: str,
        weight: float = 1.0,
        threshold: float = 0.5,
        model: Optional[Union[str, Any]] = None
    ):
        self.name = name
        self.weight = weight
        self.threshold = threshold
        self.model = model
        self._metric = None
    
    @abstractmethod
    def evaluate(
        self,
        agent: Agent,
        test_case: Union["LLMTestCase", "ConversationalTestCase", "MLLMTestCase"]
    ) -> DimensionResult:
        """Evaluate the agent on this dimension"""
        pass
    
    @abstractmethod
    def get_metric(self):
        """Get the underlying metric for this dimension"""
        pass


class InstructionFollowing(EvaluationDimension):
    """Evaluates how well agents follow instructions"""
    
    def __init__(
        self,
        weight: float = 1.0,
        threshold: float = 0.7,
        model: Optional[Union[str, Any]] = None,
        strict_mode: bool = True
    ):
        super().__init__("Instruction Following", weight, threshold, model)
        self.strict_mode = strict_mode
        self._metric = None
    
    def get_metric(self):
        if self._metric is None:
            # Import locally to avoid circular imports
            from deepeval.metrics import GEval
            self._metric = GEval(
                name="Instruction Following",
                criteria="""Evaluate how well the agent follows the given instructions. Consider:
                1. Completeness - Does the agent address all parts of the instruction?
                2. Accuracy - Does the agent follow the instruction correctly?
                3. Format compliance - Does the agent follow any specified output format?
                4. Constraint adherence - Does the agent respect any constraints or limitations?
                5. Task understanding - Does the agent demonstrate understanding of what was asked?
                
                Score higher for agents that follow instructions precisely and completely.""",
                evaluation_params=[
                    "input",
                    "actual_output",
                    "expected_output"
                ],
                model=self.model,
                threshold=self.threshold,
                strict_mode=self.strict_mode
            )
        return self._metric
    
    def evaluate(
        self,
        agent: Agent,
        test_case: Union["LLMTestCase", "ConversationalTestCase", "MLLMTestCase"]
    ) -> DimensionResult:
        import time
        start_time = time.time()
        
        try:
            metric = self.get_metric()
            metric.measure(test_case)
            
            evaluation_time = time.time() - start_time
            
            return DimensionResult(
                dimension_name=self.name,
                score=metric.score,
                passed=metric.is_successful(),
                reasoning=metric.reason or "No reasoning provided",
                details={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "model_name": agent.model_name,
                    "threshold": self.threshold,
                    "strict_mode": self.strict_mode
                },
                evaluation_time=evaluation_time
            )
        except Exception as e:
            return DimensionResult(
                dimension_name=self.name,
                score=0.0,
                passed=False,
                reasoning=f"Evaluation failed: {str(e)}",
                details={"error": str(e)},
                evaluation_time=time.time() - start_time
            )


class HallucinationDetection(EvaluationDimension):
    """Evaluates how well agents avoid hallucination"""
    
    def __init__(
        self,
        weight: float = 1.0,
        threshold: float = 0.8,
        model: Optional[Union[str, Any]] = None,
        strict_mode: bool = False
    ):
        super().__init__("Hallucination Detection", weight, threshold, model)
        self.strict_mode = strict_mode
        self._metric = None
    
    def get_metric(self):
        if self._metric is None:
            from deepeval.metrics import HallucinationMetric
            self._metric = HallucinationMetric(
                threshold=self.threshold,
                model=self.model,
                strict_mode=self.strict_mode,
                include_reason=True
            )
        return self._metric
    
    def evaluate(
        self,
        agent: Agent,
        test_case: Union["LLMTestCase", "ConversationalTestCase", "MLLMTestCase"]
    ) -> DimensionResult:
        import time
        start_time = time.time()
        
        try:
            # Ensure test case has context for hallucination detection
            if not hasattr(test_case, 'context') or not test_case.context:
                return DimensionResult(
                    dimension_name=self.name,
                    score=0.0,
                    passed=False,
                    reasoning="No context provided for hallucination detection",
                    details={"error": "Missing context"},
                    evaluation_time=0.0
                )
            
            metric = self.get_metric()
            metric.measure(test_case)
            
            evaluation_time = time.time() - start_time
            
            return DimensionResult(
                dimension_name=self.name,
                score=metric.score,
                passed=metric.is_successful(),
                reasoning=metric.reason or "No reasoning provided",
                details={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "model_name": agent.model_name,
                    "threshold": self.threshold,
                    "strict_mode": self.strict_mode,
                    "verdicts": getattr(metric, 'verdicts', [])
                },
                evaluation_time=evaluation_time
            )
        except Exception as e:
            return DimensionResult(
                dimension_name=self.name,
                score=0.0,
                passed=False,
                reasoning=f"Evaluation failed: {str(e)}",
                details={"error": str(e)},
                evaluation_time=time.time() - start_time
            )


class AssumptionControl(EvaluationDimension):
    """Evaluates how well agents avoid unwarranted assumptions"""
    
    def __init__(
        self,
        weight: float = 1.0,
        threshold: float = 0.6,
        model: Optional[Union[str, Any]] = None
    ):
        super().__init__("Assumption Control", weight, threshold, model)
        self._metric = None
    
    def get_metric(self):
        if self._metric is None:
            from deepeval.metrics import GEval
            self._metric = GEval(
                name="Assumption Control",
                criteria="""Evaluate how well the agent avoids making unwarranted assumptions. Consider:
                1. Factual accuracy - Does the agent stick to known facts without speculation?
                2. Uncertainty handling - Does the agent acknowledge when it doesn't know something?
                3. Evidence-based responses - Does the agent base responses on provided information?
                4. Avoidance of speculation - Does the agent avoid making up details not in the input?
                5. Appropriate confidence - Does the agent express appropriate levels of confidence?
                
                Score higher for agents that avoid assumptions and stick to facts.""",
                evaluation_params=[
                    "input",
                    "actual_output",
                    "context"
                ],
                model=self.model,
                threshold=self.threshold
            )
        return self._metric
    
    def evaluate(
        self,
        agent: Agent,
        test_case: Union["LLMTestCase", "ConversationalTestCase", "MLLMTestCase"]
    ) -> DimensionResult:
        import time
        start_time = time.time()
        
        try:
            metric = self.get_metric()
            metric.measure(test_case)
            
            evaluation_time = time.time() - start_time
            
            return DimensionResult(
                dimension_name=self.name,
                score=metric.score,
                passed=metric.is_successful(),
                reasoning=metric.reason or "No reasoning provided",
                details={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "model_name": agent.model_name,
                    "threshold": self.threshold
                },
                evaluation_time=evaluation_time
            )
        except Exception as e:
            return DimensionResult(
                dimension_name=self.name,
                score=0.0,
                passed=False,
                reasoning=f"Evaluation failed: {str(e)}",
                details={"error": str(e)},
                evaluation_time=time.time() - start_time
            )


class CoherenceAccuracy(EvaluationDimension):
    """Evaluates coherence and accuracy of agent responses"""
    
    def __init__(
        self,
        weight: float = 1.0,
        threshold: float = 0.7,
        model: Optional[Union[str, Any]] = None
    ):
        super().__init__("Coherence & Accuracy", weight, threshold, model)
        self._metric = None
    
    def get_metric(self):
        if self._metric is None:
            from deepeval.metrics import GEval
            self._metric = GEval(
                name="Coherence & Accuracy",
                criteria="""Evaluate the coherence and accuracy of the agent's response. Consider:
                1. Logical consistency - Is the response logically consistent throughout?
                2. Factual accuracy - Are the facts presented accurate and verifiable?
                3. Clarity and structure - Is the response clear, well-structured, and easy to follow?
                4. Completeness - Does the response adequately address the input/question?
                5. Relevance - Is the response relevant to the input/question?
                6. Grammar and language - Is the response grammatically correct and well-written?
                
                Score higher for responses that are coherent, accurate, and well-structured.""",
                evaluation_params=[
                    "input",
                    "actual_output",
                    "expected_output"
                ],
                model=self.model,
                threshold=self.threshold
            )
        return self._metric
    
    def evaluate(
        self,
        agent: Agent,
        test_case: Union["LLMTestCase", "ConversationalTestCase", "MLLMTestCase"]
    ) -> DimensionResult:
        import time
        start_time = time.time()
        
        try:
            metric = self.get_metric()
            metric.measure(test_case)
            
            evaluation_time = time.time() - start_time
            
            return DimensionResult(
                dimension_name=self.name,
                score=metric.score,
                passed=metric.is_successful(),
                reasoning=metric.reason or "No reasoning provided",
                details={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "model_name": agent.model_name,
                    "threshold": self.threshold
                },
                evaluation_time=evaluation_time
            )
        except Exception as e:
            return DimensionResult(
                dimension_name=self.name,
                score=0.0,
                passed=False,
                reasoning=f"Evaluation failed: {str(e)}",
                details={"error": str(e)},
                evaluation_time=time.time() - start_time
            )


class DimensionEvaluator:
    """Evaluator for running multiple dimensions on agents"""
    
    def __init__(self, dimensions: List[EvaluationDimension]):
        self.dimensions = dimensions
        self.dimension_weights = {dim.name: dim.weight for dim in dimensions}
        self.total_weight = sum(self.dimension_weights.values())
    
    def evaluate_agent(
        self,
        agent: Agent,
        test_case: Union["LLMTestCase", "ConversationalTestCase", "MLLMTestCase"]
    ) -> Dict[str, DimensionResult]:
        """Evaluate a single agent across all dimensions"""
        results = {}
        
        for dimension in self.dimensions:
            try:
                result = dimension.evaluate(agent, test_case)
                results[dimension.name] = result
            except Exception as e:
                # Create error result
                results[dimension.name] = DimensionResult(
                    dimension_name=dimension.name,
                    score=0.0,
                    passed=False,
                    reasoning=f"Evaluation failed: {str(e)}",
                    details={"error": str(e)},
                    evaluation_time=0.0
                )
        
        return results
    
    def calculate_weighted_score(self, dimension_results: Dict[str, DimensionResult]) -> float:
        """Calculate weighted overall score"""
        if not dimension_results:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for name, result in dimension_results.items():
            weight = self.dimension_weights.get(name, 1.0)
            weighted_sum += result.score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0