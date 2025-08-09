{
  "mcpServers": {
    "Github": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@smithery-ai/github",
        "--config",
        "{\"githubPersonalAccessToken\":\"***REDACTED***\"}"
      ]
    },
    "Browser-Tools": {
      "command": "npx",
      "args": [
        "@agentdeskai/browser-tools-mcp@1.1.0"
      ]
    },
    "iTerm": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "iterm-mcp",
        "--config",
        "{}"
      ]
    },
    "Puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@smithery-ai/puppeteer",
        "--config",
        "{}"
      ]
    },
    "SequentialThinking": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ]
    },
    "Gordon": {
      "command": "docker",
      "args": [
        "ai",
        "mcpserver"
      ],
      "notes": "Requires Docker Desktop to be installed and running."
    },
    "context7": {
      "command": "npx",
      "args": [
        "-y",
        "@upstash/context7-mcp@latest"
      ],
      "notes": "Provides up-to-date documentation for libraries."
    },
    "sequential-thinking": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ],
      "env": {}
    }
  }
}
