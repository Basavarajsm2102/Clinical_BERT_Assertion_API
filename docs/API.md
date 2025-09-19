# Clinical BERT Assertion API - Complete API Documentation

## 📋 Overview

The Clinical BERT Assertion API provides real-time clinical text classification capabilities using state-of-the-art transformer models. The API analyzes clinical sentences and categorizes medical assertions as **PRESENT**, **ABSENT**, or **POSSIBLE**.

### Base URLs
- **Production**: `https://your-service-url`
- **Staging**: `https://staging-your-service-url`
- **Development**: `http://localhost:8000`

### Authentication
All API endpoints support optional authentication via API keys:
```bash
# Include in request headers
Authorization: Bearer YOUR_API_KEY
```

---

## 🔍 Core Endpoints

### Health Check Endpoint

#### GET /health
Returns comprehensive service health information including model status, system metrics, and uptime.

**Request:**
```bash
curl -X GET https://your-service-url/health \
  -H "Content-Type: application/json"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": 1642857600.123,
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 3600.5,
  "total_predictions": 1250,
  "system_metrics": {
    "memory_mb": 730.6,
    "memory_percent": 87.7,
    "cpu_percent": 12.3,
    "disk_percent": 45.2
  },
  "model_info": {
    "model_name": "bvanaken/clinical-assertion-negation-bert",
    "device": "cpu",
    "loaded": true,
    "labels": ["PRESENT", "ABSENT", "POSSIBLE"]
  }
}
```

**Response Fields:**
- `status`: Service health status ("healthy" or "unhealthy")
- `model_loaded`: Whether ML model is loaded and ready
- `timestamp`: Unix timestamp of health check
- `version`: API version
- `environment`: Deployment environment
- `uptime_seconds`: Service uptime in seconds
- `total_predictions`: Total predictions made since startup
- `system_metrics`: System resource utilization
- `model_info`: ML model details and status

---

### Single Prediction Endpoint

#### POST /predict
Analyzes a single clinical sentence and returns assertion classification.

**Request:**
```bash
curl -X POST https://your-service-url/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "sentence": "The patient reports chest pain."
  }'
```

**Request Body:**
```json
{
  "sentence": "string (required, max 512 tokens)"
}
```

**Response (200 OK):**
```json
{
  "label": "PRESENT",
  "score": 0.9914,
  "model_label": "PRESENT",
  "prediction_time_ms": 245.67,
  "request_id": "req-12345-abcde"
}
```

**Response Fields:**
- `label`: Final classification ("PRESENT", "ABSENT", "POSSIBLE")
- `score`: Confidence score (0.0 to 1.0)
- `model_label`: Raw model prediction
- `prediction_time_ms`: Processing time in milliseconds
- `request_id`: Unique request identifier for tracing

**Error Responses:**

**400 Bad Request - Invalid Input:**
```json
{
  "error": "ValidationError",
  "message": "Input validation failed",
  "details": {
    "sentence": "Field required"
  },
  "request_id": "req-12345-error"
}
```

**429 Too Many Requests - Rate Limited:**
```json
{
  "error": "RateLimitError",
  "message": "Rate limit exceeded",
  "retry_after": 60,
  "request_id": "req-12345-rate"
}
```

**500 Internal Server Error:**
```json
{
  "error": "InternalError",
  "message": "Model inference failed",
  "request_id": "req-12345-500"
}
```

---

### Batch Prediction Endpoint

#### POST /predict/batch
Analyzes multiple clinical sentences in a single request for improved efficiency.

**Request:**
```bash
curl -X POST https://your-service-url/predict/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "sentences": [
      "The patient reports chest pain.",
      "No signs of pneumonia were observed.",
      "He has a history of hypertension."
    ]
  }'
```

**Request Body:**
```json
{
  "sentences": [
    "string (required, 1-100 sentences, max 512 tokens each)"
  ]
}
```

**Response (200 OK):**
```json
{
  "predictions": [
    {
      "label": "PRESENT",
      "score": 0.9914,
      "model_label": "PRESENT",
      "prediction_time_ms": 89.23,
      "request_id": "batch-12345-abcde"
    },
    {
      "label": "ABSENT",
      "score": 0.9654,
      "model_label": "ABSENT",
      "prediction_time_ms": 87.45,
      "request_id": "batch-12345-abcde"
    },
    {
      "label": "PRESENT",
      "score": 0.9953,
      "model_label": "PRESENT",
      "prediction_time_ms": 91.12,
      "request_id": "batch-12345-abcde"
    }
  ],
  "batch_size": 3,
  "total_prediction_time_ms": 267.8,
  "request_id": "batch-12345-abcde"
}
```

