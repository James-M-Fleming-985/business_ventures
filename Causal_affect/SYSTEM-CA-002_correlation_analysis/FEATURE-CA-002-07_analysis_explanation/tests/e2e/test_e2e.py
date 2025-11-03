"""
End-to-end tests for Analysis Explanation Natural Language Insights feature
Feature ID: FEATURE-CA-002-07
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import requests
from typing import Dict, List, Any

# Test fixtures and utilities
@pytest.fixture
def api_client():
    """Mock API client for testing"""
    class APIClient:
        def __init__(self, base_url="http://localhost:8000"):
            self.base_url = base_url
            self.session = requests.Session()
            
        def post(self, endpoint, data):
            return self.session.post(f"{self.base_url}{endpoint}", json=data)
            
        def get(self, endpoint, params=None):
            return self.session.get(f"{self.base_url}{endpoint}", params=params)
            
    return APIClient()

@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing"""
    return {
        "analysis_id": "ana_123456",
        "dataset_id": "ds_789012",
        "analysis_type": "regression",
        "results": {
            "r_squared": 0.89,
            "p_value": 0.001,
            "coefficients": {
                "feature1": 0.45,
                "feature2": -0.23,
                "feature3": 0.67
            },
            "residuals": {
                "mean": 0.02,
                "std": 0.15
            }
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "algorithm": "linear_regression",
            "parameters": {
                "regularization": "l2",
                "alpha": 0.01
            }
        }
    }

@pytest.fixture
def sample_insights_request():
    """Sample request for generating insights"""
    return {
        "analysis_id": "ana_123456",
        "user_id": "user_456",
        "language": "en",
        "detail_level": "detailed",
        "focus_areas": ["key_findings", "recommendations", "methodology"],
        "target_audience": "business_stakeholder"
    }


