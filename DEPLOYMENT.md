# LearnMate – IBM Cloud Deployment Instructions

## Overview

LearnMate can be deployed to IBM Cloud using **Cloud Foundry** (IBM Code Engine or IBM Cloud Foundry runtime).
This guide covers three deployment paths:
1. Local development
2. IBM Cloud Foundry (CF)
3. IBM Code Engine (container-based)

---

## Prerequisites

- IBM Cloud account: https://cloud.ibm.com/registration
- IBM Cloud CLI installed: https://cloud.ibm.com/docs/cli
- Python 3.11+
- Git

---

## 1 · Local Development Setup

```bash
# 1. Clone / download the project
cd learnmate

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your real IBM API key and project ID

# 5. Run the app
python app.py
# App will be available at http://localhost:5000
```

### Demo accounts (pre-seeded)
| Username | Password | Display Name   |
|----------|----------|----------------|
| alice    | Alice@123 | Alice Johnson |
| bob      | Bob@456   | Bob Williams  |

---

## 2 · Get IBM Watsonx.ai Credentials

1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Go to **Catalog → AI / Machine Learning → Watson Machine Learning**
3. Create a WML service instance (Lite tier available)
4. Go to **watsonx.ai Studio**: https://dataplatform.cloud.ibm.com
5. Create a new **Project** and note the **Project ID**
6. Go to **Manage → Access → API Keys** → Create a new API key
7. Copy the key into your `.env` file:

```env
IBM_API_KEY=your-ibm-cloud-api-key
IBM_PROJECT_ID=your-watsonx-project-id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-3-8b-instruct
```

Available Granite models:
- `ibm/granite-3-3-8b-instruct` ← **recommended**
- `ibm/granite-3-2-8b-instruct`
- `ibm/granite-13b-chat-v2`

---

## 3 · Deploy to IBM Cloud Foundry

### Step 1 – Install CF CLI plugin

```bash
ibmcloud plugin install cloud-foundry
ibmcloud login --sso
ibmcloud target --cf
```

### Step 2 – Create manifest.yml

```yaml
applications:
  - name: learnmate
    memory: 512M
    instances: 1
    buildpacks:
      - python_buildpack
    command: gunicorn app:create_app() --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    env:
      SECRET_KEY: <your-secret-key>
      IBM_API_KEY: <your-ibm-api-key>
      IBM_PROJECT_ID: <your-project-id>
      IBM_WATSONX_URL: https://us-south.ml.cloud.ibm.com
      GRANITE_MODEL_ID: ibm/granite-3-3-8b-instruct
```

> **Security Note:** Never commit `manifest.yml` with real secrets. Use IBM Cloud environment variables instead (see Step 3).

### Step 3 – Set environment variables via CLI (recommended)

```bash
# Push without env vars first
ibmcloud cf push learnmate --no-start

# Set secrets securely
ibmcloud cf set-env learnmate SECRET_KEY "your-very-long-random-secret"
ibmcloud cf set-env learnmate IBM_API_KEY "your-ibm-api-key"
ibmcloud cf set-env learnmate IBM_PROJECT_ID "your-project-id"
ibmcloud cf set-env learnmate IBM_WATSONX_URL "https://us-south.ml.cloud.ibm.com"
ibmcloud cf set-env learnmate GRANITE_MODEL_ID "ibm/granite-3-3-8b-instruct"

# Start the app
ibmcloud cf start learnmate
```

### Step 4 – View logs

```bash
ibmcloud cf logs learnmate --recent
ibmcloud cf logs learnmate          # live tail
```

---

## 4 · Deploy to IBM Code Engine (Container)

### Step 1 – Build Docker image

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120"]
```

### Step 2 – Push to IBM Container Registry

```bash
# Login
ibmcloud login --sso
ibmcloud cr login
ibmcloud cr namespace-create learnmate-ns

# Build and push
docker build -t us.icr.io/learnmate-ns/learnmate:latest .
docker push us.icr.io/learnmate-ns/learnmate:latest
```

### Step 3 – Deploy to Code Engine

```bash
ibmcloud ce project create --name learnmate-project
ibmcloud ce project select --name learnmate-project

ibmcloud ce application create \
  --name learnmate \
  --image us.icr.io/learnmate-ns/learnmate:latest \
  --port 8080 \
  --env SECRET_KEY=your-secret \
  --env IBM_API_KEY=your-key \
  --env IBM_PROJECT_ID=your-project-id \
  --env IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com \
  --env GRANITE_MODEL_ID=ibm/granite-3-3-8b-instruct

# Get the URL
ibmcloud ce application get --name learnmate --output url
```

---

## 5 · Database Notes

- **Local / CF**: SQLite (`learnmate.db`) is used by default — fine for demos and development.
- **Production**: Replace SQLite with IBM Db2 or PostgreSQL:
  ```env
  DATABASE_URL=postgresql://user:pass@host:5432/learnmate
  ```
  Install `psycopg2-binary` and add to `requirements.txt`.

---

## 6 · Customise the AI Agent

Open `ai_engine.py` and edit the `AGENT_SYSTEM_PROMPT` string (lines 50–88).

Key customisation areas:
| Section | What to change |
|---------|---------------|
| Personality & Tone | Adjust formality, emoji use, response length |
| Career Guidance | Domain focus (e.g., only cloud/ML roles) |
| Roadmap Generation | Phase count, resource types, project ideas |
| Interview Coaching | Question depth, company-specific tips |
| Safety | Topic restrictions, redirect messages |

---

## 7 · Production Checklist

- [ ] Change `SECRET_KEY` to a 64-character random string
- [ ] Use a real database (PostgreSQL) for production
- [ ] Set `DEBUG=False` (already handled in `gunicorn` mode)
- [ ] Enable HTTPS (CF/Code Engine do this automatically)
- [ ] Set up IBM Cloud monitoring and log alerts
- [ ] Rotate IBM API keys periodically
- [ ] Review and update `AGENT_SYSTEM_PROMPT` for your use case

---

## Support

- IBM Watsonx.ai docs: https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/fm-api.html
- IBM Granite models: https://www.ibm.com/granite
- Flask docs: https://flask.palletsprojects.com
- IBM Cloud CLI: https://cloud.ibm.com/docs/cli
