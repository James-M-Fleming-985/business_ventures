MVP Template Pack
=================

Included templates:
- `tpl-backend-crud-repo.jinja` - SQLAlchemy model + repository + CRUD
- `tpl-frontend-landing.jinja` - React + TypeScript landing component

Usage:
- Use `template_renderer.py` to render a Jinja2 template with a YAML variables file.

Example:

```
python template_renderer.py templates/mvp/tpl-backend-crud-repo.jinja --vars templates/mvp/samples/crud_vars.yaml
```