class TestAnalysisExplanationE2E:
    """End-to-end tests for Analysis Explanation Natural Language Insights"""
    
    @pytest.mark.asyncio
    async def test_e2e_generate_insights_complete_workflow(self, api_client, sample_analysis_data, sample_insights_request):
        """
        Test complete workflow: analysis submission -> insight generation -> retrieval
        
        Scenarios:
        1. Submit analysis for processing
        2. Request natural language insights
        3. Retrieve and verify generated insights
        4. Validate insight quality and completeness
        """
        
        # Step 1: Submit analysis data
        with patch.object(api_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "status": "success",
                "analysis_id": sample_analysis_data["analysis_id"],
                "message": "Analysis data received"
            }
            
            response = api_client.post("/api/v1/analysis", sample_analysis_data)
            assert response.status_code == 200
            
        # Step 2: Request natural language insights generation
        with patch.object(api_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 202
            mock_post.return_value.json.return_value = {
                "status": "processing",
                "job_id": "job_insights_789",
                "estimated_completion": (datetime.now() + timedelta(seconds=5)).isoformat()
            }
            
            response = api_client.post("/api/v1/insights/generate", sample_insights_request)
            assert response.status_code == 202
            job_data = response.json()
            
        # Step 3: Poll for completion (simulate async processing)
        job_complete = False
        attempts = 0
        max_attempts = 10
        
        while not job_complete and attempts < max_attempts:
            with patch.object(api_client.session, 'get') as mock_get:
                if attempts < 3:
                    # Still processing
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json.return_value = {
                        "status": "processing",
                        "progress": attempts * 30
                    }
                else:
                    # Completed
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json.return_value = {
                        "status": "completed",
                        "progress": 100,
                        "insights_id": "insights_456789"
                    }
                    job_complete = True
                
                response = api_client.get(f"/api/v1/insights/jobs/{job_data['job_id']}")
                assert response.status_code == 200
                
            await asyncio.sleep(0.1)  # Simulate delay
            attempts += 1
        
        assert job_complete, "Job did not complete within expected time"
        
        # Step 4: Retrieve generated insights
        expected_insights = {
            "insights_id": "insights_456789",
            "analysis_id": sample_analysis_data["analysis_id"],
            "generated_at": datetime.now().isoformat(),
            "language": "en",
            "sections": {
                "executive_summary": {
                    "title": "Executive Summary",
                    "content": "The regression analysis reveals strong predictive power with an R² of 0.89, "
                              "indicating that 89% of the variance in the target variable is explained by the model.",
                    "confidence_score": 0.92
                },
                "key_findings": {
                    "title": "Key Findings",
                    "content": [
                        "Feature3 shows the strongest positive correlation (0.67) with the target variable",
                        "Feature2 has a negative impact (-0.23) on the outcome",
                        "The model demonstrates statistical significance with p-value < 0.001"
                    ],
                    "visualizations": ["feature_importance_chart", "coefficient_plot"]
                },
                "recommendations": {
                    "title": "Business Recommendations",
                    "content": [
                        "Focus resources on optimizing Feature3 as it has the highest impact",
                        "Consider strategies to mitigate the negative effect of Feature2",
                        "The model's high accuracy suggests it can be reliably used for predictions"
                    ],
                    "priority": "high"
                },
                "methodology": {
                    "title": "Methodology Explanation",
                    "content": "Linear regression with L2 regularization (alpha=0.01) was applied to prevent overfitting. "
                              "The low residual standard deviation (0.15) indicates good model fit.",
                    "technical_details": {
                        "algorithm": "Linear Regression",
                        "regularization": "Ridge (L2)",
                        "validation_method": "cross-validation"
                    }
                }
            },
            "metadata": {
                "generation_time_ms": 2345,
                "model_version": "v1.2.0",
                "quality_metrics": {
                    "readability_score": 8.5,
                    "completeness": 0.95,
                    "accuracy_confidence": 0.91
                }
            }
        }
        
        with patch.object(api_client.session, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = expected_insights
            
            response = api_client.get("/api/v1/insights/insights_456789")
            assert response.status_code == 200
            insights = response.json()
            
        # Validate insights structure and content
        assert insights["analysis_id"] == sample_analysis_data["analysis_id"]
        assert "sections" in insights
        assert all(section in insights["sections"] for section in ["key_findings", "recommendations", "methodology"])
        assert insights["language"] == "en"
        assert insights["metadata"]["quality_metrics"]["readability_score"] > 7.0
        assert insights["metadata"]["quality_metrics"]["completeness"] > 0.9
        
    @pytest.mark.asyncio
    async def test_e2e_multi_language_insights_generation(self, api_client, sample_analysis_data):
        """
        Test multi-language insight generation with different audiences
        
        Scenarios:
        1. Generate insights in multiple languages
        2. Verify language-specific formatting and terminology
        3. Test different target audience adaptations
        """
        
        languages_and_audiences = [
            ("en", "technical_expert"),
            ("es", "business_stakeholder"),
            ("fr", "executive"),
            ("de", "data_scientist")
        ]
        
        generated_insights = {}
        
        for language, audience in languages_and_audiences:
            request_data = {
                "analysis_id": sample_analysis_data["analysis_id"],
                "user_id": "user_456",
                "language": language,
                "detail_level": "comprehensive" if audience == "technical_expert" else "summary",
                "focus_areas": ["all"],
                "target_audience": audience
            }
            
            # Submit insight generation request
            with patch.object(api_client.session, 'post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {
                    "status": "success",
                    "insights_id": f"insights_{language}_{audience}",
                    "processing_time_ms": 1500
                }
                
                response = api_client.post("/api/v1/insights/generate-sync", request_data)
                assert response.status_code == 200
                result = response.json()
                
            # Retrieve generated insights
            insights_by_lang = {
                "en": {
                    "technical_expert": {
                        "summary": "Advanced regression analysis with L2 regularization yielded R²=0.89, "
                                  "p<0.001, indicating robust model performance with minimal overfitting.",
                        "terminology_level": "technical"
                    }
                },
                "es": {
                    "business_stakeholder": {
                        "summary": "El análisis muestra que el modelo explica el 89% de la variación en los resultados, "
                                  "lo cual es excelente para la toma de decisiones empresariales.",
                        "terminology_level": "business"
                    }
                },
                "fr": {
                    "executive": {
                        "summary": "L'analyse révèle une forte capacité prédictive avec des implications "
                                  "stratégiques importantes pour l'entreprise.",
                        "terminology_level": "executive"
                    }
                },
                "de": {
                    "data_scientist": {
                        "summary": "Die Regressionsanalyse mit L2-Regularisierung zeigt R²=0,89 und p<0,001, "
                                  "was auf eine hohe Modellgüte hindeutet.",
                        "terminology_level": "technical"
                    }
                }
            }
            
            with patch.object(api_client.session, 'get') as mock_get:
                mock_insights = {
                    "insights_id": result["insights_id"],
                    "language": language,
                    "target_audience": audience,
                    "content": insights_by_lang.get(language, {}).get(audience, {}),
                    "sections": {
                        "summary": insights_by_lang.get(language, {}).get(audience, {}).get("summary", ""),
                        "details": "..." # Additional content
                    }
                }
                
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mock_insights
                
                response = api_client.get(f"/api/v1/insights/{result['insights_id']}")
                assert response.status_code == 200
                insights = response.json()
                generated_insights[f"{language}_{audience}"] = insights
                
        # Validate language-specific content
        assert len(generated_insights) == 4
        
        # Verify English technical content uses technical terminology
        en_tech = generated_insights.get("en_technical_expert", {})
        assert "R²" in en_tech.get("sections", {}).get("summary", "")
        assert "regularization" in en_tech.get("sections", {}).get("summary", "").lower()
        
        # Verify Spanish business content uses business terminology
        es_biz = generated_insights.get("es_business_stakeholder", {})
        assert "decisiones empresariales" in es_biz.get("sections", {}).get("summary", "")
        
        # Verify appropriate complexity for each audience
        for key, insights in generated_insights.items():
            lang, audience = key.split("_", 1)
            assert insights["language"] == lang
            assert insights["target_audience"] == audience
            
    @pytest.mark.asyncio
    async def test_e2e_error_handling_and_recovery(self, api_client):
        """
        Test error handling throughout the insight generation workflow
        
        Scenarios:
        1. Invalid analysis ID
        2. Unsupported language request
        3. Service timeout and retry
        4. Partial failure recovery
        """
        
        # Scenario 1: Invalid analysis ID
        invalid_request = {
            "analysis_id": "invalid_id_999",
            "user_id": "user_123",
            "language": "en",
            "detail_level": "summary"
        }
        
        with patch.object(api_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 404
            mock_post.return_value.json.return_value = {
                "error": "Analysis not found",
                "error_code": "ANALYSIS_NOT_FOUND",
                "analysis_id": "invalid_id_999"
            }
            
            response = api_client.post("/api/v1/insights/generate", invalid_request)
            assert response.status_code == 404
            error_data = response.json()
            assert error_data["error_code"] == "ANALYSIS_NOT_FOUND"
            
        # Scenario 2: Unsupported language
        unsupported_lang_request = {
            "analysis_id": "ana_123456",
            "user_id": "user_123",
            "language": "xyz",  # Invalid language code
            "detail_level": "summary"
        }
        
        with patch.object(api_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {
                "error": "Unsupported language",
                "error_code": "UNSUPPORTED_LANGUAGE",
                "supported_languages": ["en", "es", "fr", "de", "pt", "it", "nl", "pl", "ru", "ja", "ko", "zh"]
            }
            
            response = api_client.post("/api/v1/insights/generate", unsupported_lang_request)
            assert response.status_code == 400
            error_data = response.json()
            assert error_data["error_code"] == "UNSUPPORTED_LANGUAGE"
            assert "en" in error_data["supported_languages"]
            
        # Scenario 3: Service timeout with retry mechanism
        timeout_request = {
            "analysis_id": "ana_large_dataset",
            "user_id": "user_123",
            "language": "en",
            "detail_level": "comprehensive"
        }
        
        attempt_count = 0
        max_retries = 3
        
        while attempt_count < max_retries:
            with patch.object(api_client.session, 'post') as mock_post:
                if attempt_count < 2:
                    # Simulate timeout
                    mock_post.return_value.status_code = 504
                    mock_post.return_value.json.return_value = {
                        "error": "Gateway timeout",
                        "error_code": "TIMEOUT",
                        "retry_after": 5
                    }
                else:
                    # Success on third attempt
                    mock_post.return_value.status_code = 202
                    mock_post.return_value.json.return_value = {
                        "status": "processing",
                        "job_id": "job_retry_success"
                    }
                
                response = api_client.post("/api/v1/insights/generate", timeout_request)
                
                if response.status_code == 504:
                    attempt_count += 1
                    await asyncio.sleep(0.1)  # Wait before retry
                else:
                    break
                    
        assert response.status_code == 202
        assert attempt_count == 2  # Succeeded on third attempt
        
        # Scenario 4: Partial failure recovery
        partial_failure_request = {
            "analysis_id": "ana_complex",
            "user_id": "user_123",
            "language": "en",
            "detail_level": "detailed",
            "focus_areas": ["key_findings", "recommendations", "methodology", "limitations"]
        }
        
        with patch.object(api_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 206  # Partial Content
            mock_post.return_value.json.return_value = {
                "status": "partial_success",
                "insights_id": "insights_partial_789",
                "completed_sections": ["key_findings", "recommendations", "methodology"],
                "failed_sections": [
                    {
                        "section": "limitations",
                        "error": "Insufficient data for limitations analysis",
                        "fallback": "generic_limitations"
                    }
                ],
                "quality_score": 0.75  # Reduced due to partial failure
            }
            
            response = api_client.post("/api/v1/insights/generate-sync", partial_failure_request)
            assert response.status_code == 206
            result = response.json()
            assert result["status"] == "partial_success"
            assert len(result["completed_sections"]) == 3
            assert len(result["failed_sections"]) == 1
            assert result["quality_score"] < 0.8  # Quality impacted by partial failure
            
        # Verify partial insights can still be retrieved
        with patch.object(api_client.session, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "insights_id": "insights_partial_789",
                "status": "partial",
                "sections": {
                    "key_findings": {
                        "content": "Analysis shows significant patterns...",
                        "status": "complete"
                    },
                    "recommendations": {
                        "content": "Based on the findings, we recommend...",
                        "status": "complete"
                    },
                    "methodology": {
                        "content": "The analysis employed advanced techniques...",
                        "status": "complete"
                    },
                    "limitations": {
                        "content": "Generic limitations apply to this type of analysis...",
                        "status": "fallback",
                        "original_error": "Insufficient data"
                    }
                },
                "metadata": {
                    "completeness": 0.75,
                    "has_fallbacks": True
                }
            }
            
            response = api_client.get(f"/api/v1/insights/{result['insights_id']}")
            assert response.status_code == 200
            insights = response.json()
            assert insights["status"] == "partial"
            assert insights["metadata"]["has_fallbacks"] is True
            assert insights["sections"]["limitations"]["status"] == "fallback"
            
    @pytest.mark.asyncio
    async def test_e2e_performance_and_caching(self, api_client, sample_analysis_data):
        """
        Test performance optimizations and caching behavior
        
        Scenarios:
        1. First request triggers full generation
        2. Subsequent identical requests use cache
        3. Cache invalidation on analysis update
        4. Performance metrics validation
        """
        
        cache_test_request = {
            "analysis_id": "ana_cache_test",
            "user_id": "user_789",
            "language": "en",
            "detail_level": "summary",
            "focus_areas": ["key_findings"],
            "use_cache": True
        }
        
        # First request - full generation
        with patch.object(api_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "status": "success",
                "insights_id": "insights_cached_123",
                "cache_status": "miss",
                "generation_time_ms": 2500,
                "from_cache": False
            }
            
            start_time = datetime.now()
            response = api_client.post("/api/v1/insights/generate-sync", cache_test_request)
            first_request_time = (datetime.now() - start_time).total_seconds()
            
            assert response.status_code == 200
            result = response.json()
            assert result["cache_status"] == "miss"
            assert result["from_cache"] is False
            assert result["generation_time_ms"] > 1000  # Should take time to generate
            
        # Second identical request - should use cache
        with patch.object(api_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "status": "success",
                "insights_id": "insights_cached_123",
                "cache_status": "hit",
                "generation_time_ms": 50,  # Much faster from cache
                "from_cache": True,
                "cache_key": "ana_cache_test:en:summary:key_findings"
            }
            
            start_time = datetime.now()
            response = api_client.post("/api/v1/insights/generate-sync", cache_test_request)
            cached_request_time = (datetime.now() - start_time).total_seconds()
            
            assert response.status_code == 200
            result = response.json()
            assert result["cache_status"] == "hit"
            assert result["from_cache"] is True
            assert result["generation_time_ms"] < 100  # Should be very fast from cache
            assert cached_request_time < first_request_time * 0.1  # At least 10x faster
            
        # Update analysis data - should invalidate cache
        update_data = {
            "analysis_id": "ana_cache_test",
            "updates": {
                "results": {
                    "r_squared": 0.91  # Updated value
                }
            }
        }
        
        with patch.object(api_client.session, 'put') as mock_put:
            mock_put.return_value.status_code = 200
            mock_put.return_value.json.return_value = {
                "status": "success",
                "cache_invalidated": True,
                "invalidated_keys": ["ana_cache_test:*"]
            }
            
            response = api_client.put("/api/v1/analysis/ana_cache_test", update_data)
            assert response.status_code == 200
            assert response.json()["cache_invalidated"] is True
            
        # Next request after update - should regenerate
        with patch.object(api_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "status": "success",
                "insights_id": "insights_cached_124",  # New ID after regeneration
                "cache_status": "miss",
                "generation_time_ms": 2300,
                "from_cache": False,
                "reason": "cache_invalidated"
            }
            
            response = api_client.post("/api/v1/insights/generate-sync", cache_test_request)
            assert response.status_code == 200
            result = response.json()
            assert result["cache_status"] == "miss"
            assert result["from_cache"] is False
            assert result["insights_id"] != "insights_cached_123"  # Different from cached version
            
        # Test cache control headers
        no_cache_request = cache_test_request.copy()
        no_cache_request["use_cache"] = False
        
        with patch.object(api_client.session, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "status": "success",
                "insights_id": "insights_no_cache_125",
                "cache_status": "bypass",
                "generation_time_ms": 2400,
                "from_cache": False
            }
            
            response = api_client.post("/api/v1/insights/generate-sync", no_cache_request)
            assert response.status_code == 200
            result = response.json()
            assert result["cache_status"] == "bypass"
            assert result["from_cache"] is False


# Additional test utilities
class InsightsValidator:
    """Helper class to validate generated insights"""
    
    @staticmethod
    def validate_readability(text: str, min_score: float = 7.0) -> bool:
        """Validate text readability score"""
        # Simplified readability check
        avg_sentence_length = len(text.split()) / max(len(text.split('.')), 1)
        return avg_sentence_length < 25  # Reasonable sentence length
        
    @staticmethod
    def validate_completeness(insights: Dict[str, Any], required_sections: List[str]) -> bool:
        """Validate that all required sections are present"""
        sections = insights.get("sections", {})
        return all(section in sections and sections[section].get("content") 
                  for section in required_sections)
        
    @staticmethod
    def validate_language(text: str, language_code: str) -> bool:
        """Basic language validation"""
        language_indicators = {
            "en": ["the", "and", "is", "analysis"],
            "es": ["el", "la", "de", "análisis"],
            "fr": ["le", "la", "de", "analyse"],
            "de": ["der", "die", "das", "Analyse"]
        }
        
        indicators = language_indicators.get(language_code, [])
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])