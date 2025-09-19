# Clinical BERT API - Development Guide

## 🛠️ Development Environment Setup

### Prerequisites
- **Python**: 3.12.0 or higher
- **Git**: Latest version
- **Docker**: Optional, for containerized development
- **Virtual Environment**: venv, conda, or virtualenv

### Quick Start Development
```bash
# 1. Clone the repository
git clone https://github.com/Basavarajsm2102/Clinical_BERT_Assertion_API.git
cd Clinical_BERT_Assertion_API

# 2. Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install development dependencies
pip install -r requirements-dev.txt

# 5. Set up pre-commit hooks
pip install pre-commit
pre-commit install

# 6. Configure environment variables
cp .env.example .env
# Edit .env with your development settings

# 7. Start development server
uvicorn app.main:app --reload --port 8000 --log-level debug

# 8. Access API documentation
open http://localhost:8000/docs
```

### Development Dependencies
```txt
# requirements-dev.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.10.1
isort==5.12.0
flake8==6.1.0
mypy==1.7.0
bandit==1.7.5
safety==2.3.4
pre-commit==3.5.0
python-json-logger==2.0.7
```

## 🧪 Testing Strategy

### Test Categories

#### Unit Tests
```python
# tests/test_model.py
import pytest
from app.model import ClinicalAssertionModel

class TestClinicalAssertionModel:
    def test_model_initialization(self):
        """Test model initialization"""
        model = ClinicalAssertionModel()
        assert model is not None

    def test_model_loading(self):
        """Test model loading"""
        model = ClinicalAssertionModel()
        assert model.is_loaded() == False

        # Test async loading
        import asyncio
        asyncio.run(model.load_model())
        assert model.is_loaded() == True

    def test_prediction_validation(self):
        """Test prediction input validation"""
        model = ClinicalAssertionModel()

        # Test empty input
        with pytest.raises(ValueError):
            model.predict("")

        # Test long input
        long_text = "word " * 1000
        with pytest.raises(ValueError):
            model.predict(long_text)
```

#### Integration Tests
```python
# tests/test_api_integration.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
class TestAPIIntegration:
    @pytest.fixture
    async def client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            yield client

    async def test_health_endpoint(self, client):
        """Test health endpoint integration"""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "timestamp" in data

    async def test_prediction_workflow(self, client):
        """Test complete prediction workflow"""
        # Test single prediction
        payload = {"sentence": "The patient reports chest pain."}
        response = await client.post("/predict", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert "label" in data
        assert "score" in data
        assert "prediction_time_ms" in data
        assert data["label"] in ["PRESENT", "ABSENT", "POSSIBLE"]
        assert 0.0 <= data["score"] <= 1.0

    async def test_batch_prediction_workflow(self, client):
        """Test batch prediction workflow"""
        payload = {
            "sentences": [
                "Patient has fever.",
                "No signs of infection.",
                "Blood pressure elevated."
            ]
        }
        response = await client.post("/predict/batch", json=payload)

        assert response.status_code == 200
        data = response.json()

        assert "predictions" in data
        assert "batch_size" in data
        assert len(data["predictions"]) == 3
        assert data["batch_size"] == 3
```

