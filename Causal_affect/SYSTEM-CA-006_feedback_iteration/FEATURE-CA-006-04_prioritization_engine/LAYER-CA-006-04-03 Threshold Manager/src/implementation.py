```python
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ThresholdOperator(Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="


@dataclass
class ThresholdRule:
    """Represents a single threshold rule."""
    metric: str
    operator: str
    value: float
    weight: float = 1.0

    def evaluate(self, metric_value: float) -> bool:
        """Evaluate the rule against a metric value."""
        if self.operator == ">":
            return metric_value > self.value
        elif self.operator == "<":
            return metric_value < self.value
        elif self.operator == ">=":
            return metric_value >= self.value
        elif self.operator == "<=":
            return metric_value <= self.value
        elif self.operator == "==":
            return metric_value == self.value
        elif self.operator == "!=":
            return metric_value != self.value
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


@dataclass
class ThresholdConfiguration:
    """Represents a threshold configuration."""
    name: str
    rules: List[ThresholdRule] = field(default_factory=list)
    require_all: bool = True
    min_score: float = 0.0


class ThresholdManager:
    """Manages threshold configurations and evaluates MVPs against them."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ThresholdManager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.configurations: Dict[str, ThresholdConfiguration] = {}
        self.ab_tests: Dict[str, List[str]] = {}
        self.active_config: Optional[str] = None
        
        if config_path and os.path.exists(config_path):
            self.load_configuration(config_path)

    def load_configuration(self, config_path: str) -> None:
        """
        Load threshold configurations from a file.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Load configurations
        if 'configurations' in config_data:
            for config_name, config_dict in config_data['configurations'].items():
                rules = []
                for rule_dict in config_dict.get('rules', []):
                    rules.append(ThresholdRule(
                        metric=rule_dict['metric'],
                        operator=rule_dict['operator'],
                        value=rule_dict['value'],
                        weight=rule_dict.get('weight', 1.0)
                    ))
                
                self.configurations[config_name] = ThresholdConfiguration(
                    name=config_name,
                    rules=rules,
                    require_all=config_dict.get('require_all', True),
                    min_score=config_dict.get('min_score', 0.0)
                )
        
        # Load A/B tests
        if 'ab_tests' in config_data:
            self.ab_tests = config_data['ab_tests']
        
        # Set active configuration
        if 'active_config' in config_data:
            self.active_config = config_data['active_config']
        elif self.configurations:
            self.active_config = list(self.configurations.keys())[0]

    def add_configuration(self, configuration: ThresholdConfiguration) -> None:
        """
        Add a threshold configuration.
        
        Args:
            configuration: ThresholdConfiguration object to add
        """
        self.configurations[configuration.name] = configuration
        
        if self.active_config is None:
            self.active_config = configuration.name

    def set_active_configuration(self, config_name: str) -> None:
        """
        Set the active configuration.
        
        Args:
            config_name: Name of the configuration to activate
        """
        if config_name not in self.configurations:
            raise ValueError(f"Configuration '{config_name}' not found")
        self.active_config = config_name

    def get_configuration(self, config_name: Optional[str] = None) -> ThresholdConfiguration:
        """
        Get a threshold configuration.
        
        Args:
            config_name: Name of the configuration. If None, returns active configuration.
            
        Returns:
            ThresholdConfiguration object
        """
        if config_name is None:
            config_name = self.active_config
        
        if config_name is None:
            raise ValueError("No active configuration set")
        
        if config_name not in self.configurations:
            raise ValueError(f"Configuration '{config_name}' not found")
        
        return self.configurations[config_name]

    def evaluate_mvp(self, mvp_metrics: Dict[str, float], 
                     config_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate an MVP against threshold rules.
        
        Args:
            mvp_metrics: Dictionary of metric names to values
            config_name: Name of configuration to use. If None, uses active configuration.
            
        Returns:
            Dictionary containing evaluation results
        """
        config = self.get_configuration(config_name)
        
        results = {
            'passed': False,
            'score': 0.0,
            'rule_results': [],
            'config_name': config.name
        }
        
        total_weight = 0.0
        weighted_score = 0.0
        rules_passed = 0
        
        for rule in config.rules:
            if rule.metric not in mvp_metrics:
                rule_result = {
                    'metric': rule.metric,
                    'passed': False,
                    'error': f"Metric '{rule.metric}' not found in MVP metrics"
                }
                results['rule_results'].append(rule_result)
                continue
            
            metric_value = mvp_metrics[rule.metric]
            passed = rule.evaluate(metric_value)
            
            rule_result = {
                'metric': rule.metric,
                'operator': rule.operator,
                'threshold': rule.value,
                'actual': metric_value,
                'passed': passed,
                'weight': rule.weight
            }
            results['rule_results'].append(rule_result)
            
            total_weight += rule.weight
            if passed:
                weighted_score += rule.weight
                rules_passed += 1
        
        # Calculate score
        if total_weight > 0:
            results['score'] = weighted_score / total_weight
        
        # Determine if passed
        if config.require_all:
            results['passed'] = rules_passed == len(config.rules) and results['score'] >= config.min_score
        else:
            results['passed'] = rules_passed > 0 and results['score'] >= config.min_score
        
        return results

    def setup_ab_test(self, test_name: str, config_names: List[str]) -> None:
        """
        Setup an A/B test with multiple configurations.
        
        Args:
            test_name: Name of the A/B test
            config_names: List of configuration names to include in the test
        """
        for config_name in config_names:
            if config_name not in self.configurations:
                raise ValueError(f"Configuration '{config_name}' not found")
        
        self.ab_tests[test_name] = config_names

    def get_ab_test_configs(self, test_name: str) -> List[str]:
        """
        Get configurations for an A/B test.
        
        Args:
            test_name: Name of the A/B test
            
        Returns:
            List of configuration names
        """
        if test_name not in self.ab_tests:
            raise ValueError(f"A/B test '{test_name}' not found")
        
        return self.ab_tests[test_name]

    def evaluate_ab_test(self, test_name: str, 
                        mvp_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluate an MVP against all configurations in an A/B test.
        
        Args:
            test_name: Name of the A/B test
            mvp_metrics: Dictionary of metric names to values
            
        Returns:
            Dictionary containing results for each configuration
        """
        config_names = self.get_ab_test_configs(test_name)
        
        results = {
            'test_name': test_name,
            'configurations': {}
        }
        
        for config_name in config_names:
            results['configurations'][config_name] = self.evaluate_mvp(
                mvp_metrics, config_name
            )
        
        return results

    def save_configuration(self, output_path: Optional[str] = None) -> None:
        """
        Save current configurations to a file.
        
        Args:
            output_path: Path to save the configuration. If None, uses config_path.
        """
        if output_path is None:
            output_path = self.config_path
        
        if output_path is None:
            raise ValueError("No output path specified")
        
        config_data = {
            'active_config': self.active_config,
            'configurations': {},
            'ab_tests': self.ab_tests
        }
        
        for config_name, config in self.configurations.items():
            config_data['configurations'][config_name] = {
                'require_all': config.require_all,
                'min_score': config.min_score,
                'rules': [
                    {
                        'metric': rule.metric,
                        'operator': rule.operator,
                        'value': rule.value,
                        'weight': rule.weight
                    }
                    for rule in config.rules
                ]
            }
        
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2)
```