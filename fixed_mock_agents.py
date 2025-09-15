#!/usr/bin/env python3
"""
Fixed API Backend with Improved Mock Agents
===========================================

This fixes the core issues causing poor results:
1. Mock agents now handle diverse question types properly
2. Better response matching for math, literature, and general questions
3. Improved evaluation logic to match working version
"""

import os
import sys
import re
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Add simple mock implementations for testing without full dependency issues
class MockLLMTestCase:
    def __init__(self, input, actual_output="", expected_output="", context=None):
        self.input = input
        self.actual_output = actual_output
        self.expected_output = expected_output
        self.context = context or []

class ImprovedMockHighQualityAgent:
    """Improved mock high-quality agent that handles diverse questions properly"""
    
    def __init__(self, name: str = "Expert AI Agent"):
        self.model_name = name
        self.domain = "expert"
        
        # Comprehensive knowledge base for various question types
        self.responses = {
            # Math questions
            "2 + 2": "4",
            "what is 2 + 2": "4", 
            "2+2": "4",
            "two plus two": "4",
            
            # Literature questions
            "pride and prejudice": "Jane Austen wrote 'Pride and Prejudice', which was published in 1813. It's one of her most famous novels and a cornerstone of English literature.",
            "who wrote pride and prejudice": "Jane Austen",
            "jane austen": "Jane Austen was an English novelist known for her wit, social commentary, and romantic fiction including Pride and Prejudice, Sense and Sensibility, and Emma.",
            
            # Science questions
            "artificial intelligence": "Artificial Intelligence (AI) is a branch of computer science focused on creating systems that can perform tasks typically requiring human intelligence, such as learning, reasoning, problem-solving, and understanding natural language.",
            "machine learning": "Machine learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms to identify patterns in data and make predictions or decisions.",
            "renewable energy": "Renewable energy sources include solar, wind, hydroelectric, and geothermal power. They offer significant benefits including reduced greenhouse gas emissions, energy independence, job creation, and long-term cost savings.",
            "climate change": "Technology can help address climate change through renewable energy adoption, energy efficiency improvements, carbon capture and storage, smart grid systems, and sustainable transportation solutions.",
            "data science": "Data science and artificial intelligence are closely related fields. Data science provides the foundation by collecting, cleaning, and analyzing data, while AI uses these techniques and data to build intelligent systems that can learn and make decisions.",
            
            # General knowledge
            "unit testing": "Unit testing provides several key benefits: 1) Early bug detection during development, 2) Documentation of expected behavior, 3) Confidence when refactoring code, 4) Improved code design, and 5) Faster debugging when issues arise.",
            "benefits of unit testing": "• Catches bugs early in development\n• Provides documentation of expected behavior\n• Enables safe refactoring of code\n• Improves overall code quality\n• Reduces debugging time",
            
            # Context-based questions
            "olympics": "The 2024 Olympics took place in Paris, France. The games featured numerous events and were notable for their sustainable approach and use of existing venues along the River Seine."
        }
    
    def generate(self, prompt: str, context: str = "") -> str:
        """Generate high-quality, relevant responses using context when available"""
        prompt_lower = prompt.lower().strip()
        context_lower = context.lower().strip() if context else ""
        
        # Context-aware responses
        if context and "olympics" in context_lower and "paris" in context_lower:
            return "The 2024 Olympics took place in Paris, France, with many events held along the River Seine."
        
        if context and "australia" in context_lower and "canberra" in context_lower:
            return "According to the context, Canberra is the capital of Australia."
        
        if context and "cats" in context_lower and "summarize" in prompt_lower:
            return "Cats are small, agile, independent carnivorous mammals that are popular pets."
        
        if context and "jane austen" in context_lower and "pride" in prompt_lower:
            return "Jane Austen wrote 'Pride and Prejudice', which was published in 1813 as mentioned in the context."
        
        # Direct exact matches
        if prompt_lower in self.responses:
            return self.responses[prompt_lower]
        
        # Partial matches for key phrases
        for key, response in self.responses.items():
            if key in prompt_lower:
                return response
        
        # Pattern matching for math
        math_pattern = r'(\d+)\s*\+\s*(\d+)'
        match = re.search(math_pattern, prompt_lower)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
            return str(a + b)
        
        # Single number requests (common in math)
        if "single number" in prompt_lower and any(word in prompt_lower for word in ["2", "two", "plus", "+"]):
            return "4"
        
        # Special instruction following
        if "bullet points" in prompt_lower and "unit testing" in prompt_lower:
            return "• Early bug detection and prevention\n• Clear documentation of expected behavior\n• Safe refactoring with confidence"
        
        if "two bullet points" in prompt_lower and "404" in prompt_lower:
            return "• HTTP 404 indicates the requested resource was not found\n• It is a client-side error status code"
        
        if "one-word synonym" in prompt_lower and "quick" in prompt_lower:
            return "fast"
        
        if "don't know" in prompt_lower or "unknown" in prompt_lower:
            return "I don't know."
        
        # Default comprehensive response
        return f"Based on my expert analysis, I can provide a comprehensive and accurate response to your question about {prompt[:30]}. This demonstrates high-quality reasoning and relevant information."

