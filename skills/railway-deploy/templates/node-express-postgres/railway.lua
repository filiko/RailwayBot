local railway = require("railway")

return railway {
    build = {
        builder = "NIXPACKS",
        buildCommand = "{{BUILD_COMMAND}}",
        installCommand = "npm install",
    },
    deploy = {
        startCommand = "{{START_COMMAND}}",
        healthcheckPath = "/health",
        healthcheckPort = {{PORT}},
        restartPolicyType = "on-failure",
        restartRetryLimit = 10,
    },
    environment = {
        NODE_ENV = "production",
    },
    postgres = {
        enabled = true,
    },
    redis = {
        enabled = false,
    },
}
