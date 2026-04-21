"""
MVP Builder Service for Causal Affect Platform

YAML-driven build engine that generates MVP code from exploitation
recommendations using an AI TDD cycle (RED → GREEN → REFACTOR).

Pipeline:
  1. AI generates a LAYER_REQUIREMENTS YAML spec from the requirement
  2. Orchestrator runs RED phase  (generate failing tests)
  3. Orchestrator runs GREEN phase (generate implementation to pass tests)
  4. Orchestrator runs REFACTOR phase (improve quality)
  5. Validate generated code (ast.parse)
  6. Persist files to DB
"""

import ast
import json
import logging
import os
import py_compile
import re
import subprocess
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template metadata structures (migrated from mvp_semantic_mapper.py)
# ---------------------------------------------------------------------------

@dataclass
class TemplateMetadata:
    id: str
    name: str
    path: str
    layer_type: str  # api, ui, infra, composite, analytics
    frameworks: List[str]
    tags: List[str]
    version: str
    status: str
    description: str
    cost_estimate_tokens: int
    outputs: Optional[List[Dict[str, str]]] = None


@dataclass
class TemplateMatch:
    template: TemplateMetadata
    confidence: float
    matched_keywords: List[str]
    reasons: List[str]


# ---------------------------------------------------------------------------
# Keyword-based requirement analysis
# ---------------------------------------------------------------------------

KEYWORD_MAPPINGS = {
    'frontend': ['landing', 'page', 'ui', 'website', 'react', 'interface', 'form', 'dashboard'],
    'backend': ['api', 'server', 'endpoint', 'service', 'backend', 'fastapi'],
    'database': ['store', 'save', 'persist', 'database', 'data', 'record', 'user'],
    'auth': ['login', 'signup', 'register', 'authenticate', 'auth', 'user', 'password'],
    'deployment': ['deploy', 'host', 'railway', 'production', 'serve'],
    'payments': ['payment', 'stripe', 'checkout', 'subscription', 'billing', 'saas'],
    'analytics': ['analytics', 'tracking', 'ga4', 'mixpanel', 'amplitude', 'metrics', 'events'],
    'crud': ['create', 'read', 'update', 'delete', 'crud', 'manage', 'list'],
}

COMPLEXITY_LIMITS = {
    'LOW': 2,
    'MEDIUM': 5,
    'HIGH': 12,
}

ERROR_CATEGORIES = ['syntax', 'test', 'frontend', 'import', 'wiring', 'config', 'runtime']

# Known-good import → package mapping for automated import resolution
IMPORT_PACKAGE_MAP = {
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'sqlalchemy': 'sqlalchemy',
    'pydantic': 'pydantic',
    'requests': 'requests',
    'httpx': 'httpx',
    'jinja2': 'Jinja2',
    'pytest': 'pytest',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'stripe': 'stripe',
    'boto3': 'boto3',
    'anthropic': 'anthropic',
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'alembic': 'alembic',
    'celery': 'celery',
    'redis': 'redis',
    'jwt': 'PyJWT',
    'passlib': 'passlib',
    'cors': 'fastapi',
}


def _analyse_requirement(text: str) -> Dict[str, bool]:
    """Return which capability categories a requirement needs."""
    lower = text.lower()
    return {cat: any(kw in lower for kw in kws) for cat, kws in KEYWORD_MAPPINGS.items()}


def _score_template(template: TemplateMetadata, requirement: str, needs: Dict[str, bool]) -> Tuple[float, List[str]]:
    """Score how well *template* matches *requirement*. Returns (score, reasons)."""
    score = 0.0
    reasons: List[str] = []
    req_lower = requirement.lower()

    # Layer alignment
    layer_map = {'ui': 'frontend', 'api': 'backend', 'infra': 'deployment'}
    cat = layer_map.get(template.layer_type)
    if cat and needs.get(cat):
        score += 30
        reasons.append(f"{template.layer_type} layer matches")

    # Tag match
    for tag in template.tags:
        if tag.lower() in req_lower:
            score += 15
            reasons.append(f"tag '{tag}'")

    # Framework match
    for fw in template.frameworks:
        if fw.lower() in req_lower:
            score += 10
            reasons.append(f"framework '{fw}'")

    # Description word overlap
    stop = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with'}
    desc_words = set(re.findall(r'\b\w+\b', template.description.lower())) - stop
    req_words = set(re.findall(r'\b\w+\b', req_lower)) - stop
    overlap = desc_words & req_words
    if overlap:
        score += min(len(overlap) * 5, 20)
        reasons.append(f"{len(overlap)} keyword overlaps")

    # Specific boosts
    if template.id == 'tpl-backend-fastapi-crud' and any(w in req_lower for w in ['crud', 'api', 'store', 'manage']):
        score += 20
    if template.id == 'tpl-backend-fastapi-auth' and needs.get('auth'):
        score += 25
    if template.id == 'tpl-infra-railway-service' and needs.get('deployment'):
        score += 20
    if 'analytics' in template.id and needs.get('analytics'):
        score += 50

    return min(score, 100.0), reasons


