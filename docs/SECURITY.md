# Clinical BERT API - Security Guide

## 🔒 Security Overview

This document outlines the comprehensive security measures implemented in the Clinical BERT Assertion API, designed to meet enterprise-grade security requirements and HIPAA compliance standards.

## 🛡️ Security Architecture

### Defense in Depth Strategy

The API implements multiple layers of security controls:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client Layer   │───▶│  Network Layer   │───▶│ Application Layer │
│                 │    │                  │    │                 │
│ • API Keys      │    │ • TLS 1.3        │    │ • Input          │
│ • Rate Limiting │    │ • DDoS Protection│    │   Validation     │
│ • Request Auth  │    │ • VPC Isolation  │    │ • Sanitization   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
       ┌─────────────────────────────────────────────────┼─────────────────┐
       │                                                 ▼                 │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐         │
│   Data Layer     │    │  Monitoring      │    │  Infrastructure  │         │
│                 │    │                  │    │                 │         │
│ • Encryption    │    │ • Audit Logs     │    │ • Access Control │         │
│ • PHI Protection│    │ • Threat Detection│    │ • Secrets Mgmt  │         │
│ • Data Masking  │    │ • SIEM Integration│    │ • Network Policies│         │
└─────────────────┘    └──────────────────┘    └─────────────────┘         │
       └─────────────────────────────────────────────────────────────────────┘