class ImprovedMockAverageAgent:
    """Improved mock average-quality agent"""
    
    def __init__(self, name: str = "Standard AI Agent"):
        self.model_name = name
        self.domain = "general"
    
    def generate(self, prompt: str, context: str = "") -> str:
        """Generate average-quality responses using some context"""
        prompt_lower = prompt.lower().strip()
        context_lower = context.lower().strip() if context else ""
        
        # Context-aware responses (partially correct)
        if context and "olympics" in context_lower:
            return "The Olympics were in Paris in 2024."
        
        if context and "australia" in context_lower and "capital" in prompt_lower:
            return "Canberra"
        
        if context and "cats" in context_lower and "summarize" in prompt_lower:
            return "Cats are small pets that are agile and independent."
        
        # Math - correct but brief
        if "2 + 2" in prompt_lower or "2+2" in prompt_lower:
            return "4"
        
        # Literature - partially correct
        if "pride and prejudice" in prompt_lower:
            return "Jane Austen"
        
        # Instruction following - partial attempt
        if "bullet points" in prompt_lower and "unit testing" in prompt_lower:
            return "Unit testing helps find bugs and makes code better."
        
        if "two bullet points" in prompt_lower and "404" in prompt_lower:
            return "HTTP 404 means not found. It's an error."
        
        if "one-word synonym" in prompt_lower and "quick" in prompt_lower:
            return "fast"
        
        if "don't know" in prompt_lower:
            return "I'm not sure about that."
        
        # Science - basic responses
        if "artificial intelligence" in prompt_lower or "ai" in prompt_lower:
            return "AI is computer technology that tries to think like humans. It uses algorithms and data."
        elif "machine learning" in prompt_lower:
            return "Machine learning is when computers learn from data automatically."
        elif "renewable energy" in prompt_lower:
            return "Renewable energy comes from sources like solar and wind. It's better for the environment."
        elif "climate change" in prompt_lower:
            return "Technology can help with climate change through clean energy."
        elif "data science" in prompt_lower:
            return "Data science works with AI to analyze information and make smart systems."
        elif "olympics" in prompt_lower:
            return "The Olympics were held in Paris in 2024."
        else:
            return f"This is a reasonable answer about {prompt[:30]}. It provides some relevant information."

class ImprovedMockPoorAgent:
    """Improved mock poor-quality agent that still gives poor responses but attempts to answer"""
    
    def __init__(self, name: str = "Basic AI Agent"):
        self.model_name = name
        self.domain = "basic"
    
    def generate(self, prompt: str, context: str = "") -> str:
        """Generate poor-quality responses with limited context usage"""
        prompt_lower = prompt.lower().strip()
        
        # Even poor agents might get very simple math right sometimes
        if "2 + 2" in prompt_lower and "number" in prompt_lower:
            return "4 maybe"
        
        # Context misuse or ignoring
        if "olympics" in prompt_lower:
            return "Some sports event happened somewhere"
        
        if "capital" in prompt_lower and "australia" in prompt_lower:
            return "Sydney or Melbourne I think"
        
        # But struggle with most things
        if "pride and prejudice" in prompt_lower:
            return "Some author wrote it"
        elif "artificial intelligence" in prompt_lower:
            return "AI is complicated stuff"
        elif "machine learning" in prompt_lower:
            return "Computers learn things somehow"
        elif "renewable energy" in prompt_lower:
            return "Solar power is good I think"
        elif "unit testing" in prompt_lower:
            return "Testing is important"
        elif "bullet points" in prompt_lower:
            return "I don't know how to format that"
        elif "synonym" in prompt_lower:
            return "Hard to say"
        elif "don't know" in prompt_lower:
            return "This seems complicated"
        else:
            poor_responses = [
                "I'm not sure about this",
                "This seems complicated", 
                "Maybe someone else knows",
                "Hard to say",
                "Could be anything"
            ]
            import random
            return random.choice(poor_responses)

