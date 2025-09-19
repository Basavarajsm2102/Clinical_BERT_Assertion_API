# Clinical BERT API - Monitoring & Observability Guide

## 📊 Monitoring Overview

This guide covers the comprehensive monitoring and observability setup for the Clinical BERT Assertion API, designed to provide real-time insights into system performance, health, and operational metrics.

## 🏗️ Monitoring Architecture

### Observability Stack

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Prometheus     │───▶│   Grafana       │
│                 │    │                  │    │                 │
│ • Health Checks │    │ • Metrics        │    │ • Dashboards    │
│ • Performance   │    │   Collection     │    │ • Alerts        │
│ • Business KPIs │    │ • Alert Rules    │    │ • Reports       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
       ┌─────────────────────────────────────────────────┼─────────────────┐
       │                                                 ▼                 │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐         │
│   Cloud Logging │    │   Alert Manager  │    │   Notification   │         │
│                 │    │                  │    │                 │         │
│ • Structured    │    │ • Alert Routing  │    │ • Email         │         │
│   Logs          │    │ • Escalation     │    │ • Slack         │         │
│ • Audit Trails  │    │ • Silencing      │    │ • PagerDuty     │         │
└─────────────────┘    └──────────────────┘    └─────────────────┘         │
       └─────────────────────────────────────────────────────────────────────┘
```

## 📈 Key Metrics

### Application Metrics

#### Performance Metrics
```prometheus
# Response Time (histogram)
http_request_duration_seconds{quantile="0.5"}  # P50
http_request_duration_seconds{quantile="0.95"} # P95
http_request_duration_seconds{quantile="0.99"} # P99

# Request Rate
rate(http_requests_total[5m])

# Error Rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

#### Business Metrics
```prometheus
# Model Performance
model_predictions_total{label="PRESENT"}
model_predictions_total{label="ABSENT"}
model_predictions_total{label="POSSIBLE"}

# Usage Metrics
api_requests_total{endpoint="/predict"}
api_requests_total{endpoint="/predict/batch"}

# Accuracy Metrics
model_accuracy_ratio
prediction_confidence_avg
```

### System Metrics

#### Resource Utilization
```prometheus
# CPU Usage
rate(process_cpu_user_seconds_total[5m])
rate(process_cpu_system_seconds_total[5m])

# Memory Usage
process_resident_memory_bytes / 1024 / 1024  # MB
(process_resident_memory_bytes / process_virtual_memory_bytes) * 100  # %

# Disk Usage
disk_used_percent{mountpoint="/"} > 80
```

#### Container Metrics
```prometheus
# Container Resources
container_cpu_usage_seconds_total
container_memory_usage_bytes
container_network_receive_bytes_total
container_network_transmit_bytes_total
```

## 📊 Grafana Dashboards

### Main Dashboard Configuration

#### System Overview Panel
```json
{
  "title": "System Overview",
  "type": "stat",
  "targets": [
    {
      "expr": "up{job='clinical-bert-api'}",
      "legendFormat": "Service Status"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "mappings": [
        {
          "options": {
            "0": {
              "text": "DOWN",
              "color": "red"
            },
            "1": {
              "text": "UP",
              "color": "green"
            }
          },
          "type": "value"
        }
      ]
    }
  }
}
```

#### Response Time Graph
```json
{
  "title": "Response Time Percentiles",
  "type": "graph",
  "targets": [
    {
      "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m])) * 1000",
      "legendFormat": "P50 (ms)"
    },
    {
      "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) * 1000",
      "legendFormat": "P95 (ms)"
    },
    {
      "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) * 1000",
      "legendFormat": "P99 (ms)"
    }
  ]
}
```

#### Request Rate Panel
```json
{
  "title": "Request Rate",
  "type": "graph",
  "targets": [
    {
      "expr": "rate(http_requests_total[5m])",
      "legendFormat": "Requests/sec"
    }
  ]
}
```

#### Error Rate Panel
```json
{
  "title": "Error Rate",
  "type": "graph",
  "targets": [
    {
      "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
      "legendFormat": "Error Rate (%)"
    }
  ]
}
```

