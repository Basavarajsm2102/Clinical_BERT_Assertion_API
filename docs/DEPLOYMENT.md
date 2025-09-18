# Deployment Guide

## Local Development
```bash
uvicorn app.main:app --reload
```

## Docker Deployment  
```bash
docker build -t clinical-bert-api .
docker run -p 8000:8000 clinical-bert-api
```

## Google Cloud Run
```bash
./deploy.sh production
```
