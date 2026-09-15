# start_celery.ps1

$env:PYTHONPATH = $PSScriptRoot
$env:PYTHONWARNINGS = "ignore::SyntaxWarning,ignore::DeprecationWarning,ignore::ResourceWarning,ignore::UserWarning"

# 1.清理当前项目的字节码缓存，跳过.venv避免递归扫描数万文件
$excludeVenv = { $_.FullName -notmatch '[\\/]\.venv[\\/]' }
Get-ChildItem -Path $PSScriptRoot -Filter *.pyc -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object $excludeVenv |
    Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $PSScriptRoot -Filter __pycache__ -Recurse -Directory -ErrorAction SilentlyContinue |
    Where-Object $excludeVenv |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# 2.启动Celery Worker
#    注意：这里用 python -m celery 而不是 celery.exe，因为.venv\Scripts下所有
#    *.exe启动器当前均已失效（Failed to canonicalize script path），
#    而 python -m 直接走包入口，可以绕开该问题
& "$PSScriptRoot\.venv\Scripts\python.exe" -m celery -A app.http.app.celery worker -l info --pool eventlet
