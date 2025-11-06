# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| 0.7.x   | :x:                |
| < 0.7   | :x:                |

## Reporting a Vulnerability

We take the security of MCP-FreeCAD seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

1. **DO NOT** open a public GitHub issue for security vulnerabilities
2. Email security concerns to: [info@cryptolinx.de](mailto:info@cryptolinx.de)
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Suggested fix (if you have one)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Assessment**: We will assess the vulnerability and determine its impact and severity
- **Timeline**: We aim to provide an initial response within 7 days
- **Updates**: We will keep you informed about the progress of fixing the vulnerability
- **Credit**: If you wish, we will acknowledge your responsible disclosure in the fix release notes

### Security Update Process

1. The security team will investigate and validate the report
2. A fix will be developed and tested
3. A security advisory will be published (if applicable)
4. A patch release will be created and published
5. The vulnerability details will be disclosed publicly after the patch is available

## Security Best Practices

When using MCP-FreeCAD, we recommend:

### API Keys and Credentials

- **Never commit API keys** or credentials to the repository
- Store API keys in environment variables or secure configuration files
- Use the encrypted configuration options when available
- Keep `api_keys.json` and similar files in `.gitignore`

### Network Security

- Use HTTPS/TLS for all network connections when possible
- Validate server certificates when connecting to external services
- Be cautious when connecting to unknown FreeCAD instances
- Use firewall rules to restrict access to FreeCAD server ports

### Code Execution

- Be aware that FreeCAD scripts can execute arbitrary code
- Review generated scripts before execution in production environments
- Use sandboxed environments when testing untrusted code
- Keep FreeCAD and dependencies up to date

### Docker Deployment

- Use official Docker images or build from trusted sources
- Don't run containers as root when possible
- Keep Docker and container images up to date
- Use Docker secrets for sensitive configuration

## Known Security Considerations

### FreeCAD Script Execution

MCP-FreeCAD can execute Python scripts in FreeCAD. While this is a core feature, users should:

- Only use trusted tool providers
- Review generated scripts in sensitive environments
- Understand that scripts have full access to FreeCAD's capabilities

### AI Provider Integration

When using AI providers (Claude, OpenAI, Google, OpenRouter):

- API keys should be stored securely
- Be aware of data sent to third-party APIs
- Review AI provider terms of service and privacy policies
- Consider using self-hosted models for sensitive projects

### Network Connections

The server opens network connections for:

- FreeCAD communication (configurable port)
- AI provider APIs (HTTPS)
- MCP protocol communication

Ensure these connections are properly secured in your environment.

## Vulnerability Disclosure Policy

We follow a coordinated vulnerability disclosure process:

1. Security researchers report vulnerabilities privately
2. We work to fix the vulnerability
3. A security advisory is prepared
4. The fix is released
5. The vulnerability is publicly disclosed with credit to the researcher

We kindly ask researchers to:

- Allow reasonable time for us to fix the vulnerability before public disclosure
- Make a good faith effort to avoid privacy violations, data destruction, and service interruption
- Not exploit the vulnerability beyond what is necessary to demonstrate it

## Contact

For security issues: [info@cryptolinx.de](mailto:info@cryptolinx.de)

For general support: [GitHub Issues](https://github.com/jango-blockchained/mcp-freecad/issues)

## Acknowledgments

We appreciate the security research community's efforts in responsibly disclosing vulnerabilities and helping us keep MCP-FreeCAD secure.