class MVPBuilderService:
    """Orchestrates MVP code generation via YAML-driven TDD pipeline."""

    def __init__(self, s3_service=None):
        self.s3 = s3_service
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.templates_dir = Path(__file__).resolve().parent.parent / 'templates' / 'mvp'
        self.templates: List[TemplateMetadata] = []
        self._load_templates()

        if self.anthropic_key:
            logger.info("✅ MVPBuilderService initialised with AI key")
        else:
            logger.warning("⚠️  ANTHROPIC_API_KEY not set – AI generation disabled")

    # ------------------------------------------------------------------
    # Template loading
    # ------------------------------------------------------------------

    def _load_templates(self):
        index_file = self.templates_dir / 'index.yaml'
        if not index_file.exists():
            logger.warning(f"Template index not found: {index_file}")
            return
        with open(index_file, 'r') as f:
            data = yaml.safe_load(f)
        for t in data.get('templates', []):
            self.templates.append(TemplateMetadata(
                id=t['id'], name=t['name'], path=t['path'],
                layer_type=t['layer_type'], frameworks=t.get('frameworks', []),
                tags=t.get('tags', []), version=t['version'], status=t['status'],
                description=t.get('description', ''),
                cost_estimate_tokens=t.get('cost_estimate_tokens', 0),
            ))
        logger.info(f"Loaded {len(self.templates)} MVP templates")

    # ------------------------------------------------------------------
    # Template matching
    # ------------------------------------------------------------------

    def match_templates(self, requirement: str, complexity: str) -> List[TemplateMatch]:
        """Select templates that match *requirement*, capped by *complexity*."""
        needs = _analyse_requirement(requirement)
        scored = []
        for tpl in self.templates:
            if tpl.status != 'approved':
                continue
            score, reasons = _score_template(tpl, requirement, needs)
            if score >= 15:
                scored.append(TemplateMatch(template=tpl, confidence=score,
                                            matched_keywords=[], reasons=reasons))
        scored.sort(key=lambda m: m.confidence, reverse=True)
        limit = COMPLEXITY_LIMITS.get(complexity, 5)
        return scored[:limit]

    # ------------------------------------------------------------------
    # Jinja2 rendering
    # ------------------------------------------------------------------

    def _render_template_dir(self, template: TemplateMetadata, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Render all .jinja files inside a template directory. Returns list of {path, content, size}."""
        tpl_path = self.templates_dir / template.path
        if not tpl_path.is_dir():
            logger.warning(f"Template path missing: {tpl_path}")
            return []

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(tpl_path)),
            undefined=jinja2.Undefined,
            keep_trailing_newline=True,
        )

        files: List[Dict[str, Any]] = []
        for jinja_file in sorted(tpl_path.rglob('*.jinja')):
            rel = jinja_file.relative_to(tpl_path)
            out_name = str(rel).replace('.jinja', '')
            try:
                tmpl = env.get_template(str(rel))
                content = tmpl.render(**params)
                files.append({'path': out_name, 'content': content, 'size': len(content.encode()),
                              'template_id': template.id})
            except Exception as exc:
                logger.error(f"Render error {rel}: {exc}")
                files.append({'path': out_name, 'content': f'# RENDER ERROR: {exc}', 'size': 0,
                              'template_id': template.id, 'error': str(exc)})
        return files

    # ------------------------------------------------------------------
    # AI code generation
    # ------------------------------------------------------------------

    def _ai_generate(self, requirement: str, matched_templates: List[TemplateMatch],
                     rendered_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use Claude to fill gaps — returns additional generated files."""
        if not self.anthropic_key:
            return []

        try:
            import anthropic
        except ImportError:
            logger.warning("anthropic package not installed")
            return []

        file_summary = '\n'.join(f"- {f['path']}" for f in rendered_files)
        template_summary = ', '.join(m.template.name for m in matched_templates)

        prompt = (
            f"You are an expert software engineer. An MVP is being generated for the "
            f"following requirement:\n\n\"{requirement}\"\n\n"
            f"Templates already used: {template_summary}\n"
            f"Files already generated:\n{file_summary}\n\n"
            f"Generate any MISSING files needed to make this MVP functional. "
            f"For each file, respond with a JSON array of objects with keys "
            f"\"path\" (relative file path) and \"content\" (full file content). "
            f"Only output the JSON array, no other text."
        )

        try:
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            resp = client.messages.create(
                model='claude-sonnet-4-20250514',
                max_tokens=4096,
                messages=[{'role': 'user', 'content': prompt}],
            )
            text = resp.content[0].text.strip()
            # Extract JSON array from response
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                ai_files = json.loads(match.group())
                result = []
                for f in ai_files:
                    content = f.get('content', '')
                    result.append({
                        'path': f['path'],
                        'content': content,
                        'size': len(content.encode()),
                        'template_id': 'ai-generated',
                    })
                cost = (resp.usage.input_tokens * 0.003 + resp.usage.output_tokens * 0.015) / 1000
                logger.info(f"AI generated {len(result)} files (${cost:.4f})")
                return result, cost
        except Exception as exc:
            logger.error(f"AI generation failed: {exc}")

        return [], 0.0

    # ------------------------------------------------------------------
    # S3 upload
    # ------------------------------------------------------------------

    def _upload_files(self, files: List[Dict[str, Any]], s3_prefix: str) -> List[Dict[str, Any]]:
        """Upload generated files to S3. Returns enriched file dicts with s3_key."""
        if not self.s3 or not self.s3.enabled:
            logger.warning("S3 not available – skipping upload")
            for f in files:
                f['s3_key'] = f"{s3_prefix}{f['path']}"
            return files

        for f in files:
            key = f"{s3_prefix}{f['path']}"
            buf = io.BytesIO(f['content'].encode('utf-8'))
            self.s3.upload_file(buf, key, content_type='text/plain')
            f['s3_key'] = key
        return files

    # ------------------------------------------------------------------
    # Pre-build validation (Phase 2.1)
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_template_file(file_path: str, content: str) -> List[Dict[str, Any]]:
        """Validate a single Python file with AST parse + py_compile + syntax checks.

        Returns list of structured error dicts (empty = file is clean).
        Each error dict is ML-consumable: {type, message, file, line, category, traceback_snippet}.
        """
        errors: List[Dict[str, Any]] = []
        if not file_path.endswith('.py'):
            return errors

        # 1. AST parse — catches syntax errors
        try:
            ast.parse(content, filename=file_path)
        except SyntaxError as e:
            errors.append({
                'type': 'SyntaxError',
                'message': str(e.msg) if e.msg else str(e),
                'file': file_path,
                'line': e.lineno or 0,
                'category': 'syntax',
                'traceback_snippet': f"line {e.lineno}: {e.text.strip() if e.text else ''}",
            })

        # 2. py_compile — catches encoding issues and edge syntax ast misses
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            py_compile.compile(tmp_path, doraise=True)
        except py_compile.PyCompileError as e:
            # Only add if not a duplicate of the AST error
            if not any(err['type'] == 'SyntaxError' and err['file'] == file_path for err in errors):
                errors.append({
                    'type': 'PyCompileError',
                    'message': str(e),
                    'file': file_path,
                    'line': getattr(e, 'lineno', 0) or 0,
                    'category': 'syntax',
                    'traceback_snippet': str(e)[:200],
                })
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        # 3. Basic lint checks — common Python mistakes
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.rstrip()
            # Mixed tabs and spaces
            if '\t' in line and '    ' in line:
                errors.append({
                    'type': 'IndentationWarning',
                    'message': 'Mixed tabs and spaces',
                    'file': file_path,
                    'line': i,
                    'category': 'syntax',
                    'traceback_snippet': stripped[:120],
                })
            # Bare except (bad practice that hides bugs)
            if re.match(r'^\s*except\s*:\s*$', stripped):
                errors.append({
                    'type': 'LintWarning',
                    'message': 'Bare except clause — should specify exception type',
                    'file': file_path,
                    'line': i,
                    'category': 'syntax',
                    'traceback_snippet': stripped[:120],
                })

        return errors

    @staticmethod
    def _auto_fix_lint(content: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Auto-fix common lint issues in generated Python code.

        Returns (fixed_content, list_of_fix_records).
        """
        fixes: List[Dict[str, Any]] = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Bare except → except Exception
            if re.match(r'^(\s*)except\s*:\s*$', line.rstrip()):
                indent = re.match(r'^(\s*)', line).group(1)
                lines[i] = f'{indent}except Exception:'
                fixes.append({
                    'type': 'LintWarning',
                    'message': 'Bare except clause — auto-fixed to except Exception',
                    'file': '',
                    'line': i + 1,
                    'category': 'syntax',
                    'traceback_snippet': line.rstrip()[:120],
                    'auto_fixed': True,
                })
        return '\n'.join(lines), fixes

    def _validate_templates_pre_build(self, files: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Run pre-build validation on all template files.

        Returns (clean_files, all_errors) — files with errors are excluded.
        """
        clean: List[Dict[str, Any]] = []
        all_errors: List[Dict[str, Any]] = []

        # Auto-fix pass: mechanically fix known lint issues before validation
        for f in files:
            if f.get('path', '').endswith('.py') and f.get('content'):
                fixed_content, fix_records = self._auto_fix_lint(f['content'])
                if fix_records:
                    f['content'] = fixed_content
                    for rec in fix_records:
                        rec['file'] = f['path']
                    all_errors.extend(fix_records)
                    logger.info(f"Auto-fixed {len(fix_records)} lint issues in {f['path']}")

        for f in files:
            errs = self._validate_template_file(f.get('path', ''), f.get('content', ''))
            if errs:
                logger.warning(f"Pre-build validation: skipping {f['path']} ({len(errs)} errors)")
                all_errors.extend(errs)
            else:
                clean.append(f)

        if all_errors:
            logger.info(f"Pre-build validation: {len(all_errors)} errors in {len(files) - len(clean)}/{len(files)} files")
        else:
            logger.info(f"Pre-build validation: all {len(files)} files clean")

        return clean, all_errors

    # ------------------------------------------------------------------
    # Import resolution retry (Phase 2.2)
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_missing_import(error_output: str) -> Optional[str]:
        """Parse pytest/Python output to find missing module names."""
        # ModuleNotFoundError: No module named 'xyz'
        match = re.search(r"No module named ['\"]([\w.]+)['\"]", error_output)
        if match:
            return match.group(1).split('.')[0]
        # ImportError: cannot import name 'X' from 'Y'
        match = re.search(r"cannot import name ['\"]\w+['\"] from ['\"]([\w.]+)['\"]", error_output)
        if match:
            return match.group(1).split('.')[0]
        return None

    @staticmethod
    def _fix_missing_import(content: str, module_name: str) -> str:
        """Inject a missing import at the top of a Python file."""
        import_line = f"import {module_name}"
        if import_line in content:
            return content
        # Insert after any existing imports or after the docstring
        lines = content.split('\n')
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_at = i + 1
        lines.insert(insert_at, import_line)
        return '\n'.join(lines)

    def _attempt_import_resolution(self, files: List[Dict[str, Any]], error_output: str,
                                    max_retries: int = 3) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
        """Attempt to fix import errors in generated files.

        Returns (fixed_files, error_records, retries_used).
        """
        fix_errors: List[Dict[str, Any]] = []
        retries = 0

        remaining_error = error_output
        for attempt in range(max_retries):
            module = self._extract_missing_import(remaining_error)
            if not module:
                break

            retries += 1
            known = module in IMPORT_PACKAGE_MAP
            logger.info(f"Import resolution attempt {attempt + 1}: {module} (known={known})")

            fixed_any = False
            for f in files:
                if not f['path'].endswith('.py'):
                    continue
                content = f['content']
                if f"import {module}" in content or f"from {module}" in content:
                    continue
                # Check if this file likely needs the import
                if module in content or (module.replace('_', '') in content.lower()):
                    f['content'] = self._fix_missing_import(content, module)
                    f['size'] = len(f['content'].encode())
                    fixed_any = True
                    fix_errors.append({
                        'type': 'ImportError',
                        'message': f'Auto-resolved: added "import {module}"',
                        'file': f['path'],
                        'line': 0,
                        'category': 'import',
                        'traceback_snippet': f'Missing module: {module} (attempt {attempt + 1})',
                        'auto_fixed': True,
                    })

            if not fixed_any:
                fix_errors.append({
                    'type': 'ImportError',
                    'message': f'Could not auto-resolve: {module}',
                    'file': 'unknown',
                    'line': 0,
                    'category': 'import',
                    'traceback_snippet': remaining_error[:200],
                    'auto_fixed': False,
                })
                break

            # Re-validate to see if more imports are needed
            remaining_errors = []
            for f in files:
                remaining_errors.extend(self._validate_template_file(f['path'], f['content']))
            remaining_error = '\n'.join(e.get('message', '') for e in remaining_errors)

        return files, fix_errors, retries

    # ------------------------------------------------------------------
    # ML-consumable error reporting (Phase 2.3)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_error_report(all_errors: List[Dict[str, Any]], build_id: int,
                            duration: float) -> Dict[str, Any]:
        """Build a structured, ML-consumable error report.

        Schema designed for future intelligence layer consumption:
        - Per-error records with normalised type/message/file/line
        - Category counts for quick aggregation
        - Auto-fix tracking for learning which errors are mechanically fixable
        """
        breakdown = {cat: 0 for cat in ERROR_CATEGORIES}
        for err in all_errors:
            cat = err.get('category', 'runtime')
            if cat in breakdown:
                breakdown[cat] += 1
            else:
                breakdown['runtime'] += 1

        auto_fixed = [e for e in all_errors if e.get('auto_fixed')]
        unfixed = [e for e in all_errors if not e.get('auto_fixed')]

        return {
            'build_id': build_id,
            'timestamp': datetime.utcnow().isoformat(),
            'total_errors': len(all_errors),
            'total_auto_fixed': len(auto_fixed),
            'total_unfixed': len(unfixed),
            'breakdown': breakdown,
            'errors': [
                {
                    'type': e.get('type', 'Unknown'),
                    'message': e.get('message', '')[:500],
                    'file': e.get('file', 'unknown'),
                    'line': e.get('line', 0),
                    'category': e.get('category', 'runtime'),
                    'traceback_snippet': e.get('traceback_snippet', '')[:300],
                    'auto_fixed': e.get('auto_fixed', False),
                }
                for e in all_errors
            ],
            'duration_seconds': round(duration, 2),
        }

    # ------------------------------------------------------------------
    # Legacy error classification (kept for backward compat)
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_errors(files: List[Dict[str, Any]]) -> Dict[str, int]:
        breakdown = {cat: 0 for cat in ERROR_CATEGORIES}
        for f in files:
            if f.get('error'):
                if 'import' in f['error'].lower():
                    breakdown['import'] += 1
                elif 'syntax' in f['error'].lower():
                    breakdown['syntax'] += 1
                else:
                    breakdown['config'] += 1
        return breakdown

    # ------------------------------------------------------------------
    # Main entry point — YAML-driven TDD pipeline
    # ------------------------------------------------------------------

    def build_mvp(self, requirement: str, complexity: str, build_id: int,
                  db_session=None, recommendation_meta: dict = None,
                  iteration_meta: dict = None) -> Dict[str, Any]:
        """
        YAML-driven TDD build pipeline:
        1. Generate LAYER_REQUIREMENTS spec via AI
        2. RED phase   — generate failing tests
        3. GREEN phase — generate implementation
        4. REFACTOR    — improve quality
        5. Validate    — ast.parse all Python files
        6. Persist     — save files + metrics to DB
        """
        from models import MVPBuild, MVPBuildFile
        from services.spec_generator import generate_layer_spec_with_ai
        from services.ai_code_generator_orchestrator import AICodeGeneratorOrchestrator

        start = time.time()
        all_files: List[Dict[str, Any]] = []
        steps: List[Dict[str, Any]] = []
        collected_errors: List[Dict[str, Any]] = []
        total_ai_cost = 0.0
        syntax_errors = 0
        test_errors = 0

        def _step(name: str, detail: str):
            steps.append({'step': name, 'at': datetime.utcnow().isoformat(), 'detail': detail})
            if db_session:
                build = db_session.query(MVPBuild).get(build_id)
                if build:
                    build.build_steps = list(steps)
                    db_session.commit()

        try:
            # --- 1. Determine pipeline and generate spec ---
            ai_available = bool(self.anthropic_key)
            pipeline = 'yaml-tdd' if ai_available else 'jinja-template'

            if db_session:
                build = db_session.query(MVPBuild).get(build_id)
                if build:
                    build.status = 'GENERATING'
                    build.build_config = {'complexity': complexity, 'pipeline': pipeline}
                    db_session.commit()

            import tempfile
            work_dir = tempfile.mkdtemp(prefix=f'mvp_build_{build_id}_')
            work_path = Path(work_dir)
            green_status = 'SKIP'
            tests_passed = 0
            coverage = 0.0
            red_result = {}
            ac_verification: Optional[Dict[str, Any]] = None  # PR3 — set by VERIFICATION phase

            if ai_available:
                # --- AI pipeline: spec → RED → GREEN → REFACTOR ---
                spec, spec_cost = generate_layer_spec_with_ai(
                    requirement, complexity, build_id, self.anthropic_key,
                    db_session=db_session,
                    iteration_meta=iteration_meta,
                )
                total_ai_cost += spec_cost

                # Inject the original requirement text into the spec so the
                # orchestrator can include the full user brief in code-gen prompts.
                spec['_requirement_text'] = requirement

                ac_count = len(spec.get('acceptance_criteria', []))
                _step('SPEC_GENERATED', f"{ac_count} acceptance criteria, ${spec_cost:.4f}")
                logger.info(f"Build {build_id}: spec generated with {ac_count} AC")

                # Write spec to disk so orchestrator can reference it
                spec_file = work_path / 'LAYER_REQUIREMENTS.yaml'
                spec_file.write_text(yaml.dump(spec, default_flow_style=False))
                all_files.append({
                    'path': 'LAYER_REQUIREMENTS.yaml',
                    'content': spec_file.read_text(),
                    'size': spec_file.stat().st_size,
                    'phase': 'SPEC',
                })

                orchestrator = AICodeGeneratorOrchestrator({
                    'provider': 'anthropic',
                    'output_base_path': str(work_path),
                })

                # PR7 — stamp the build with the orchestrator's prompt vintage
                # so per-prompt-version correlation analysis can run later.
                if db_session:
                    try:
                        from services.ai_code_generator_orchestrator import PROMPT_VERSION
                        b_row = db_session.query(MVPBuild).get(build_id)
                        if b_row is not None and not b_row.prompt_version:
                            b_row.prompt_version = PROMPT_VERSION
                            db_session.commit()
                    except Exception as pv_exc:
                        logger.warning("Failed to stamp prompt_version on build %d: %s", build_id, pv_exc)

                # RED phase
                _step('RED_PHASE', 'Generating failing tests…')
                red_result = orchestrator.execute_red_phase(spec)
                red_status = red_result.get('status', 'UNKNOWN')
                _step('RED_PHASE_DONE', f"status={red_status}, tests_failed={red_result.get('tests_failed', 0)}")

                # GREEN phase
                _step('GREEN_PHASE', 'Generating implementation…')
                green_result = orchestrator.execute_green_phase(spec, red_result)
                green_status = green_result.get('status', 'UNKNOWN')
                tests_passed = green_result.get('tests_passed', 0)
                coverage = green_result.get('coverage', 0.0)
                green_attempts = green_result.get('attempts', 1)
                _step('GREEN_PHASE_DONE', f"status={green_status}, tests_passed={tests_passed}, coverage={coverage:.0%}, attempts={green_attempts}")

                # REFACTOR phase
                _step('REFACTOR_PHASE', 'Improving code quality…')
                refactor_result = orchestrator.execute_refactor_phase(green_result)
                _step('REFACTOR_DONE', f"status={refactor_result.get('status', 'UNKNOWN')}")

                # PR3 — VERIFICATION phase: surface the AC traceability report
                # already computed during GREEN. Persisted to MVPBuild below.
                _step('VERIFICATION', 'Mapping acceptance criteria → tests…')
                verification_result = orchestrator.execute_verification_phase(green_result)
                ac_verification = verification_result.get('ac_verification') or {}
                ver_summary = ac_verification.get('summary', {}) or {}
                _step(
                    'VERIFICATION_DONE',
                    f"verified={ver_summary.get('fully_verified_acs', 0)}/{ver_summary.get('total_acs', 0)} "
                    f"({ver_summary.get('verification_pct', 0)}%)"
                )

                # PR4 — Auto-REFACTOR loop. If verification is below threshold,
                # re-run GREEN (with retry-prompt feedback baked in) + REFACTOR
                # + VERIFICATION up to max_verification_retries additional times.
                min_pct = orchestrator.min_verification_pct
                max_retries = orchestrator.max_verification_retries
                ver_attempts = 1
                while ver_attempts <= max_retries:
                    pct = float(ver_summary.get('verification_pct', 0) or 0)
                    if pct >= min_pct:
                        break
                    _step(
                        'AUTO_REFACTOR',
                        f"retry {ver_attempts}/{max_retries}: pct={pct}% < threshold={min_pct}%",
                    )
                    green_result = orchestrator.execute_green_phase(spec, red_result)
                    green_status = green_result.get('status', 'UNKNOWN')
                    tests_passed = green_result.get('tests_passed', 0)
                    coverage = green_result.get('coverage', 0.0)
                    refactor_result = orchestrator.execute_refactor_phase(green_result)
                    verification_result = orchestrator.execute_verification_phase(green_result)
                    ac_verification = verification_result.get('ac_verification') or {}
                    ver_summary = ac_verification.get('summary', {}) or {}
                    ver_attempts += 1
                    _step(
                        'AUTO_REFACTOR_DONE',
                        f"attempt {ver_attempts}: verified="
                        f"{ver_summary.get('fully_verified_acs', 0)}/{ver_summary.get('total_acs', 0)} "
                        f"({ver_summary.get('verification_pct', 0)}%)"
                    )

                # Stamp retry metadata so the dashboard / telemetry can see it.
                if isinstance(ac_verification, dict):
                    ac_verification.setdefault('summary', {})
                    ac_verification['summary']['attempts'] = ver_attempts
                    ac_verification['summary']['threshold_pct'] = min_pct
                    ac_verification['summary']['threshold_met'] = (
                        float(ac_verification['summary'].get('verification_pct', 0) or 0) >= min_pct
                    )

                # Inject recommendation metadata into spec for dashboard hero
                if recommendation_meta:
                    spec['_meta'] = recommendation_meta

                # Inject iteration intelligence so downstream consumers
                # (spec persistence, debugging, future analytics) can see
                # exactly what evidence drove this iteration's requirements.
                if iteration_meta:
                    spec['_iteration_meta'] = iteration_meta

                # Collect generated files
                generated = orchestrator.collect_generated_files(spec=spec, build_id=build_id)
                all_files.extend(generated)
            else:
                # --- Template fallback: match + render Jinja templates ---
                logger.warning(f"Build {build_id}: ANTHROPIC_API_KEY not set — using template fallback")
                _step('TEMPLATE_FALLBACK', 'AI unavailable — using Jinja template pipeline')

                matches = self.match_templates(requirement, complexity)
                if not matches:
                    _step('TEMPLATE_MATCH', 'No matching templates found')
                else:
                    params = _default_params(requirement)
                    tpl_names = [m.template.name for m in matches]
                    _step('TEMPLATE_MATCH', f"Matched {len(matches)} templates: {', '.join(tpl_names)}")
                    for match in matches:
                        rendered = self._render_template_dir(match.template, params)
                        all_files.extend(rendered)
                    _step('TEMPLATE_RENDER', f"Rendered {len(all_files)} files from templates")

            # Phase 2.1: Pre-build validation gate
            _step('PRE_BUILD_VALIDATION', f"Validating {len(all_files)} files (AST + py_compile + lint)…")
            clean_files, pre_build_errors = self._validate_templates_pre_build(all_files)
            collected_errors.extend(pre_build_errors)

            syntax_errors = sum(1 for e in pre_build_errors if e['category'] == 'syntax' and not e.get('auto_fixed'))
            skipped_count = len(all_files) - len(clean_files)
            _step('PRE_BUILD_DONE', f"{skipped_count} files skipped, {syntax_errors} syntax errors found")

            # Phase 2.2: Import resolution retry loop
            error_output = '\n'.join(e.get('message', '') for e in pre_build_errors)
            if any(e.get('category') == 'import' or 'import' in e.get('message', '').lower() for e in pre_build_errors):
                _step('IMPORT_RESOLUTION', 'Attempting automated import fixes…')
                all_files, import_errors, retries_used = self._attempt_import_resolution(
                    all_files, error_output, max_retries=3
                )
                collected_errors.extend(import_errors)
                auto_fixed = sum(1 for e in import_errors if e.get('auto_fixed'))
                _step('IMPORT_RESOLUTION_DONE', f"{retries_used} retries, {auto_fixed} auto-fixed")

            # Count test errors from GREEN phase (AI pipeline only)
            if ai_available and green_status != 'PASS':
                test_errors = max(1, red_result.get('tests_failed', 1))
                collected_errors.append({
                    'type': 'TestFailure',
                    'message': f'{test_errors} test(s) failed in GREEN phase',
                    'file': 'pytest',
                    'line': 0,
                    'category': 'test',
                    'traceback_snippet': green_result.get('pytest_output', '')[:300],
                })

            total_errors = syntax_errors + test_errors
            _step('VALIDATION', f"{len(all_files)} files, {syntax_errors} syntax, {test_errors} test errors")

            # PR4 — BLOCK deploy on persistent verification failure. If we ran
            # the AI pipeline and the final ac_verification is below threshold,
            # treat the build as FAILED and log a structured error so the
            # dashboard / telemetry can attribute the block.
            verification_blocked = False
            if ai_available and ac_verification:
                _ver = ac_verification.get('summary', {}) or {}
                _met = _ver.get('threshold_met')
                if _met is False:  # explicit False (None means no AC list at all)
                    verification_blocked = True
                    block_pct = _ver.get('verification_pct', 0)
                    block_threshold = _ver.get('threshold_pct', 0)
                    block_attempts = _ver.get('attempts', 1)
                    collected_errors.append({
                        'type': 'VerificationBelowThreshold',
                        'message': (
                            f'AC verification {block_pct}% < threshold {block_threshold}% '
                            f'after {block_attempts} attempt(s) — deploy blocked'
                        ),
                        'file': 'verification_engine',
                        'line': 0,
                        'category': 'verification',
                        'traceback_snippet': '',
                    })
                    _step(
                        'VERIFICATION_BLOCKED_DEPLOY',
                        f"pct={block_pct}% < threshold={block_threshold}% (attempts={block_attempts})",
                    )
                    total_errors = max(total_errors, 1)

            # --- 6. Build ML-consumable error report + persist to DB ---
            duration = time.time() - start
            final_status = 'FAILED' if (total_errors > 0 or verification_blocked) else (
                'DEPLOYING' if os.getenv('RAILWAY_TOKEN') else 'LIVE'
            )

            # Phase 2.3: ML-consumable structured error report
            error_report = self._build_error_report(collected_errors, build_id, duration)

            if db_session:
                build = db_session.query(MVPBuild).get(build_id)
                if build:
                    build.s3_prefix = f"mvps/{build_id}/"
                    build.total_errors = total_errors
                    build.error_breakdown = error_report
                    build.duration_seconds = round(duration, 2)
                    build.ai_cost_usd = round(total_ai_cost, 6) if total_ai_cost > 0 else None
                    build.status = final_status
                    if ac_verification is not None:
                        build.ac_verification = ac_verification
                    if total_errors > 0:
                        build.error_message = f"{syntax_errors} syntax + {test_errors} test errors"
                    elif verification_blocked:
                        _ver = ac_verification.get('summary', {}) or {}
                        build.error_message = (
                            f"AC verification {_ver.get('verification_pct', 0)}% < threshold "
                            f"{_ver.get('threshold_pct', 0)}% after {_ver.get('attempts', 1)} attempt(s)"
                        )
                    for f in all_files:
                        db_session.add(MVPBuildFile(
                            build_id=build_id,
                            file_path=f['path'],
                            s3_key=f.get('s3_key', ''),
                            file_size_bytes=f.get('size', 0),
                            template_id=f.get('phase', 'tdd'),
                            content=f.get('content', ''),
                        ))
                    db_session.commit()

                # Auto-create ProductDeployment on successful build (Track G — M2)
                if db_session and final_status in ('LIVE', 'DEPLOYING'):
                    try:
                        from models import ProductDeployment, ExploitationRecommendation
                        build = db_session.query(MVPBuild).get(build_id)
                        rec_id = build.recommendation_id if build else None
                        # Only create if no deployment already exists for this build
                        existing_dep = db_session.query(ProductDeployment).filter(
                            ProductDeployment.build_id == build_id
                        ).first()
                        if not existing_dep and rec_id:
                            rec = db_session.query(ExploitationRecommendation).filter(
                                ExploitationRecommendation.id == rec_id
                            ).first()
                            product_name = requirement[:80] if requirement else f"MVP-{build_id}"
                            dep = ProductDeployment(
                                recommendation_id=rec_id,
                                build_id=build_id,
                                product_name=product_name,
                                app_id=f"mvp_{build_id}",
                                description=requirement[:255] if requirement else None,
                                tech_stack={"framework": "fastapi", "language": "python", "hosting": "railway"},
                                pricing_model="freemium",
                                market_category=getattr(rec, 'signal_display_name', None) if rec else None,
                                target_demographic=getattr(rec, 'target_display_name', None) if rec else None,
                                status="active",
                                deployed_at=datetime.utcnow(),
                            )
                            db_session.add(dep)
                            db_session.commit()
                            logger.info("Auto-created ProductDeployment for build %d", build_id)
                    except Exception as dep_exc:
                        logger.warning("Failed to auto-create ProductDeployment for build %d: %s", build_id, dep_exc)

                # PR5: seed BuildTelemetry row so the dashboard has something to
                # display before the first GA4/Stripe data lands. Idempotent.
                if db_session and final_status in ('LIVE', 'DEPLOYING'):
                    try:
                        from services.build_telemetry_service import recompute_build_telemetry
                        recompute_build_telemetry(db_session, build_id)
                    except Exception as tel_exc:
                        logger.warning("Failed to seed BuildTelemetry for build %d: %s", build_id, tel_exc)

            # _step after commit is best-effort — don't let it flip LIVE → FAILED
            try:
                _step('COMPLETE', f"{len(all_files)} files, {total_errors} errors, {round(duration, 1)}s")
            except Exception as step_exc:
                logger.warning("Build %d: COMPLETE step failed (status already committed): %s", build_id, step_exc)

            # Cleanup temp dir (best-effort)
            try:
                import shutil
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

            return {
                'build_id': build_id,
                'files': len(all_files),
                'errors': total_errors,
                'duration': round(duration, 2),
                'status': final_status,
                'tests_passed': tests_passed,
                'coverage': coverage,
            }

        except Exception as exc:
            logger.exception(f"Build {build_id} failed: {exc}")
            if db_session:
                build = db_session.query(MVPBuild).get(build_id)
                if build:
                    build.status = 'FAILED'
                    build.error_message = str(exc)[:500]
                    build.duration_seconds = round(time.time() - start, 2)
                    try:
                        from services.build_error_classifier import classify_build_error
                        classification = classify_build_error(str(exc))
                        build.error_breakdown = classification
                    except Exception:
                        pass
                    db_session.commit()
            return {'build_id': build_id, 'files': 0, 'errors': 1,
                    'duration': round(time.time() - start, 2), 'status': 'FAILED'}


def _default_params(requirement: str) -> Dict[str, Any]:
    """Generate sensible default template parameters from the requirement."""
    words = requirement.split()
    app_name = '_'.join(words[:3]).lower().replace('-', '_') if words else 'mvp_app'
    return {
        'app_name': app_name,
        'app_title': requirement[:60],
        'requirement': requirement,
        'project_name': app_name,
        'model_name': 'Item',
        'table_name': 'items',
        'include_email_capture': 'email' in requirement.lower(),
        'tagline': requirement[:80],
    }
