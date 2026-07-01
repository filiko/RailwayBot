local railway = require("railway")

return railway {
    build = {
        builder = "NIXPACKS",
        buildCommand = "go build -o server .",
        installCommand = "go mod download",
    },
    deploy = {
        startCommand = "./server",
        healthcheckPath = "/health",
        healthcheckPort = 8080,
        restartPolicyType = "on-failure",
        restartRetryLimit = 10,
    },
    environment = {
        PORT = "8080",
    },
    postgres = {
        enabled = true,
    },
}