#### Performance Tests
```python
# tests/test_performance.py
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import requests

class TestPerformance:
    def test_single_prediction_performance(self):
        """Test single prediction performance"""
        payload = {"sentence": "The patient reports chest pain."}

        start_time = time.time()
        response = requests.post("http://localhost:8000/predict", json=payload)
        end_time = time.time()

        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000  # Convert to ms

        # Assert performance requirements
        assert response_time < 500  # Less than 500ms
        print(f"Response time: {response_time:.2f}ms")

    def test_concurrent_predictions(self):
        """Test concurrent prediction handling"""
        payload = {"sentence": "Patient has symptoms."}

        def make_request():
            return requests.post("http://localhost:8000/predict", json=payload)

        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]

        # All requests should succeed
        assert all(response.status_code == 200 for response in responses)

        # Calculate average response time
        response_times = []
        for response in responses:
            # Extract response time from custom header or calculate
            response_times.append(response.elapsed.total_seconds() * 1000)

        avg_response_time = sum(response_times) / len(response_times)
        print(f"Average response time: {avg_response_time:.2f}ms")

        # Assert performance under concurrent load
        assert avg_response_time < 1000  # Less than 1 second average

    @pytest.mark.asyncio
    async def test_batch_processing_efficiency(self):
        """Test batch processing efficiency"""
        sentences = [
            "Patient reports pain.",
            "No abnormal findings.",
            "Vital signs stable.",
            "Laboratory results normal.",
            "Physical examination unremarkable."
        ] * 10  # 50 sentences total

        payload = {"sentences": sentences}

        start_time = time.time()
        response = requests.post("http://localhost:8000/predict/batch", json=payload)
        end_time = time.time()

        assert response.status_code == 200
        data = response.json()

        batch_time = (end_time - start_time) * 1000
        per_item_time = batch_time / len(sentences)

        print(f"Batch time: {batch_time:.2f}ms")
        print(f"Per item time: {per_item_time:.2f}ms")

        # Assert batch efficiency
        assert per_item_time < 100  # Less than 100ms per item
        assert len(data["predictions"]) == len(sentences)
```

### Running Tests

#### Basic Test Execution
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py

# Run specific test class
pytest tests/test_api.py::TestHealthEndpoint

# Run specific test method
pytest tests/test_api.py::TestHealthEndpoint::test_health_check_success
```

#### Test Coverage
```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term

# View coverage report in browser
open htmlcov/index.html

# Coverage thresholds
pytest --cov=app --cov-report=term --cov-fail-under=75
```

#### Test Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --tb=short
    --cov=app
    --cov-report=html
    --cov-report=term
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
```

## 🔧 Code Quality Tools

### Black - Code Formatting
```bash
# Format all Python files
black .

# Check formatting without changes
black --check .

# Format specific files
black app/main.py app/model.py
```

### isort - Import Sorting
```bash
# Sort imports in all files
isort .

# Check import sorting
isort --check-only .

# Sort imports with specific profile
isort --profile black .
```

### flake8 - Linting
```bash
# Lint all Python files
flake8 .

# Lint specific files
flake8 app/main.py

# Show statistics
flake8 --statistics
```

### mypy - Type Checking
```bash
# Type check all files
mypy .

# Type check specific module
mypy app/model.py

# Generate type checking report
mypy --html-report mypy-report .
```

### bandit - Security Scanning
```bash
# Scan for security issues
bandit -r app/

# Scan with specific severity
bandit -r app/ -l high

# Generate HTML report
bandit -r app/ -f html -o security-report.html
```

### safety - Dependency Vulnerability Scanning
```bash
# Check for known vulnerabilities
safety check

# Check specific requirements file
safety check -r requirements.txt

# Generate detailed report
safety check --full-report
```

## 🔄 Development Workflow

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes with tests
# ... development work ...

# Run quality checks
make quality

# Run tests
make test

# Commit changes
git add .
git commit -m "feat: add new feature

- Add feature description
- Update tests
- Update documentation"

# Push branch
git push origin feature/new-feature

# Create pull request
# ... GitHub PR process ...
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203,W503"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Makefile Commands
```makefile
# Makefile
.PHONY: help install test quality clean

help:
    @echo "Available commands:"
    @echo "  install     Install dependencies"
    @echo "  test        Run test suite"
    @echo "  quality     Run quality checks"
    @echo "  clean       Clean up generated files"

install:
    pip install -r requirements.txt
    pip install -r requirements-dev.txt

test:
    pytest --cov=app --cov-report=html --cov-report=term

quality:
    black --check .
    isort --check-only .
    flake8 .
    mypy .
    bandit -r app/
    safety check

clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    rm -rf .coverage htmlcov .mypy_cache .pytest_cache
```

## 🐛 Debugging Techniques

### Local Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints
def debug_prediction(sentence: str):
    print(f"Input sentence: {sentence}")
    print(f"Sentence length: {len(sentence)}")

    # ... prediction logic ...

    print(f"Model output: {result}")
    return result
