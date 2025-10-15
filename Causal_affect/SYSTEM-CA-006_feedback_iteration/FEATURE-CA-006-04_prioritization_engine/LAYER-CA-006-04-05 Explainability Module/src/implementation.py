```python
import json
from typing import Dict, List, Tuple, Any


class ExplainabilityModule:
    """Module for explaining prioritization decisions and score breakdowns."""
    
    def __init__(self):
        """Initialize the explainability module."""
        self.weight_descriptions = {
            'impact': 'Expected business impact and value generation',
            'feasibility': 'Technical and operational feasibility',
            'alignment': 'Strategic alignment with business goals',
            'urgency': 'Time sensitivity and market timing',
            'risk': 'Associated risks and uncertainties',
            'resources': 'Resource requirements and availability',
            'dependencies': 'External dependencies and prerequisites',
            'roi': 'Return on investment potential',
            'innovation': 'Innovation and competitive advantage',
            'scalability': 'Scalability and growth potential'
        }
    
    def generate_score_breakdown(self, venture_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete score breakdown with all components.
        
        Args:
            venture_data: Dictionary containing venture scores and metadata
            
        Returns:
            Dictionary with complete score breakdown
        """
        components = venture_data.get('components', {})
        weights = venture_data.get('weights', {})
        total_score = venture_data.get('total_score', 0)
        
        breakdown = {
            'total_score': total_score,
            'components': {},
            'weighted_contributions': {},
            'top_factors': []
        }
        
        # Calculate component details
        weighted_scores = {}
        for component, score in components.items():
            weight = weights.get(component, 0)
            weighted_score = score * weight
            weighted_scores[component] = weighted_score
            
            breakdown['components'][component] = {
                'raw_score': score,
                'weight': weight,
                'weighted_score': weighted_score,
                'description': self.weight_descriptions.get(component, f'{component} factor')
            }
            
            breakdown['weighted_contributions'][component] = weighted_score
        
        # Identify top 3 factors
        sorted_factors = sorted(
            weighted_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        breakdown['top_factors'] = [
            {
                'factor': factor,
                'weighted_score': score,
                'raw_score': components.get(factor, 0),
                'weight': weights.get(factor, 0),
                'description': self.weight_descriptions.get(factor, f'{factor} factor')
            }
            for factor, score in sorted_factors[:3]
        ]
        
        return breakdown
    
    def generate_rationale(self, venture_data: Dict[str, Any]) -> str:
        """
        Generate natural language decision rationale.
        
        Args:
            venture_data: Dictionary containing venture scores and metadata
            
        Returns:
            Natural language rationale string
        """
        name = venture_data.get('name', 'This venture')
        total_score = venture_data.get('total_score', 0)
        components = venture_data.get('components', {})
        weights = venture_data.get('weights', {})
        
        # Calculate weighted scores for ranking
        weighted_scores = {
            component: score * weights.get(component, 0)
            for component, score in components.items()
        }
        
        # Get top 3 factors
        top_factors = sorted(
            weighted_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Generate rationale
        rationale_parts = []
        
        # Opening statement
        score_level = self._get_score_level(total_score)
        rationale_parts.append(
            f"{name} received a {score_level} priority score of {total_score:.2f}."
        )
        
        # Top factors analysis
        if top_factors:
            rationale_parts.append("The key factors driving this score are:")
            
            for i, (factor, weighted_score) in enumerate(top_factors, 1):
                raw_score = components.get(factor, 0)
                weight = weights.get(factor, 0)
                description = self.weight_descriptions.get(factor, factor)
                
                contribution_pct = (weighted_score / total_score * 100) if total_score > 0 else 0
                
                factor_desc = self._get_factor_description(factor, raw_score, weight)
                rationale_parts.append(
                    f"{i}. {factor.capitalize()} ({description}): "
                    f"Score of {raw_score:.2f} with weight {weight:.2f}, "
                    f"contributing {contribution_pct:.1f}% to the total. {factor_desc}"
                )
        
        # Conclusion
        conclusion = self._generate_conclusion(total_score, top_factors, components)
        rationale_parts.append(conclusion)
        
        return " ".join(rationale_parts)
    
    def highlight_top_factors(self, venture_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Highlight top 3 factors influencing the score.
        
        Args:
            venture_data: Dictionary containing venture scores and metadata
            
        Returns:
            List of top 3 factors with details
        """
        components = venture_data.get('components', {})
        weights = venture_data.get('weights', {})
        
        # Calculate weighted scores
        weighted_scores = {
            component: score * weights.get(component, 0)
            for component, score in components.items()
        }
        
        # Sort and get top 3
        sorted_factors = sorted(
            weighted_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        top_factors = []
        for rank, (factor, weighted_score) in enumerate(sorted_factors, 1):
            raw_score = components.get(factor, 0)
            weight = weights.get(factor, 0)
            
            top_factors.append({
                'rank': rank,
                'factor': factor,
                'raw_score': raw_score,
                'weight': weight,
                'weighted_score': weighted_score,
                'description': self.weight_descriptions.get(factor, f'{factor} factor'),
                'impact_level': self._get_impact_level(raw_score)
            })
        
        return top_factors
    
    def explain_decision(self, venture_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete explanation of prioritization decision.
        
        Args:
            venture_data: Dictionary containing venture scores and metadata
            
        Returns:
            Dictionary with complete explanation including breakdown, rationale, and top factors
        """
        return {
            'score_breakdown': self.generate_score_breakdown(venture_data),
            'rationale': self.generate_rationale(venture_data),
            'top_factors': self.highlight_top_factors(venture_data)
        }
    
    def _get_score_level(self, score: float) -> str:
        """Get descriptive level for score."""
        if score >= 8.0:
            return "high"
        elif score >= 6.0:
            return "medium-high"
        elif score >= 4.0:
            return "medium"
        elif score >= 2.0:
            return "low-medium"
        else:
            return "low"
    
    def _get_impact_level(self, score: float) -> str:
        """Get impact level for a component score."""
        if score >= 8.0:
            return "very high"
        elif score >= 6.0:
            return "high"
        elif score >= 4.0:
            return "moderate"
        elif score >= 2.0:
            return "low"
        else:
            return "very low"
    
    def _get_factor_description(self, factor: str, score: float, weight: float) -> str:
        """Generate description for a factor."""
        impact = self._get_impact_level(score)
        
        if score >= 7.0:
            return f"This {impact} score indicates strong performance in this area."
        elif score >= 5.0:
            return f"This {impact} score shows solid performance."
        elif score >= 3.0:
            return f"This {impact} score suggests room for improvement."
        else:
            return f"This {impact} score indicates significant challenges."
    
    def _generate_conclusion(self, total_score: float, top_factors: List[Tuple[str, float]], 
                           components: Dict[str, float]) -> str:
        """Generate conclusion for the rationale."""
        if total_score >= 7.0:
            return "Overall, this venture shows strong potential and should be prioritized highly."
        elif total_score >= 5.0:
            return "Overall, this venture demonstrates good potential with some areas for optimization."
        elif total_score >= 3.0:
            return "Overall, this venture has moderate potential but requires careful consideration."
        else:
            return "Overall, this venture faces significant challenges and may need substantial improvements."


def create_explainability_module() -> ExplainabilityModule:
    """Factory function to create an ExplainabilityModule instance."""
    return ExplainabilityModule()
```