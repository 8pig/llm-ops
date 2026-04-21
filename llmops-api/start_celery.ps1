# start_celery.ps1
$env:PYTHONPATH = $PSScriptRoot
uv run celery -A app.http.app.celery worker -l info --pool eventlet