local railway = require("railway")

return railway {
    build = {
        builder = "NIXPACKS",
        buildCommand = "pip install --no-cache-dir -r requirements.txt",
        installCommand = "pip install --no-cache-dir -r requirements.txt",
    },
    deploy = {
        startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT",
        healthcheckPath = "/health",
        healthcheckPort = 8000,
        restartPolicyType = "on-failure",
        restartRetryLimit = 10,
    },
    environment = {
        PYTHONUNBUFFERED = "1",
    },
    postgres = {
        enabled = true,
    },
}