```

## 🔐 Authentication & Authorization

### API Key Authentication

#### Implementation
```python
# Authentication middleware
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from request headers"""
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    # Validate API key against secure store
    if not await validate_api_key_securely(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return credentials.credentials
```

#### API Key Management
```bash
# Generate secure API key
openssl rand -hex 32

# Store in Google Cloud Secret Manager
echo -n "your-generated-api-key" | gcloud secrets create api-key --data-file=-

# Access in application
API_KEY=$(gcloud secrets versions access latest --secret=api-key)
```

### OAuth 2.0 Support (Optional)

#### Configuration
```python
from authlib.integrations.fastapi_oauth2 import OAuth2TokenBearer
from authlib.integrations.httpx_oauth2 import OAuth2Client

# OAuth2 configuration
OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
OAUTH2_TOKEN_URL = os.getenv("OAUTH2_TOKEN_URL")

oauth2_scheme = OAuth2TokenBearer(
    token_url=OAUTH2_TOKEN_URL,
    client_id=OAUTH2_CLIENT_ID,
    client_secret=OAUTH2_CLIENT_SECRET
)
```

## 🛡️ Data Protection

### PHI (Protected Health Information) Handling

#### Data Classification
- **Public Data**: API responses, error messages
- **Internal Data**: Logs, metrics, configuration
- **Sensitive Data**: API keys, tokens, credentials
- **PHI Data**: Clinical text, patient information

#### Encryption Strategy

**At Rest:**
```python
from cryptography.fernet import Fernet
import os

# Generate encryption key
def generate_key():
    return Fernet.generate_key()

# Encrypt sensitive data
def encrypt_data(data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

# Decrypt sensitive data
def decrypt_data(encrypted_data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()
```

**In Transit:**
- TLS 1.3 encryption for all HTTP communications
- Certificate pinning for production environments
- HSTS (HTTP Strict Transport Security) headers

### Data Sanitization

#### Input Validation
```python
from pydantic import BaseModel, validator
import re

class PredictionRequest(BaseModel):
    sentence: str

    @validator('sentence')
    def validate_sentence(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Sentence cannot be empty')

        if len(v) > 512:
            raise ValueError('Sentence too long (max 512 characters)')

        # Remove potentially harmful characters
        v = re.sub(r'[^\w\s.,!?-]', '', v)

        return v.strip()
```

#### SQL Injection Prevention
- Parameterized queries (when database is used)
- Input sanitization for all text inputs
- Prepared statements for data access

## 🔍 Security Monitoring

### Real-time Threat Detection

#### Log Analysis
```python
import logging
import json
from datetime import datetime

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)

        # Structured logging format
        formatter = logging.Formatter(
            json.dumps({
                'timestamp': '%(asctime)s',
                'level': '%(levelname)s',
                'service': 'clinical-bert-api',
                'message': '%(message)s',
                'request_id': '%(request_id)s',
                'ip_address': '%(ip_address)s',
                'user_agent': '%(user_agent)s'
            })
        )

    def log_security_event(self, event_type: str, details: dict, request_id: str = None):
        """Log security-related events"""
        self.logger.info(
            f"Security event: {event_type}",
            extra={
                'request_id': request_id or 'unknown',
                'event_type': event_type,
                'details': json.dumps(details),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
```

#### Automated Alerts

**Prometheus Alerting Rules:**
```yaml
groups:
  - name: security_alerts
    rules:
      - alert: SuspiciousActivity
        expr: rate(security_events_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Suspicious activity detected"
          description: "High rate of security events: {{ $value }}/min"

      - alert: FailedAuthentications
        expr: rate(authentication_failures_total[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High authentication failure rate"
          description: "Authentication failures: {{ $value }}/min"
```

### Intrusion Detection

#### Rate Limiting Implementation
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

# Apply to FastAPI app
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Route-specific limits
@app.get("/health")
@limiter.limit("100/minute")
async def health_check():
    return {"status": "healthy"}

@app.post("/predict")
@limiter.limit("50/minute")
async def predict(request: PredictionRequest):
    # Prediction logic
    pass
```

#### DDoS Protection
- Cloud Armor policies for Google Cloud Run
- Rate limiting at application level
- Request size limits and timeouts
- Connection pooling limits

## 📋 Compliance Requirements

### HIPAA Security Rule

#### Administrative Safeguards
- ✅ Security management process
- ✅ Assigned security responsibility
- ✅ Workforce security
- ✅ Information access management
- ✅ Security awareness training
- ✅ Security incident procedures
- ✅ Contingency plan
- ✅ Evaluation

#### Physical Safeguards
- ✅ Facility access controls
- ✅ Workstation use
- ✅ Workstation security
- ✅ Device and media controls

#### Technical Safeguards
- ✅ Access control
- ✅ Audit controls
- ✅ Integrity
- ✅ Person or entity authentication
- ✅ Transmission security

### SOC 2 Type II Compliance

#### Security Criteria
- ✅ Organization and management
- ✅ Communications
- ✅ Risk management
- ✅ Monitoring activities
- ✅ Control activities

#### Availability Criteria
- ✅ Processing integrity
- ✅ System availability
- ✅ Confidentiality
- ✅ Privacy

## 🔧 Security Hardening

### Container Security

#### Dockerfile Best Practices
```dockerfile
# Use official base images
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install only necessary packages
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application with appropriate permissions
COPY --chown=appuser:appuser . /app
WORKDIR /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080
CMD ["python", "main.py"]
```

#### Image Scanning
```bash
# Scan for vulnerabilities
docker scan clinical-bert-api:latest

# Use Trivy for comprehensive scanning
trivy image clinical-bert-api:latest

# Integrate with CI/CD pipeline
- name: Security Scan
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'image'
    scan-ref: 'us-central1-docker.pkg.dev/project/repo/image:latest'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### Application Security

#### Dependency Management
```bash
# Regular dependency updates
pip install --upgrade -r requirements.txt

# Security vulnerability scanning
safety check

# Automated dependency updates
pip-tools compile --upgrade
```

#### Secret Management
```python
import os
from google.cloud import secretmanager

def get_secret(secret_name: str) -> str:
    """Retrieve secret from Google Cloud Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"

    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
