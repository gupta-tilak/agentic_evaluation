from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .types import DomainType, Agent, AgentResult
from .dimensions import EvaluationDimension


class DomainEvaluator:
    """Domain-specific evaluation capabilities"""
    
    def __init__(self, domain: DomainType):
        self.domain = domain
        self.domain_metrics = self._load_domain_metrics()
    
    def _load_domain_metrics(self) -> Dict[str, EvaluationDimension]:
        """Load domain-specific metrics"""
        if self.domain == DomainType.QA:
            return self._get_qa_metrics()
        elif self.domain == DomainType.SUMMARIZATION:
            return self._get_summarization_metrics()
        elif self.domain == DomainType.REASONING:
            return self._get_reasoning_metrics()
        elif self.domain == DomainType.CONVERSATION:
            return self._get_conversation_metrics()
        elif self.domain == DomainType.CODE_GENERATION:
            return self._get_code_generation_metrics()
        else:
            return self._get_general_metrics()
    
    def _get_qa_metrics(self) -> Dict[str, EvaluationDimension]:
        """Get QA-specific metrics"""
        from .dimensions import GEval
        return {
            "answer_accuracy": GEval(
                name="Answer Accuracy",
                criteria="""Evaluate the accuracy of the answer to the question. Consider:
                1. Correctness - Is the answer factually correct?
                2. Completeness - Does the answer fully address the question?
                3. Relevance - Is the answer relevant to the question asked?
                4. Clarity - Is the answer clear and understandable?
                5. Evidence - Does the answer provide appropriate evidence or reasoning?
                
                Score higher for answers that are correct, complete, and well-reasoned.""",
                evaluation_params=["input", "actual_output", "expected_output"],
                threshold=0.7
            ),
            "factual_consistency": GEval(
                name="Factual Consistency",
                criteria="""Evaluate the factual consistency of the answer. Consider:
                1. Internal consistency - Are all parts of the answer consistent with each other?
                2. External consistency - Is the answer consistent with known facts?
                3. Logical consistency - Does the reasoning follow logically?
                4. Temporal consistency - Are temporal references consistent?
                
                Score higher for answers that are factually consistent throughout.""",
                evaluation_params=["input", "actual_output", "context"],
                threshold=0.6
            )
        }
    
    def _get_summarization_metrics(self) -> Dict[str, EvaluationDimension]:
        """Get summarization-specific metrics"""
        from .dimensions import GEval
        return {
            "summary_quality": GEval(
                name="Summary Quality",
                criteria="""Evaluate the quality of the summary. Consider:
                1. Conciseness - Is the summary appropriately concise?
                2. Completeness - Does it cover all important points?
                3. Coherence - Is the summary coherent and well-structured?
                4. Clarity - Is the summary clear and easy to understand?
                5. Objectivity - Does it maintain objectivity?
                
                Score higher for summaries that are concise, complete, and coherent.""",
                evaluation_params=["input", "actual_output", "expected_output"],
                threshold=0.7
            ),
            "information_retention": GEval(
                name="Information Retention",
                criteria="""Evaluate how well the summary retains key information. Consider:
                1. Key points - Are the main points from the original text included?
                2. Important details - Are important details preserved?
                3. Context preservation - Is important context maintained?
                4. Factual accuracy - Are facts accurately represented?
                
                Score higher for summaries that retain more important information.""",
                evaluation_params=["input", "actual_output", "context"],
                threshold=0.6
            )
        }
    
    def _get_reasoning_metrics(self) -> Dict[str, EvaluationDimension]:
        """Get reasoning-specific metrics"""
        from .dimensions import GEval
        return {
            "logical_reasoning": GEval(
                name="Logical Reasoning",
                criteria="""Evaluate the logical reasoning quality. Consider:
                1. Logical validity - Are the logical steps valid?
                2. Premise quality - Are the premises sound and relevant?
                3. Conclusion quality - Does the conclusion follow from the premises?
                4. Reasoning clarity - Is the reasoning process clear?
                5. Fallacy avoidance - Are logical fallacies avoided?
                
                Score higher for responses with strong logical reasoning.""",
                evaluation_params=["input", "actual_output", "expected_output"],
                threshold=0.7
            ),
            "problem_solving": GEval(
                name="Problem Solving",
                criteria="""Evaluate problem-solving ability. Consider:
                1. Problem understanding - Is the problem correctly understood?
                2. Solution approach - Is the approach to solving appropriate?
                3. Solution quality - Is the solution correct and complete?
                4. Alternative consideration - Are alternative approaches considered?
                5. Verification - Is the solution verified or checked?
                
                Score higher for responses that demonstrate good problem-solving skills.""",
                evaluation_params=["input", "actual_output", "expected_output"],
                threshold=0.6
            )
        }
    
    def _get_conversation_metrics(self) -> Dict[str, EvaluationDimension]:
        """Get conversation-specific metrics"""
        from .dimensions import GEval
        return {
            "conversational_quality": GEval(
                name="Conversational Quality",
                criteria="""Evaluate the quality of conversational responses. Consider:
                1. Relevance - Is the response relevant to the conversation?
                2. Context awareness - Does it show awareness of conversation context?
                3. Naturalness - Does it sound natural and human-like?
                4. Engagement - Is it engaging and appropriate?
                5. Continuity - Does it maintain conversation flow?
                
                Score higher for responses that are natural and contextually appropriate.""",
                evaluation_params=["input", "actual_output", "expected_output"],
                threshold=0.7
            ),
            "empathy_understanding": GEval(
                name="Empathy and Understanding",
                criteria="""Evaluate empathy and understanding in responses. Consider:
                1. Emotional recognition - Does it recognize emotional cues?
                2. Appropriate response - Is the response emotionally appropriate?
                3. Understanding depth - Does it show deep understanding?
                4. Supportiveness - Is it supportive and helpful?
                5. Sensitivity - Is it sensitive to the user's needs?
                
                Score higher for responses that show empathy and understanding.""",
                evaluation_params=["input", "actual_output", "expected_output"],
                threshold=0.6
            )
        }
    
    def _get_code_generation_metrics(self) -> Dict[str, EvaluationDimension]:
        """Get code generation-specific metrics"""
        from .dimensions import GEval
        return {
            "code_correctness": GEval(
                name="Code Correctness",
                criteria="""Evaluate the correctness of generated code. Consider:
                1. Syntax correctness - Is the code syntactically correct?
                2. Logic correctness - Does the code implement the required logic?
                3. Functionality - Does the code work as intended?
                4. Edge case handling - Are edge cases handled appropriately?
                5. Error handling - Is error handling implemented?
                
                Score higher for code that is correct and functional.""",
                evaluation_params=["input", "actual_output", "expected_output"],
                threshold=0.7
            ),
            "code_quality": GEval(
                name="Code Quality",
                criteria="""Evaluate the quality of generated code. Consider:
                1. Readability - Is the code readable and well-formatted?
                2. Efficiency - Is the code efficient?
                3. Best practices - Does it follow coding best practices?
                4. Documentation - Is the code well-documented?
                5. Maintainability - Is the code maintainable?
                
                Score higher for code that follows best practices and is well-structured.""",
                evaluation_params=["input", "actual_output", "expected_output"],
                threshold=0.6
            )
        }
    
    def _get_general_metrics(self) -> Dict[str, EvaluationDimension]:
        """Get general-purpose metrics"""
        from .dimensions import GEval
        return {
            "general_quality": GEval(
                name="General Quality",
                criteria="""Evaluate the general quality of the response. Consider:
                1. Relevance - Is the response relevant to the input?
                2. Accuracy - Is the response accurate?
                3. Completeness - Does it fully address the input?
                4. Clarity - Is it clear and understandable?
                5. Usefulness - Is it useful and helpful?
                
                Score higher for responses that are relevant, accurate, and useful.""",
                evaluation_params=["input", "actual_output", "expected_output"],
                threshold=0.7
            )
        }
    
    def evaluate_domain_specific(
        self,
        agents: List[Agent],
        test_cases: List[Any],
        evaluator: 'AgenticEvaluator'
    ) -> Dict[str, Any]:
        """Evaluate agents using domain-specific metrics"""
        domain_results = {
            "domain": self.domain.value,
            "agent_count": len(agents),
            "metrics_used": list(self.domain_metrics.keys()),
            "results": {}
        }
        
        # Run evaluation for each agent
        for agent in agents:
            agent_scores = {}
            
            for metric_name, metric in self.domain_metrics.items():
                try:
                    # This would need to be integrated with the main evaluator
                    # For now, we'll create a placeholder structure
                    agent_scores[metric_name] = {
                        "score": 0.0,  # Placeholder
                        "passed": False,  # Placeholder
                        "reasoning": "Domain-specific evaluation not yet implemented"
                    }
                except Exception as e:
                    agent_scores[metric_name] = {
                        "score": 0.0,
                        "passed": False,
                        "reasoning": f"Error: {str(e)}"
                    }
            
            domain_results["results"][agent.id] = {
                "agent_name": agent.name,
                "scores": agent_scores
            }
        
        return domain_results
    
    def get_domain_benchmarks(self) -> Dict[str, float]:
        """Get domain-specific benchmark scores"""
        benchmarks = {
            DomainType.QA: {
                "excellent": 0.9,
                "good": 0.7,
                "fair": 0.5,
                "poor": 0.3
            },
            DomainType.SUMMARIZATION: {
                "excellent": 0.85,
                "good": 0.65,
                "fair": 0.45,
                "poor": 0.25
            },
            DomainType.REASONING: {
                "excellent": 0.9,
                "good": 0.7,
                "fair": 0.5,
                "poor": 0.3
            },
            DomainType.CONVERSATION: {
                "excellent": 0.8,
                "good": 0.6,
                "fair": 0.4,
                "poor": 0.2
            },
            DomainType.CODE_GENERATION: {
                "excellent": 0.9,
                "good": 0.7,
                "fair": 0.5,
                "poor": 0.3
            },
            DomainType.GENERAL: {
                "excellent": 0.8,
                "good": 0.6,
                "fair": 0.4,
                "poor": 0.2
            }
        }
        
        return benchmarks.get(self.domain, benchmarks[DomainType.GENERAL])
    
    def get_domain_requirements(self) -> Dict[str, Any]:
        """Get domain-specific requirements and guidelines"""
        requirements = {
            DomainType.QA: {
                "description": "Question Answering",
                "key_requirements": [
                    "Accurate and factual responses",
                    "Complete answers that address all parts of the question",
                    "Clear and understandable explanations",
                    "Appropriate use of evidence and reasoning"
                ],
                "evaluation_focus": "Accuracy, completeness, and clarity"
            },
            DomainType.SUMMARIZATION: {
                "description": "Text Summarization",
                "key_requirements": [
                    "Concise yet complete summaries",
                    "Preservation of key information",
                    "Coherent and well-structured output",
                    "Appropriate length and detail level"
                ],
                "evaluation_focus": "Conciseness, completeness, and coherence"
            },
            DomainType.REASONING: {
                "description": "Logical Reasoning",
                "key_requirements": [
                    "Valid logical steps and reasoning",
                    "Sound premises and conclusions",
                    "Clear problem-solving approach",
                    "Avoidance of logical fallacies"
                ],
                "evaluation_focus": "Logical validity and problem-solving ability"
            },
            DomainType.CONVERSATION: {
                "description": "Conversational AI",
                "key_requirements": [
                    "Natural and engaging responses",
                    "Context awareness and continuity",
                    "Appropriate emotional responses",
                    "Empathetic and supportive communication"
                ],
                "evaluation_focus": "Naturalness, context awareness, and empathy"
            },
            DomainType.CODE_GENERATION: {
                "description": "Code Generation",
                "key_requirements": [
                    "Syntactically and logically correct code",
                    "Implementation of required functionality",
                    "Following coding best practices",
                    "Proper error handling and edge cases"
                ],
                "evaluation_focus": "Correctness, functionality, and code quality"
            },
            DomainType.GENERAL: {
                "description": "General Purpose",
                "key_requirements": [
                    "Relevant and accurate responses",
                    "Clear and complete answers",
                    "Appropriate tone and style",
                    "Useful and helpful information"
                ],
                "evaluation_focus": "Relevance, accuracy, and usefulness"
            }
        }
        
        return requirements.get(self.domain, requirements[DomainType.GENERAL])
    
    def suggest_improvements(
        self,
        agent_result: AgentResult,
        domain: DomainType
    ) -> List[str]:
        """Suggest domain-specific improvements for an agent"""
        suggestions = []
        
        if domain == DomainType.QA:
            if agent_result.scores.get("answer_accuracy", 0) < 0.6:
                suggestions.append("Improve answer accuracy by focusing on factual correctness")
            if agent_result.scores.get("factual_consistency", 0) < 0.6:
                suggestions.append("Enhance factual consistency by cross-referencing information")
        
        elif domain == DomainType.SUMMARIZATION:
            if agent_result.scores.get("summary_quality", 0) < 0.6:
                suggestions.append("Improve summary quality by balancing conciseness and completeness")
            if agent_result.scores.get("information_retention", 0) < 0.6:
                suggestions.append("Better preserve key information in summaries")
        
        elif domain == DomainType.REASONING:
            if agent_result.scores.get("logical_reasoning", 0) < 0.6:
                suggestions.append("Strengthen logical reasoning by improving step-by-step analysis")
            if agent_result.scores.get("problem_solving", 0) < 0.6:
                suggestions.append("Enhance problem-solving by considering multiple approaches")
        
        elif domain == DomainType.CONVERSATION:
            if agent_result.scores.get("conversational_quality", 0) < 0.6:
                suggestions.append("Improve conversational quality by being more natural and engaging")
            if agent_result.scores.get("empathy_understanding", 0) < 0.6:
                suggestions.append("Develop better empathy and emotional understanding")
        
        elif domain == DomainType.CODE_GENERATION:
            if agent_result.scores.get("code_correctness", 0) < 0.6:
                suggestions.append("Improve code correctness by better syntax and logic validation")
            if agent_result.scores.get("code_quality", 0) < 0.6:
                suggestions.append("Enhance code quality by following best practices")
        
        return suggestions