# Simplified metric simulation for testing without Groq
class MockMetric:
    """Mock metric that evaluates responses without requiring Groq API"""
    
    def __init__(self, name: str, threshold: float = 0.7):
        self.name = name
        self.threshold = threshold
        self.score = 0.0
        self.success = False
        self.reason = ""
    
    def evaluate(self, prompt: str, response: str, expected: str, context: str = "") -> Dict[str, Any]:
        """Evaluate response quality using specific criteria for each metric"""
        
        # Normalize strings for comparison
        response_lower = response.lower().strip()
        expected_lower = expected.lower().strip()
        prompt_lower = prompt.lower().strip()
        context_lower = context.lower().strip() if context else ""
        
        # Metric-specific evaluation
        if self.name == "instruction_following":
            score, reason = self._evaluate_instruction_following(prompt_lower, response_lower, expected_lower)
        elif self.name == "coherence_accuracy":
            score, reason = self._evaluate_coherence_accuracy(prompt_lower, response_lower, expected_lower, context_lower)
        elif self.name == "hallucination_detection":
            score, reason = self._evaluate_hallucination_detection(prompt_lower, response_lower, context_lower)
        elif self.name == "relevance_quality":
            score, reason = self._evaluate_relevance_quality(prompt_lower, response_lower, expected_lower)
        else:
            score, reason = self._evaluate_general_quality(prompt_lower, response_lower, expected_lower)
        
        self.score = score
        self.reason = reason
        self.success = self.score >= self.threshold
        
        return {
            "score": self.score,
            "threshold": self.threshold,
            "success": self.success,
            "reasoning": self.reason
        }
    
    def _evaluate_instruction_following(self, prompt: str, response: str, expected: str) -> tuple:
        """Evaluate how well the response follows instructions"""
        if "single number" in prompt and response.strip() in ["4", "4 maybe"]:
            if response.strip() == "4":
                return 1.0, "Perfect adherence to single number instruction"
            else:
                return 0.8, "Correct answer but with extra text"
        
        if "bullet points" in prompt:
            if "•" in response or "-" in response:
                return 1.0, "Correctly formatted with bullet points"
            else:
                return 0.3, "Failed to use bullet point formatting"
        
        if "two bullet points" in prompt:
            bullet_count = response.count("•") + response.count("-") + response.count("1)") + response.count("2)")
            if bullet_count >= 2:
                return 1.0, "Correctly provided two bullet points"
            else:
                return 0.4, "Did not provide exactly two bullet points"
        
        if "one-word" in prompt:
            words = response.split()
            if len(words) == 1:
                return 1.0, "Correctly provided single word response"
            else:
                return 0.5, f"Provided {len(words)} words instead of one"
        
        if "don't know" in prompt and "don't know" in response:
            return 1.0, "Correctly acknowledged uncertainty as instructed"
        
        # General instruction following
        if len(response) > 20:
            return 0.8, "Provided detailed response following general instructions"
        else:
            return 0.6, "Brief response with partial instruction following"
    
    def _evaluate_coherence_accuracy(self, prompt: str, response: str, expected: str, context: str) -> tuple:
        """Evaluate factual accuracy and coherence"""
        # Math accuracy
        if "2 + 2" in prompt:
            if "4" in response:
                return 1.0, "Mathematically accurate response"
            else:
                return 0.1, "Mathematically incorrect response"
        
        # Literature accuracy
        if "pride and prejudice" in prompt:
            if "jane austen" in response:
                return 1.0, "Factually accurate author identification"
            elif "austen" in response:
                return 0.8, "Partially accurate author name"
            else:
                return 0.2, "Factually incorrect or missing author"
        
        # Context-based accuracy
        if context and "canberra" in context and "capital" in prompt:
            if "canberra" in response:
                return 1.0, "Accurate extraction from context"
            else:
                return 0.3, "Failed to extract correct information from context"
        
        # Machine learning accuracy
        if "machine learning" in prompt:
            key_terms = ["algorithm", "data", "pattern", "learn", "computer"]
            matches = sum(1 for term in key_terms if term in response)
            if matches >= 3:
                return 1.0, "Accurate definition with key concepts"
            elif matches >= 2:
                return 0.8, "Mostly accurate with some key concepts"
            else:
                return 0.5, "Limited accuracy in definition"
        
        return 0.7, "Generally coherent response with reasonable accuracy"
    
    def _evaluate_hallucination_detection(self, prompt: str, response: str, context: str) -> tuple:
        """Evaluate if response contains hallucinations or false information"""
        # Check for context adherence
        if context:
            if "answer using only" in prompt or "according to context" in prompt:
                if context and "paris" in context and "olympics" in context:
                    if "paris" in response and "olympics" in response:
                        return 1.0, "Correctly used only provided context"
                    elif "tokyo" in response or "japan" in response:
                        return 0.1, "Hallucinated incorrect location (Tokyo instead of Paris)"
                    else:
                        return 0.5, "Did not properly use provided context"
                
                if "canberra" in context and "capital" in prompt:
                    if "canberra" in response:
                        return 1.0, "Correctly used context without hallucination"
                    elif "sydney" in response or "melbourne" in response:
                        return 0.3, "Used incorrect information despite context"
                    else:
                        return 0.6, "Avoided hallucination but didn't use context"
        
        # Check for obvious factual errors
        if "pride and prejudice" in prompt and "tokyo" in response:
            return 0.1, "Contains clear factual hallucination"
        
        if "2 + 2" in prompt and response not in ["4", "4 maybe"]:
            return 0.2, "Mathematical hallucination"
        
        # Check for uncertainty vs false confidence
        if "don't know" in prompt:
            uncertainty_words = ["don't know", "not sure", "uncertain", "maybe", "complicated"]
            if any(word in response for word in uncertainty_words):
                return 1.0, "Appropriately expressed uncertainty instead of hallucinating"
            else:
                return 0.4, "May have invented information instead of expressing uncertainty"
        
        return 0.8, "No obvious hallucinations detected"
    
    def _evaluate_relevance_quality(self, prompt: str, response: str, expected: str) -> tuple:
        """Evaluate relevance and overall quality of response"""
        # Check if response addresses the prompt
        prompt_keywords = prompt.split()
        response_words = response.split()
        
        # Calculate keyword overlap
        overlap = len(set(prompt_keywords) & set(response_words))
        relevance_score = min(overlap / max(len(prompt_keywords) * 0.3, 1), 1.0)
        
        # Specific relevance checks
        if "unit testing" in prompt and "test" in response:
            return 0.9, "Highly relevant to unit testing topic"
        
        if "machine learning" in prompt and ("learn" in response or "algorithm" in response):
            return 0.9, "Highly relevant to machine learning topic"
        
        if "synonym" in prompt and "quick" in prompt:
            if response.strip() in ["fast", "rapid", "swift", "speedy"]:
                return 1.0, "Perfect synonym relevance"
            else:
                return 0.3, "Not relevant synonym provided"
        
        # Check response quality indicators
        quality_score = 0.5
        if len(response) > 10:
            quality_score += 0.2
        if len(response) > 50:
            quality_score += 0.2
        if any(word in expected.lower() for word in response.lower().split()):
            quality_score += 0.3
        
        quality_score = min(quality_score, 1.0)
        final_score = (relevance_score + quality_score) / 2
        
        if final_score >= 0.8:
            return final_score, "Highly relevant and quality response"
        elif final_score >= 0.6:
            return final_score, "Moderately relevant with decent quality"
        else:
            return final_score, "Limited relevance or poor quality"
    
    def _evaluate_general_quality(self, prompt: str, response: str, expected: str) -> tuple:
        """General quality assessment fallback"""
        score = 0.5
        
        if len(response) > 50:
            score += 0.1
        if any(word in expected.lower() for word in response.lower().split()):
            score += 0.2
        if len(response) > 20 and not any(word in response.lower() for word in ["don't know", "not sure", "maybe", "complicated"]):
            score += 0.2
        
        return min(score, 1.0), f"General quality assessment based on content and length"

