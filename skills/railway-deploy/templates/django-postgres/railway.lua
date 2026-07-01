local railway = require("railway")

return railway {
    build = {
        builder = "NIXPACKS",
        buildCommand = "python manage.py migrate && python manage.py collectstatic --noinput",
        installCommand = "pip install --no-cache-dir -r requirements.txt",
    },
    deploy = {
        startCommand = "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT",
        healthcheckPath = "/health",
        healthcheckPort = 8000,
        restartPolicyType = "on-failure",
        restartRetryLimit = 10,
    },
    environment = {
        PYTHONUNBUFFERED = "1",
        DJANGO_SETTINGS_MODULE = "config.settings",
    },
    postgres = {
        enabled = true,
    },
}
