"""Quality evaluator calculating numeric pass indicators."""

class QualityEvaluator:
    def __init__(self, thresholds_policy):
        self.thresholds = thresholds_policy

    def evaluate(self, validation_passed, error_count):
        """Computes a quality score and determines grade compliance."""
        score = 100
        
        if not validation_passed:
            score -= 30
        score -= min(50, error_count * 15)
        
        min_threshold = self.thresholds.get("minimum_score", 70)
        rec_threshold = self.thresholds.get("recommended_score", 85)
        
        grade = "FAIL"
        if score >= rec_threshold:
            grade = "RECOMMENDED"
        elif score >= min_threshold:
            grade = "MINIMUM"
            
        return {
            "score": score,
            "grade": grade,
            "confidence": min(100, score + 10)  # Mock confidence formula
        }
