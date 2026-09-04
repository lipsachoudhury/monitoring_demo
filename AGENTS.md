# Agent Guidelines — Python Flask Application

## Stack
- **Language:** Python 3.11+
- **Framework:** Flask
- **Package Manager:** pip with `requirements.txt`

## Project Structure
```
app/
├── app.py            # App factory & entry point
├── config.py         # Config classes (Dev / Prod)
├── requirements.txt
├── routes/           # Blueprints
├── templates/        # Jinja2 HTML templates
└── static/           # CSS, JS, images
```

## Code Rules
- Use **Flask Blueprints** for route organisation
- Use `python-dotenv` for env variables — never hardcode secrets
- Return JSON responses with `jsonify()` for API endpoints
- Use `flask.abort()` for HTTP errors, not manual responses
- Keep route handlers thin — move logic into service functions

## Conventions
- Snake_case for variables and functions
- Config via `app.config.from_object()` using config classes
- Always use `if __name__ == "__main__":` guard in `app.py`

## Dependencies
Only add packages that are genuinely needed. Pin versions in `requirements.txt`.
```
flask>=3.0
python-dotenv>=1.0
```

## What to Avoid
- Do not use `app.run()` in production — use Gunicorn
- Do not import `app` directly across modules — use `current_app` or blueprints
- Do not put business logic inside route decorators
