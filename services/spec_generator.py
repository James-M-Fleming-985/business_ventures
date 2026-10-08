"""
Spec Generator Service

Translates an exploitation recommendation (one sentence + metadata)
into a LAYER_REQUIREMENTS YAML spec that the AI Code Generator
Orchestrator can consume for its TDD cycle.

This is the missing bridge between:
  - ExploitationRecommendation (1-sentence business idea)
  - LAYER_REQUIREMENTS.yaml (structured spec with acceptance criteria)
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Complexity → number of acceptance criteria + scenarios
COMPLEXITY_AC_COUNTS = {
    'LOW': {'ac': 4, 'integration': 1, 'e2e': 1},
    'MEDIUM': {'ac': 7, 'integration': 2, 'e2e': 1},
    'HIGH': {'ac': 12, 'integration': 3, 'e2e': 2},
}


def generate_layer_spec_with_ai(
    requirement: str,
    complexity: str,
    build_id: int,
    anthropic_key: str,
    db_session=None,
    iteration_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Use AI to generate a structured LAYER_REQUIREMENTS dict from a
    one-line business requirement.

    If a db_session is provided, consults commercial intelligence to
    inject historical deployment performance context into the AI prompt
    (Track G — M3: YAML auto-generator consults commercial intelligence).

    If ``iteration_meta`` is provided (i.e. this is an iteration build),
    the BuildIntelligenceService evidence is rendered into the prompt so
    the AI derives the next iteration's requirements from real user
    behaviour on the live app rather than from the recommendation alone.

    Returns a dict that is a valid input for
    AICodeGeneratorOrchestrator.execute_full_cycle(requirements).
    """
    counts = COMPLEXITY_AC_COUNTS.get(complexity, COMPLEXITY_AC_COUNTS['MEDIUM'])

    # Build commercial intelligence context if available
    commercial_context = ""
    confidence_note = ""
    if db_session:
        try:
            from services.commercial_intelligence_service import (
                get_commercial_context_for_spec,
                get_configuration_confidence,
            )
            commercial_context = get_commercial_context_for_spec(db_session)
            confidence = get_configuration_confidence(
                db_session,
                tech_stack="fastapi",
                pricing_model="freemium",
            )
            confidence_note = (
                f"\nCONFIGURATION CONFIDENCE: {confidence['overall_confidence']}% — "
                f"{confidence['recommendation']}"
            )
        except Exception as exc:
            logger.warning("Could not load commercial intelligence for spec: %s", exc)

    # Iteration intelligence — only present for iteration builds.
    iteration_context = ""
    if iteration_meta:
        try:
            from services.build_intelligence_service import (
                format_intelligence_for_prompt,
            )
            iteration_context = format_intelligence_for_prompt(iteration_meta)
            if iteration_context:
                iteration_context = "\n" + iteration_context + "\n"
        except Exception as exc:
            logger.warning("Could not format iteration intelligence: %s", exc)

    prompt = f"""You are an expert software architect. Given a business requirement,
generate a structured YAML layer specification for automated code generation.

BUSINESS REQUIREMENT:
"{requirement}"

COMPLEXITY: {complexity}
{commercial_context}
{confidence_note}
{iteration_context}

IMPORTANT CONTEXT FOR REQUIREMENT PARSING:
- If the requirement contains labelled sections like PRODUCT VISION, KEY FEATURES,
  UI/UX STYLE, REQUIRED INTEGRATIONS, or TARGET USERS, use each section to generate
  targeted acceptance criteria, test scenarios, and implementation details.
- PRODUCT VISION should inform the feature_name and requirement_title.
- KEY FEATURES should map directly to specific acceptance criteria.
- UI/UX STYLE constraints should appear in acceptance criteria related to the interface.
- REQUIRED INTEGRATIONS should generate dedicated integration test scenarios.
- TARGET USERS should shape user-facing test scenarios and E2E workflows.

Generate a YAML document with EXACTLY this structure (output ONLY the YAML, no explanation):

layer_id: "LAYER-MVP-{build_id:04d}"
feature_name: "<short descriptive name>"
requirement_title: "<one-line summary>"

technical_constraints:
  language: "Python"
  framework: "FastAPI"
  output_file_type: ".py"

acceptance_criteria:
  # Generate EXACTLY {counts['ac']} acceptance criteria as a list of objects
  - criterion_id: "AC-001"
    criterion: "<specific, testable requirement>"
    description: "<detailed description>"
  # ... continue for all {counts['ac']} criteria

integration_test_scenarios:
  # Generate EXACTLY {counts['integration']} integration scenario(s)
  - scenario: "<scenario name>"
    description: "<what is being tested>"
    test_class: "TestIntegration<Name>"
    tests:
      - "test_<specific_test_name>"
      - "test_<another_test_name>"

e2e_test_scenarios:
  # Generate EXACTLY {counts['e2e']} E2E scenario(s)
  - scenario: "<scenario name>"
    description: "<what is being tested end to end>"
    test_class: "TestE2E<Name>"
    tests:
      - "test_<specific_test_name>"

IMPORTANT:
- Acceptance criteria must be SPECIFIC, TESTABLE, and IMPLEMENTABLE in Python
- Each criterion should map to a distinct piece of functionality
- Integration scenarios should test components working together
- E2E scenarios should test complete user workflows
- All test names must be valid Python identifiers
- Output ONLY the YAML document, nothing else
"""

    try:
        import anthropic
        from services.ai_provider import DEFAULT_ANTHROPIC_MODEL, response_text
        client = anthropic.Anthropic(api_key=anthropic_key)
        resp = client.messages.create(
            model=DEFAULT_ANTHROPIC_MODEL,
            max_tokens=4096,
            messages=[{'role': 'user', 'content': prompt}],
            timeout=120.0,
        )
        text = response_text(resp).strip()
        cost = (resp.usage.input_tokens * 0.003 + resp.usage.output_tokens * 0.015) / 1000

        # Strip markdown fences if present
        if text.startswith('```'):
            lines = text.split('\n')
            lines = [l for l in lines if not l.strip().startswith('```')]
            text = '\n'.join(lines)

        spec = yaml.safe_load(text)
        if not isinstance(spec, dict):
            raise ValueError("AI returned non-dict YAML")

        logger.info(f"Spec generated for build {build_id} (${cost:.4f})")
        return spec, cost

    except Exception as exc:
        logger.error(f"AI spec generation failed: {exc}")
        # Return a minimal fallback spec so the build can still attempt
        return _fallback_spec(requirement, build_id, counts), 0.0


