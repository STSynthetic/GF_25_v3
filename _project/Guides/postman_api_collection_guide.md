# Postman Collection JSON Format: Complete Import Specification Guide

Creating properly formatted Postman collections requires understanding the official JSON schema, adhering to desktop import requirements, and avoiding common formatting pitfalls. **The most critical requirement is using Collection Format v2.1.0 with the correct schema URL and maintaining UTF-8 encoding throughout your JSON files**.

## Official collection format and required structure

The Postman Collection Format follows a versioned JSON schema specification maintained at `github.com/postmanlabs/schemas`. The current standard v2.1.0 uses JSON Schema Draft-07 and provides comprehensive support for modern API workflows. Every valid collection must include these minimum required fields:

```json
{
  "info": {
    "name": "Collection Name",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": []
}
```

The **schema URL must be exactly as shown** - a common import failure occurs when antivirus software modifies these URLs during email transmission, wrapping them with security redirects like `urldefense.proofpoint.com`. This modification causes immediate import rejection with "format not recognized" errors. Share collections via ZIP files or cloud storage to avoid this issue.

Collection structure follows a hierarchical pattern where items can be either requests or folders containing nested items. Each request requires a method and URL, while optional components include authentication, headers, body content, pre-request scripts, and test scripts. The v2.1.0 format introduced enhanced authentication arrays and improved variable scoping compared to the legacy v2.0.0 object-based authentication structure.

## Desktop import specifications and limitations

Postman desktop applications support both v2.1.0 and v2.0.0 collection formats with automatic version detection during import. **Collections must use UTF-8 encoding and should remain under 15MB for reliable imports** - larger files often fail silently, with community reports indicating consistent failures above 80MB.

Desktop versions offer significant advantages over web imports, including direct file system access, no CORS limitations, and support for advanced proxy configurations. The desktop application reads files from the working directory (`~/Postman/files` on macOS/Linux or `%userprofile%\Postman\files` on Windows) by default, though this can be customized in settings.

Version 1.0.0 collections are completely unsupported and require conversion using the postman-collection-transformer CLI tool before import. Authentication methods in v2.1.0 use array structures that aren't backward compatible with v2.0.0's object format, potentially causing import issues when mixing versions.

## Common import errors and proven solutions

The most frequent import error stems from **malformed JSON syntax**, including missing quotes, unescaped backslashes in file paths, or trailing commas. Windows file paths require double escaping: `"path": "c:\\\\temp\\\\file.txt"` rather than `"path": "c:\temp\file.txt"`. Validate your JSON structure using online validators before attempting import.

Schema validation failures occur when required fields are missing or incorrectly formatted. Collections exported from older Postman versions may reference outdated schema URLs or use incompatible authentication structures. Update all schema references to `https://schema.getpostman.com/json/collection/v2.1.0/collection.json` and ensure the info object contains both name and schema properties.

**Environment variable resolution** presents unique challenges in pre-request scripts. Variables referenced as `{{variableName}}` in request URLs resolve automatically, but scripts require explicit retrieval using `pm.environment.get('variableName')`. This timing difference causes "undefined variable" errors when scripts attempt to use the mustache syntax directly.

Character encoding issues manifest as corrupted text for non-ASCII characters. Set explicit UTF-8 encoding in Content-Type headers (`application/json; charset=UTF-8`) and ensure source files use UTF-8 encoding throughout. Special characters in URLs require encoding using `encodeURIComponent()` in pre-request scripts.

## Working examples and validation approaches

Industry-standard collections demonstrate proper structure implementation. The Salesforce API collection contains over 250 requests with OAuth 2.0 authentication, bulk operations, and comprehensive environment variables. Box and HERE Maps collections showcase folder organization, complex authentication flows, and proper variable scoping across nested requests.

A complete working example with authentication and variables:

```json
{
  "info": {
    "name": "API Integration Collection",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    "_postman_id": "12345678-1234-1234-1234-123456789012",
    "description": "Production API endpoints with OAuth 2.0"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "item": [
    {
      "name": "User Management",
      "item": [
        {
          "name": "Get User Profile",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Accept",
                "value": "application/json"
              }
            ],
            "url": {
              "raw": "{{baseUrl}}/api/v1/users/{{userId}}",
              "host": ["{{baseUrl}}"],
              "path": ["api", "v1", "users", "{{userId}}"]
            }
          },
          "response": []
        }
      ]
    }
  ],
  "event": [
    {
      "listen": "prerequest",
      "script": {
        "type": "text/javascript",
        "exec": [
          "// Refresh token if needed",
          "const tokenExpiry = pm.globals.get('token_expiry');",
          "if (!tokenExpiry || Date.now() > tokenExpiry) {",
          "    // Token refresh logic here",
          "}"
        ]
      }
    }
  ],
  "variable": [
    {
      "key": "baseUrl",
      "value": "https://api.example.com",
      "type": "string"
    },
    {
      "key": "userId",
      "value": "",
      "type": "string"
    }
  ]
}
```

## Validation tools and verification methods

**Newman CLI provides the most reliable validation method** for collections before import. Install via npm (`npm install -g newman`) and validate collections using `newman run collection.json`. Failed validations report specific schema violations and structural issues.

Programmatic validation using Node.js and the official schema:

```javascript
const https = require('https');
const validate = require('is-my-json-valid');

https.get('https://schema.getpostman.com/json/collection/v2.1.0/', (response) => {
  let body = '';
  response.on('data', (d) => { body += d; });
  response.on('end', () => {
    const validator = validate(JSON.parse(body));
    const isValid = validator(yourCollection);
    if (!isValid) console.log('Validation errors:', validator.errors);
  });
});
```

The new Postman CLI offers additional governance validation beyond basic schema checking, particularly useful for enterprise environments requiring API compliance verification.

For immediate validation, Postman's built-in import process validates collections against the schema during import. However, pre-import validation saves time by identifying issues before attempting import, especially for large collections or automated workflows.

## Best practices for reliable imports

Structure collections hierarchically using folders to organize related endpoints. Limit collection size by extracting large test datasets to separate files and referencing them via file paths or URLs. Include descriptive names and documentation at every level to improve maintainability.

Store sensitive data like API keys in Postman Vault rather than plain environment variables. Use consistent variable naming conventions and scope variables appropriately - global for cross-collection values, environment for deployment-specific settings, and collection variables for request-specific data.

Test collections in a clean Postman instance before distribution to ensure all dependencies are properly included. Export using v2.1.0 format exclusively and validate the exported JSON before sharing. When troubleshooting failed imports, start with a minimal collection structure and progressively add complexity to isolate issues.

Regular validation during development prevents accumulation of structural issues. Integrate Newman validation into CI/CD pipelines to catch format problems before they reach production environments. This proactive approach ensures collections remain importable across Postman versions and platforms.