#### Model Performance Panel
```json
{
  "title": "Model Predictions",
  "type": "bargauge",
  "targets": [
    {
      "expr": "sum(model_predictions_total)",
      "legendFormat": "Total Predictions"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "mappings": [
        {
          "options": {
            "from": 0,
            "to": 1000,
            "result": {
              "text": "LOW",
              "color": "green"
            }
          },
          "type": "range"
        },
        {
          "options": {
            "from": 1000,
            "to": 5000,
            "result": {
              "text": "MEDIUM",
              "color": "orange"
            }
          },
          "type": "range"
        },
        {
          "options": {
            "from": 5000,
            "to": 10000,
            "result": {
              "text": "HIGH",
              "color": "red"
            }
          },
          "type": "range"
        }
      ]
    }
  }
}
```

## 🚨 Alerting Configuration

### Prometheus Alert Rules

#### Critical Alerts
```yaml
groups:
  - name: clinical_bert_api_critical
    rules:
      - alert: ServiceDown
        expr: up{job="clinical-bert-api"} == 0
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Clinical BERT API is down"
          description: "Service has been down for 5 minutes"
          runbook_url: "https://docs.company.com/runbooks/clinical-bert-down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | printf \"%.2f\" }}%"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2.0
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value | printf \"%.2f\" }}s"
```

#### Warning Alerts
```yaml
groups:
  - name: clinical_bert_api_warning
    rules:
      - alert: ModerateErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Moderate error rate detected"
          description: "Error rate is {{ $value | printf \"%.2f\" }}%"

      - alert: ElevatedResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Elevated response time detected"
          description: "95th percentile response time is {{ $value | printf \"%.2f\" }}s"

      - alert: HighMemoryUsage
        expr: (process_resident_memory_bytes / 1024 / 1024 / 1024) > 3
        for: 15m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is {{ $value | printf \"%.2f\" }}GB"
```

#### Info Alerts
```yaml
groups:
  - name: clinical_bert_api_info
    rules:
      - alert: DeploymentCompleted
        expr: up{job="clinical-bert-api"} == 1 and up{job="clinical-bert-api"} offset 5m == 0
        for: 1m
        labels:
          severity: info
          team: platform
        annotations:
          summary: "Deployment completed"
          description: "Clinical BERT API deployment completed successfully"

      - alert: HighTraffic
        expr: rate(http_requests_total[5m]) > 100
        for: 5m
        labels:
          severity: info
          team: platform
        annotations:
          summary: "High traffic detected"
          description: "Request rate is {{ $value | printf \"%.0f\" }} req/sec"
```

### Alert Manager Configuration

#### Routing Configuration
```yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-pager'
    continue: true
  - match:
      severity: warning
    receiver: 'warning-slack'
  - match:
      severity: info
    receiver: 'info-email'

receivers:
- name: 'default'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/...'
    channel: '#alerts'
    title: '{{ .GroupLabels.alertname }}'
    text: '{{ .CommonAnnotations.description }}'

- name: 'critical-pager'
  pagerduty_configs:
  - service_key: 'your-pagerduty-service-key'
    description: '{{ .CommonAnnotations.summary }}'

- name: 'warning-slack'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/...'
    channel: '#warnings'
    title: '{{ .GroupLabels.alertname }}'

- name: 'info-email'
  email_configs:
  - to: 'team@company.com'
    from: 'alerts@company.com'
    smarthost: 'smtp.company.com:587'
    auth_username: 'alerts@company.com'
    auth_password: 'your-smtp-password'
```

## 📝 Logging Strategy

### Structured Logging Implementation

#### Python Logging Configuration
```python
import logging
import json
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add custom fields
        log_record['service'] = 'clinical-bert-api'
        log_record['version'] = '1.0.0'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')

        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id

# Configure logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = CustomJsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

#### Log Levels and Usage
```python
# ERROR: System errors requiring immediate attention
logger.error("Model loading failed", extra={
    'error_type': 'ModelLoadError',
    'model_name': 'clinical-assertion-negation-bert',
    'error_details': str(e)
})

# WARN: Potential issues or unusual conditions
logger.warning("High memory usage detected", extra={
    'memory_usage_mb': 850,
    'threshold_mb': 800,
    'service': 'clinical-bert-api'
})

# INFO: Normal operational messages
logger.info("Prediction completed", extra={
    'request_id': 'req-12345-abcde',
    'prediction_time_ms': 245.67,
    'model_label': 'PRESENT',
    'confidence': 0.9914
})

