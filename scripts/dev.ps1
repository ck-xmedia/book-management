param()
$env:APP_ENV = $env:APP_ENV -ne $null ? $env:APP_ENV : "dev"
$env:PORT = $env:PORT -ne $null ? $env:PORT : "8080"
uvicorn app.main:app --reload --port $env:PORT --host 0.0.0.0 --workers 1