def _fallback_spec(requirement: str, build_id: int, counts: Dict[str, int]) -> Dict[str, Any]:
    """Generate a minimal spec without AI when the API call fails."""
    words = requirement.split()
    name = ' '.join(words[:5]) if len(words) >= 5 else requirement

    ac = []
    for i in range(1, counts['ac'] + 1):
        ac.append({
            'criterion_id': f'AC-{i:03d}',
            'criterion': f'Implement requirement aspect {i} of: {requirement[:80]}',
            'description': f'Auto-generated criterion {i}',
        })

    return {
        'layer_id': f'LAYER-MVP-{build_id:04d}',
        'feature_name': name[:60],
        'requirement_title': requirement[:120],
        'technical_constraints': {
            'language': 'Python',
            'framework': 'FastAPI',
            'output_file_type': '.py',
        },
        'acceptance_criteria': ac,
        'integration_test_scenarios': [{
            'scenario': 'Component integration',
            'description': 'Verify components work together',
            'test_class': 'TestIntegration',
            'tests': ['test_components_integrate'],
        }],
        'e2e_test_scenarios': [{
            'scenario': 'End-to-end workflow',
            'description': 'Complete user flow',
            'test_class': 'TestE2E',
            'tests': ['test_full_workflow'],
        }],
    }