# DEBUG: Detailed debugging information
logger.debug("Model inference details", extra={
    'input_tokens': 45,
    'output_logits': [2.1, -1.5, 0.3],
    'processing_steps': ['tokenization', 'inference', 'postprocessing']
})
```

### Log Aggregation and Analysis

#### Google Cloud Logging Queries
```sql
-- Recent errors
SELECT
  timestamp,
  severity,
  jsonPayload.message,
  jsonPayload.request_id,
  jsonPayload.error_type
FROM `your-project.global._Default._Default`
WHERE resource.type = "cloud_run_revision"
  AND resource.labels.service_name = "clinical-bert-api"
  AND severity >= "ERROR"
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY timestamp DESC

-- Performance analysis
SELECT
  timestamp,
  jsonPayload.request_id,
  jsonPayload.prediction_time_ms,
  jsonPayload.endpoint
FROM `your-project.global._Default._Default`
WHERE resource.type = "cloud_run_revision"
  AND resource.labels.service_name = "clinical-bert-api"
  AND jsonPayload.prediction_time_ms IS NOT NULL
ORDER BY jsonPayload.prediction_time_ms DESC
LIMIT 100

-- Usage patterns
SELECT
  TIMESTAMP_TRUNC(timestamp, HOUR) as hour,
  COUNT(*) as request_count,
  AVG(jsonPayload.prediction_time_ms) as avg_response_time
FROM `your-project.global._Default._Default`
WHERE resource.type = "cloud_run_revision"
  AND resource.labels.service_name = "clinical-bert-api"
  AND jsonPayload.endpoint = "/predict"
GROUP BY hour
ORDER BY hour DESC
LIMIT 24
```

## 🔍 Health Checks

### Application Health Checks

#### Basic Health Check
```python
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

#### Comprehensive Health Check
```python
@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system metrics"""
    try:
        # Model health
        model_healthy = model.is_loaded() if model else False

        # System metrics
        system_metrics = get_system_metrics()

        # Database connectivity (if applicable)
        db_healthy = await check_database_connection()

        # External service dependencies
        external_services = await check_external_services()

        overall_health = all([
            model_healthy,
            system_metrics.get('memory_percent', 0) < 90,
            system_metrics.get('cpu_percent', 0) < 95,
            db_healthy,
            all(external_services.values())
        ])

        return {
            "status": "healthy" if overall_health else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {
                "model": {
                    "healthy": model_healthy,
                    "status": "loaded" if model_healthy else "not loaded"
                },
                "system": {
                    "healthy": system_metrics.get('memory_percent', 0) < 90,
                    "memory_percent": system_metrics.get('memory_percent', 0),
                    "cpu_percent": system_metrics.get('cpu_percent', 0)
                },
                "database": {
                    "healthy": db_healthy,
                    "response_time_ms": db_response_time
                },
                "external_services": external_services
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
```

### Kubernetes Health Checks

#### Readiness Probe
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  successThreshold: 1
  failureThreshold: 3
```

#### Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 30
  timeoutSeconds: 10
  successThreshold: 1
  failureThreshold: 3
```

## 📈 Performance Monitoring

### Application Performance Monitoring (APM)

#### Custom Metrics Implementation
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Model metrics
MODEL_INFERENCE_DURATION = Histogram(
    'model_inference_duration_seconds',
    'Model inference time'
)

MODEL_PREDICTIONS_TOTAL = Counter(
    'model_predictions_total',
    'Total model predictions',
    ['label']
)

