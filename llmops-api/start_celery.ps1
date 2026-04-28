# start_celery.ps1

$env:PYTHONPATH = $PSScriptRoot
$env:PYTHONWARNINGS = "ignore::SyntaxWarning,ignore::DeprecationWarning,ignore::ResourceWarning,ignore::UserWarning"
Get-ChildItem -Path D:\code\llm-ops\llmops-api -Filter *.pyc -Recurse -File | Remove-Item -Force
Get-ChildItem -Path D:\code\llm-ops\llmops-api -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force
uv run celery -A app.http.app.celery worker -l info --pool eventlet