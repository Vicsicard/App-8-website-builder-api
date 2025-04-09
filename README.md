# Self Cast Studios Website Builder API

This is the Python backend for the Self Cast Studios Website Builder system. It handles the generation and management of personal brand websites.

## Features

- Website generation from templates
- Content management
- Build tracking
- Publishing system
- API endpoints for dashboard integration

## Tech Stack

- Python 3.11
- FastAPI
- Supabase
- Jinja2 Templates

## Environment Variables

Required environment variables:

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_PROJECT_ID=your_project_id
SUPABASE_ANON_KEY=your_anon_key
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python run_api.py

# Run tests
python -m pytest tests/
```

## Deployment

This application is deployed on Render. The deployment process is automated through GitHub integration.

## Related Projects

This API is part of the Self Cast Studios ecosystem:
- Dashboard (Next.js frontend)
- Content Analysis
- Video Agent
- Transcript Builder