```

### Remote Debugging
```python
# Enable remote debugging with debugpy
import debugpy

# Allow other computers to attach
debugpy.listen(("0.0.0.0", 5678))
print("Debugger listening on port 5678")

# Wait for debugger to attach
debugpy.wait_for_client()

# Your code here
# ...
```

### Performance Profiling
```python
import cProfile
import pstats
from io import StringIO

def profile_function():
    pr = cProfile.Profile()
    pr.enable()

    # Code to profile
    result = make_prediction("Test sentence")

    pr.disable()
    s = StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())

    return result
```

### Memory Profiling
```python
from memory_profiler import profile

@profile
def memory_intensive_prediction():
    # This function will be profiled for memory usage
    sentences = ["Long sentence " * 100] * 50
    results = []

    for sentence in sentences:
        result = predict_single(sentence)
        results.append(result)

    return results

if __name__ == "__main__":
    memory_intensive_prediction()
```

## 📊 Development Metrics

### Code Quality Metrics
```python
# Calculate code quality metrics
import radon.complexity as cc
import radon.metrics as mt

def analyze_code_quality(file_path: str):
    """Analyze code quality metrics"""

    # Cyclomatic complexity
    complexity = cc.cc_visit(file_path)
    avg_complexity = sum(c.complexity for c in complexity) / len(complexity)

    # Maintainability index
    mi = mt.mi_visit(file_path, multi=True)

    return {
        "complexity": avg_complexity,
        "maintainability_index": mi,
        "lines_of_code": sum(1 for _ in open(file_path)),
    }
```

### Test Coverage Analysis
```python
# Analyze test coverage gaps
import coverage
import os

def analyze_coverage_gaps():
    """Analyze areas with insufficient test coverage"""

    cov = coverage.Coverage()
    cov.load()

    # Get coverage data
    covered_lines = cov.get_covered_lines()
    missing_lines = cov.get_missing_lines()

    # Analyze by module
    for module in covered_lines:
        covered = len(covered_lines[module])
        missing = len(missing_lines.get(module, []))

        if covered + missing > 0:
            coverage_pct = covered / (covered + missing) * 100
            print(f"{module}: {coverage_pct:.1f}% coverage")

            if coverage_pct < 80:
                print(f"  Low coverage areas: {missing_lines[module][:5]}...")
```

## 🚀 Deployment for Development

### Local Docker Development
```bash
# Build development image
docker build -t clinical-bert-dev -f Dockerfile.dev .

# Run with hot reload
docker run -p 8000:8000 -v $(pwd):/app clinical-bert-dev

# Run with debugging
docker run -p 8000:8000 -p 5678:5678 \
  -v $(pwd):/app \
  -e DEBUG=true \
  clinical-bert-dev
```

### Development Environment Variables
```bash
# .env.development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true

# Model settings
MODEL_CACHE_DIR=./model_cache
MAX_SEQUENCE_LENGTH=512

# API settings
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Development features
AUTO_RELOAD=true
ENABLE_DOCS=true
ENABLE_DEBUG=true

# Optional: Authentication (development only)
API_KEY=dev-api-key-12345
REQUIRE_API_KEY=false
```

## 📚 Learning Resources

### Recommended Reading
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Hugging Face Transformers**: https://huggingface.co/docs/transformers/
- **Python Testing**: https://docs.python.org/3/library/unittest.html
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/

### Online Courses
- **FastAPI Course**: Build APIs with Python
- **ML Engineering**: Production ML systems
- **DevOps for Developers**: CI/CD pipelines
- **Security Best Practices**: Application security

### Community Resources
- **FastAPI Discord**: Real-time help and discussions
- **Hugging Face Forums**: ML model discussions
- **Stack Overflow**: Programming Q&A
- **GitHub Issues**: Bug reports and feature requests

---

**🛠️ Develop • 🧪 Test • 🚀 Deploy**

*Comprehensive development guide for Clinical BERT API*
