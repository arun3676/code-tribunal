from typing import List, Dict, Any
import statistics
from .models import CodeAnalysisResult, ModelEvaluationResult

class ModelEvaluator:
    """Evaluates and compares performance of different LLM models."""
    
    def __init__(self):
        self.results: Dict[str, List[CodeAnalysisResult]] = {}
        
    def add_result(self, result: CodeAnalysisResult):
        """Add a single analysis result to the evaluation."""
        if result.model_name not in self.results:
            self.results[result.model_name] = []
        self.results[result.model_name].append(result)
        
    def get_evaluation(self, model_name: str) -> ModelEvaluationResult:
        """Get evaluation metrics for a specific model."""
        if model_name not in self.results:
            raise ValueError(f"No results found for model: {model_name}")
            
        results = self.results[model_name]
        
        return ModelEvaluationResult(
            model_name=model_name,
            average_quality_score=statistics.mean(r.code_quality_score for r in results),
            average_execution_time=statistics.mean(r.execution_time for r in results),
            success_rate=len([r for r in results if r.code_quality_score > 0]) / len(results),
            analysis_samples=results
        )
        
    def compare_models(self) -> Dict[str, ModelEvaluationResult]:
        """Compare performance across all models."""
        return {
            model: self.get_evaluation(model)
            for model in self.results
        }