**Batch Processing Notes:**
- **Maximum batch size**: 100 sentences
- **Processing**: All sentences processed in parallel
- **Efficiency**: ~3x faster than individual requests
- **Memory**: Optimized for large batches
- **Error handling**: Individual sentence failures don't affect batch

---

### Model Information Endpoint

#### GET /model/info
Returns detailed information about the loaded ML model and its capabilities.

**Request:**
```bash
curl -X GET https://your-service-url/model/info \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response (200 OK):**
```json
{
  "model_name": "bvanaken/clinical-assertion-negation-bert",
  "device": "cpu",
  "loaded": true,
  "labels": ["PRESENT", "ABSENT", "POSSIBLE"],
  "max_sequence_length": 512,
  "model_size_mb": 420.5,
  "tokenizer_type": "BERT",
  "framework": "transformers",
  "version": "1.0.0"
}
```

---

## 📊 Monitoring Endpoints

### Prometheus Metrics

#### GET /metrics
Returns comprehensive metrics in Prometheus format for monitoring and alerting.

**Request:**
```bash
curl -X GET https://your-service-url/metrics
```

**Sample Output:**
```prometheus
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/predict",status="200"} 1250

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="POST",endpoint="/predict",le="0.1"} 850
http_request_duration_seconds_bucket{method="POST",endpoint="/predict",le="0.5"} 1200
http_request_duration_seconds_bucket{method="POST",endpoint="/predict",le="+Inf"} 1250

# HELP model_predictions_total Total model predictions
# TYPE model_predictions_total counter
model_predictions_total{label="PRESENT"} 650
model_predictions_total{label="ABSENT"} 450
model_predictions_total{label="POSSIBLE"} 150
```

**Available Metrics:**
- **Request metrics**: Count, duration, error rates by endpoint
- **Model metrics**: Prediction counts, inference times, accuracy
- **System metrics**: CPU, memory, disk usage
- **Business metrics**: Usage patterns, client distribution

---

## 🔧 API Specifications

### Request/Response Format

#### Content Types
- **Request**: `application/json`
- **Response**: `application/json`
- **Encoding**: UTF-8

#### Rate Limiting
- **Default limit**: 100 requests per minute per client
- **Headers**: Include rate limit information in responses
- **Backoff**: Exponential backoff recommended

#### Timeouts
- **Request timeout**: 30 seconds
- **Connection timeout**: 10 seconds
- **Read timeout**: 30 seconds

### Error Handling

#### HTTP Status Codes
- **200 OK**: Successful request
- **400 Bad Request**: Invalid input parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Endpoint doesn't exist
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

#### Error Response Format
```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "field": "specific field error",
    "constraint": "validation constraint"
  },
  "request_id": "unique-request-identifier",
  "timestamp": 1642857600.123
}
```

---

## 🧪 Testing & Validation

### Test Data Examples

#### Clinical Assertion Examples

**PRESENT Assertions:**
- "The patient reports chest pain."
- "He has a history of hypertension."
- "Blood pressure is elevated at 160/95."
- "Patient exhibits signs of pneumonia."

**ABSENT Assertions:**
- "The patient denies chest pain."
- "No signs of pneumonia were observed."
- "Patient reports no history of diabetes."
- "Blood pressure within normal limits."

**POSSIBLE Assertions:**
- "If symptoms persist, call doctor."
- "Patient may have pneumonia."
- "Suspected cardiac arrhythmia."
- "Possible medication interaction."

### Validation Rules

#### Input Validation
- **Sentence length**: 1-512 tokens
- **Content type**: Plain text only
- **Encoding**: UTF-8
- **Special characters**: Limited sanitization applied

#### Output Validation
- **Label format**: One of ["PRESENT", "ABSENT", "POSSIBLE"]
- **Score range**: 0.0 to 1.0
- **Response time**: <500ms for single predictions
- **Request ID**: UUID format

---

## 🔒 Security Considerations

### Authentication Methods
1. **API Key Authentication** (recommended for production)
2. **OAuth 2.0** (for enterprise integrations)
3. **JWT Tokens** (for stateless authentication)

### Data Protection
- **Input sanitization**: Automatic cleaning of clinical text
- **Output filtering**: Sensitive information masking
- **Audit logging**: All requests logged with correlation IDs
- **Rate limiting**: Protection against abuse

### Compliance
- **HIPAA**: Protected health information handling
- **GDPR**: Data protection and privacy
- **SOC 2**: Security and availability controls

---

## 📈 Usage Guidelines

### Best Practices

#### Request Optimization
- Use batch predictions for multiple sentences
- Implement client-side caching for repeated queries
- Respect rate limits and implement backoff strategies
- Monitor response times and adjust timeouts accordingly

#### Error Handling
- Implement comprehensive error handling
- Use request IDs for debugging and support
- Log errors with appropriate detail levels
- Implement retry logic with exponential backoff

#### Monitoring Integration
- Monitor API usage and performance metrics
- Set up alerts for error rates and response times
- Track business metrics and usage patterns
- Implement logging and tracing for debugging

### Performance Tips

#### Client-Side Optimization
- **Connection pooling**: Reuse HTTP connections
- **Compression**: Enable gzip compression
- **Async processing**: Use async/await for concurrent requests
- **Load balancing**: Distribute requests across multiple instances

#### Server-Side Optimization
- **Caching**: Implement response caching for frequent queries
- **Batch processing**: Use batch endpoints for efficiency
- **Resource allocation**: Monitor and adjust instance sizing
- **Auto-scaling**: Configure appropriate scaling policies

---

## 🔗 Integration Examples

### Python Integration
```python
import requests
from typing import List, Dict, Any