# System metrics
MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Current memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'Current CPU usage percentage'
)
```

#### Metrics Collection Middleware
```python
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect HTTP metrics"""
    start_time = time.time()

    # Increment request counter
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status="pending"
    ).inc()

    try:
        response = await call_next(request)

        # Update metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=str(response.status_code)
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(time.time() - start_time)

        return response

    except Exception as e:
        # Handle errors
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status="500"
        ).inc()

        raise
```

### Distributed Tracing

#### OpenTelemetry Integration
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument application
@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    """Middleware to add distributed tracing"""
    with tracer.start_as_span(f"{request.method} {request.url.path}") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.scheme", request.url.scheme)

        try:
            response = await call_next(request)
            span.set_attribute("http.status_code", response.status_code)
            return response
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
```

## 🚨 Incident Response

### Automated Incident Detection

#### Anomaly Detection
```python
import numpy as np
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.data_points = []

    def add_data_point(self, response_time: float, error_rate: float):
        """Add data point for anomaly detection"""
        self.data_points.append([response_time, error_rate])

        # Keep only recent data points
        if len(self.data_points) > 1000:
            self.data_points = self.data_points[-1000:]

        # Retrain model periodically
        if len(self.data_points) % 100 == 0:
            self.model.fit(self.data_points)

    def detect_anomaly(self, response_time: float, error_rate: float) -> bool:
        """Detect if current metrics are anomalous"""
        if len(self.data_points) < 10:
            return False

        prediction = self.model.predict([[response_time, error_rate]])
        return prediction[0] == -1  # -1 indicates anomaly
```

### Runbooks and Procedures

#### Service Restart Procedure
```bash
#!/bin/bash
# restart-service.sh

SERVICE_NAME="clinical-bert-api"
REGION="us-central1"

echo "🔄 Restarting $SERVICE_NAME..."

# Scale down to trigger restart
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --min-instances=0 \
  --max-instances=0

sleep 30

# Scale back up
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --min-instances=1 \
  --max-instances=10

echo "✅ Service restart completed"
```

#### Emergency Rollback Procedure
```bash
#!/bin/bash
# rollback-service.sh

SERVICE_NAME="clinical-bert-api"
REGION="us-central1"
ROLLBACK_REVISION="clinical-bert-api-00008-6gz"

echo "🔄 Rolling back $SERVICE_NAME to $ROLLBACK_REVISION..."

# Update traffic to previous revision
gcloud run services update-traffic $SERVICE_NAME \
  --region=$REGION \
  --to-revisions=$ROLLBACK_REVISION=100

echo "✅ Rollback completed"
```

## 📊 Reporting and Analytics

### Performance Reports

#### Daily Performance Report
```python
def generate_daily_report():
    """Generate daily performance report"""
    # Query metrics from last 24 hours
    metrics = query_prometheus_metrics("24h")

    report = {
        "date": datetime.utcnow().date().isoformat(),
        "summary": {
            "total_requests": metrics.get('total_requests', 0),
            "avg_response_time": metrics.get('avg_response_time', 0),
            "error_rate": metrics.get('error_rate', 0),
            "uptime_percentage": metrics.get('uptime_percentage', 100)
        },
        "performance": {
            "p50_response_time": metrics.get('p50_response_time', 0),
            "p95_response_time": metrics.get('p95_response_time', 0),
            "p99_response_time": metrics.get('p99_response_time', 0),
            "throughput_rps": metrics.get('throughput_rps', 0)
        },
        "errors": {
            "total_errors": metrics.get('total_errors', 0),
            "error_breakdown": metrics.get('error_breakdown', {}),
            "top_error_endpoints": metrics.get('top_error_endpoints', [])
        },
        "resources": {
            "avg_cpu_usage": metrics.get('avg_cpu_usage', 0),
            "avg_memory_usage": metrics.get('avg_memory_usage', 0),
            "peak_memory_usage": metrics.get('peak_memory_usage', 0)
        }
    }

    return report
```

### Business Intelligence Reports

#### Usage Analytics
```python
def generate_usage_report():
    """Generate usage analytics report"""
    # Query usage metrics
    usage_metrics = query_usage_metrics("30d")

    report = {
        "period": "last_30_days",
        "user_analytics": {
            "total_users": usage_metrics.get('total_users', 0),
            "active_users": usage_metrics.get('active_users', 0),
            "new_users": usage_metrics.get('new_users', 0),
            "user_retention": usage_metrics.get('user_retention', 0)
        },
        "api_usage": {
            "total_predictions": usage_metrics.get('total_predictions', 0),
            "predictions_by_type": usage_metrics.get('predictions_by_type', {}),
            "peak_usage_hours": usage_metrics.get('peak_usage_hours', []),
            "geographic_distribution": usage_metrics.get('geographic_distribution', {})
        },
        "performance_trends": {
            "response_time_trend": usage_metrics.get('response_time_trend', []),
            "accuracy_trend": usage_metrics.get('accuracy_trend', []),
            "error_rate_trend": usage_metrics.get('error_rate_trend', [])
        }
    }

    return report
```

---

**📊 Monitor • 🚨 Alert • 📈 Optimize**

*Comprehensive monitoring and observability for Clinical BERT API*