API_KEY = get_secret("api-key")
DATABASE_URL = get_secret("database-url")
```

## 🚨 Incident Response

### Security Incident Process

#### Detection Phase
1. **Automated Alerts**: Monitoring systems detect anomalies
2. **Manual Reports**: Security team receives incident reports
3. **Log Analysis**: Review security logs for indicators
4. **Initial Assessment**: Determine incident scope and impact

#### Response Phase
1. **Containment**: Isolate affected systems
2. **Investigation**: Gather evidence and analyze root cause
3. **Recovery**: Restore systems from clean backups
4. **Communication**: Notify stakeholders and regulatory bodies

#### Post-Incident Phase
1. **Documentation**: Record incident details and response
2. **Lessons Learned**: Identify improvements and preventive measures
3. **Implementation**: Apply security enhancements
4. **Review**: Update incident response procedures

### Emergency Contacts

#### Security Team
- **Primary**: security@company.com
- **Secondary**: security-backup@company.com
- **Phone**: +1-800-SECURITY

#### Development Team
- **Lead Developer**: dev-lead@company.com
- **On-call Engineer**: oncall@company.com
- **DevOps Team**: devops@company.com

#### Executive Team
- **CISO**: ciso@company.com
- **CTO**: cto@company.com
- **CEO**: ceo@company.com

## 📊 Security Metrics

### Key Security Indicators

#### Authentication Metrics
- Successful authentication rate
- Failed authentication attempts
- API key usage patterns
- Token expiration rates

#### Access Control Metrics
- Unauthorized access attempts
- Permission violation incidents
- Role-based access patterns
- Administrative access usage

#### Data Protection Metrics
- Encryption success rates
- Data masking effectiveness
- PHI exposure incidents
- Backup integrity checks

### Security Dashboard

#### Grafana Panels
```json
{
  "title": "Security Overview",
  "panels": [
    {
      "title": "Authentication Failures",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(authentication_failures_total[5m])",
          "legendFormat": "Failures/min"
        }
      ]
    },
    {
      "title": "Security Events",
      "type": "table",
      "targets": [
        {
          "expr": "security_events_total",
          "legendFormat": "Total Events"
        }
      ]
    },
    {
      "title": "Access Patterns",
      "type": "heatmap",
      "targets": [
        {
          "expr": "rate(http_requests_total[1h])",
          "legendFormat": "Requests/hour"
        }
      ]
    }
  ]
}
```

## 🔄 Security Updates

### Regular Security Procedures

#### Weekly Tasks
- [ ] Review security logs and alerts
- [ ] Update security signatures
- [ ] Monitor vulnerability databases
- [ ] Verify backup integrity

#### Monthly Tasks
- [ ] Security patch deployment
- [ ] Access control audits
- [ ] Security training updates
- [ ] Compliance documentation review

#### Quarterly Tasks
- [ ] Penetration testing
- [ ] Security assessments
- [ ] Incident response drills
- [ ] Third-party vendor reviews

### Security Training

#### Required Training
- **Annual Security Awareness**: All employees
- **Role-specific Training**: Developers, administrators
- **HIPAA Training**: Healthcare personnel
- **Incident Response Training**: Security team

#### Training Resources
- **OWASP Top 10**: Web application security
- **NIST Cybersecurity Framework**: Security best practices
- **HIPAA Security Rule**: Healthcare compliance
- **Zero Trust Architecture**: Modern security principles

---

## 📞 Security Support

### Reporting Security Issues

#### Responsible Disclosure
- **Email**: security@company.com
- **PGP Key**: Available at security.company.com/pgp
- **Response Time**: <24 hours for critical issues
- **Bounty Program**: Available for qualifying disclosures

#### Security Issue Template
```
Subject: Security Vulnerability Report

Description:
- Vulnerability type:
- Affected component:
- Severity level:
- Steps to reproduce:
- Potential impact:
- Suggested fix:

Contact Information:
- Name:
- Email:
- Phone:
- PGP Key ID:
```

### Security Documentation

#### Available Resources
- **Security Policy**: Comprehensive security policies and procedures
- **Incident Response Plan**: Detailed incident handling procedures
- **Compliance Documentation**: HIPAA and SOC 2 compliance evidence
- **Security Architecture**: System security design and controls

---

**🔒 Security First • 🛡️ HIPAA Compliant • 🚨 Zero Trust**

*Enterprise-grade security for healthcare AI*