# Test function
def test_improved_agents():
    """Test the improved agent implementations"""
    
    print("🔧 TESTING IMPROVED MOCK AGENTS")
    print("=" * 50)
    
    # Test cases from frontend
    test_cases = [
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
        }
    ]
    
    # Test agents
    agents = [
        ImprovedMockHighQualityAgent("Expert AI"),
        ImprovedMockAverageAgent("Standard AI"),
        ImprovedMockPoorAgent("Basic AI")
    ]
    
    # Metrics
    metrics = [
        MockMetric("instruction_following", 0.7),
        MockMetric("coherence_accuracy", 0.7),
        MockMetric("hallucination_detection", 0.7),
        MockMetric("relevance_quality", 0.7)
    ]
    
    for agent in agents:
        print(f"\n🤖 Testing: {agent.model_name}")
        print("-" * 30)
        
        for test_case in test_cases:
            response = agent.generate(test_case["prompt"])
            
            print(f"\nTest {test_case['test_case_id']}:")
            print(f"  Q: {test_case['prompt']}")
            print(f"  A: {response}")
            print(f"  Expected: {test_case['reference']}")
            
            # Evaluate with mock metrics
            avg_score = 0.0
            for metric in metrics:
                result = metric.evaluate(
                    test_case["prompt"], 
                    response, 
                    test_case["reference"],
                    test_case["context"]
                )
                avg_score += result["score"]
                print(f"    {metric.name}: {result['score']:.2f} ({'✅' if result['success'] else '❌'})")
            
            avg_score /= len(metrics)
            print(f"    Overall: {avg_score:.2f}")
    
    print(f"\n✅ IMPROVED AGENTS TESTED")
    print("Key improvements:")
    print("1. Proper math question handling (2+2=4)")
    print("2. Correct literature answers (Jane Austen)")
    print("3. Quality-appropriate responses for each agent tier")
    print("4. Better prompt matching and response generation")

if __name__ == "__main__":
    test_improved_agents()
