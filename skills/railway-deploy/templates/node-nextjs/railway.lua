local railway = require("railway")

return railway {
    build = {
        builder = "NIXPACKS",
        buildCommand = "npm run build",
        installCommand = "npm install",
    },
    deploy = {
        startCommand = "npm start",
        healthcheckPath = "/",
        healthcheckPort = 3000,
        restartPolicyType = "on-failure",
        restartRetryLimit = 10,
    },
    environment = {
        NODE_ENV = "production",
    },
}
