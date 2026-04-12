{
  "mcpServers": {
    "monolith": {
      "type": "http",
      "url": "http://localhost:9316/mcp"
    },
    "unreal-mcp": {
      "command": "npx",
      "args": ["-y", "@runreal/unreal-mcp"]
    },
    "unrealclaude-bridge": {
      "command": "node",
      "args": ["{{UE_PROJECT_ROOT}}/Plugins/UnrealClaude/Resources/mcp-bridge/index.js"],
      "env": {
        "UNREAL_MCP_URL": "http://localhost:3000",
        "INJECT_CONTEXT": "true"
      }
    }
  }
}