class ClinicalBERTClient:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })

    def predict(self, sentence: str) -> Dict[str, Any]:
        """Single sentence prediction"""
        response = self.session.post(
            f"{self.base_url}/predict",
            json={"sentence": sentence}
        )
        response.raise_for_status()
        return response.json()

    def predict_batch(self, sentences: List[str]) -> Dict[str, Any]:
        """Batch prediction"""
        response = self.session.post(
            f"{self.base_url}/predict/batch",
            json={"sentences": sentences}
        )
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

# Usage example
client = ClinicalBERTClient("https://your-service-url", "your-api-key")
result = client.predict("The patient reports chest pain.")
print(f"Prediction: {result['label']} (confidence: {result['score']:.4f})")
```

### JavaScript/Node.js Integration
```javascript
const axios = require('axios');

class ClinicalBERTClient {
    constructor(baseURL, apiKey = null) {
        this.client = axios.create({
            baseURL,
            headers: apiKey ? {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            } : {
                'Content-Type': 'application/json'
            }
        });
    }

    async predict(sentence) {
        const response = await this.client.post('/predict', { sentence });
        return response.data;
    }

    async predictBatch(sentences) {
        const response = await this.client.post('/predict/batch', { sentences });
        return response.data;
    }

    async healthCheck() {
        const response = await this.client.get('/health');
        return response.data;
    }
}

// Usage example
const client = new ClinicalBERTClient('https://your-service-url', 'your-api-key');
client.predict('The patient reports chest pain.')
    .then(result => {
        console.log(`Prediction: ${result.label} (confidence: ${result.score.toFixed(4)})`);
    })
    .catch(error => {
        console.error('API Error:', error.response.data);
    });
```

---

## 📞 Support & Troubleshooting

### Getting Help
- **API Issues**: Check health endpoint first
- **Rate Limiting**: Monitor usage and implement backoff
- **Timeouts**: Adjust client timeout settings
- **Errors**: Use request IDs for support tickets

### Common Issues
- **Model Loading**: Check `/health` endpoint
- **Rate Limits**: Implement exponential backoff
- **Network Issues**: Verify connectivity and DNS
- **Authentication**: Validate API key configuration

### Support Channels
- **Documentation**: This comprehensive API guide
- **GitHub Issues**: Bug reports and feature requests
- **Email Support**: enterprise-support@yourcompany.com
- **Response SLA**: <4 hours for production issues

---

**⚕️ Clinical AI • 🚀 Production Ready • 🔒 Enterprise Secure**

*Complete API documentation for healthcare AI integration*
