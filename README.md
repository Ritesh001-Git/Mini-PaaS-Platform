# 🚀 CloudOps Mini-PaaS Platform

A lightweight **Platform-as-a-Service (PaaS)** built with **Python, Docker, Nginx, PostgreSQL, and AWS EC2** that allows users to deploy GitHub repositories as containerized applications automatically.

The platform clones a repository, builds a Docker image, deploys the container, configures Nginx reverse proxy, and tracks deployments in a database.

This project demonstrates real-world DevOps practices such as container orchestration, infrastructure automation, reverse proxy management, deployment pipelines, and backend API development using Python with FastAPI.

---

# 📌 Features

## Automated Deployment

* Deploy any GitHub repository with a **Dockerfile**
* Automatic **Git clone → Docker build → Container run**

## Container Orchestration

* Each project runs in an isolated Docker container
* Automatic container restart policies

## Reverse Proxy with Nginx

* Dynamic Nginx configuration generation
* Route traffic from domain/subdomain to deployed containers

## Database Tracking

* PostgreSQL stores:

  * Repository URL
  * Container name
  * Port
  * Deployment status

## Background Deployment

* Deployments run asynchronously using **FastAPI background tasks**
* API remains responsive during builds

## REST API

* Deploy applications via API
* Retrieve deployed project details

---

# 🏗️ Architecture

```
User → Web UI → FastAPI Backend → Deployment Engine
                                      │
                                      │
                                      ▼
                               GitHub Repository
                                      │
                                      ▼
                                Docker Build
                                      │
                                      ▼
                               Docker Container
                                      │
                                      ▼
                               Nginx Reverse Proxy
                                      │
                                      ▼
                                Public Access
```

---

# 🧰 Tech Stack

### Backend

* FastAPI
* SQLAlchemy
* Python

### Infrastructure

* Docker
* Docker Compose
* Nginx

### Database

* PostgreSQL

### Cloud

* AWS EC2 (Free Tier compatible)

### DevOps Tools

* Git
* Docker Engine API
* Reverse Proxy Automation

---

# 📂 Project Structure

```
Mini-PaaS-Platform
│
├── backend
│   ├── main.py
│   ├── deployer.py
│   ├── database.py
│   ├── models.py
│   └── templates
│       └── index.html
│
├── nginx
│   └── conf.d
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
```

---

# ⚙️ How Deployment Works

1️⃣ User submits a **GitHub repository URL**
2️⃣ Backend validates request and saves project in database
3️⃣ Repository is cloned to the server

```
git clone <repo_url>
```

4️⃣ Docker builds an image using the repository Dockerfile

```
docker build -t <container_name>
```

5️⃣ Container is started and mapped to a port

```
docker run -p <port>:8000 <container_name>
```

6️⃣ Nginx configuration is generated automatically

7️⃣ Nginx reloads and routes traffic to the new container

---

# 🚀 Running the Platform

## 1️⃣ Clone the Repository

```
git clone https://github.com/yourusername/Mini-PaaS-Platform.git
cd Mini-PaaS-Platform
```

---

## 2️⃣ Configure Environment Variables

Create a `.env` file in the root directory.

```
DOCKERHUB_USERNAME=your_dockerhub_username
DOCKERHUB_PASSWORD=your_dockerhub_access_token
```

---

## 3️⃣ Start the Platform

```
docker-compose up -d --build
```

---

## 4️⃣ Access the Platform

```
http://YOUR_SERVER_IP
```

API documentation:

```
http://YOUR_SERVER_IP/docs
```

---

# 🧪 Example Deployment Request

POST request to `/deploy`

```
{
  "repo_url": "https://github.com/user/sample-app",
  "name": "myapp",
  "port": 9001
}
```

Response:

```
{
  "project_id": 1,
  "status": "Deployment started"
}
```

---

# 📊 Project Status Tracking

Each deployment has a status stored in PostgreSQL:

* `PENDING`
* `DEPLOYING`
* `RUNNING`
* `FAILED`
* `ERROR`

This allows monitoring of deployment progress.

---

# ⚠️ Requirements for Deploying Apps

Repositories deployed to this platform must contain:

* A valid **Dockerfile**
* Application exposed on **port 8000**

Example Dockerfile:

```
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

---

# 🔐 Planned Improvements

Upcoming enhancements:

* User authentication (JWT)
* Multi-user project isolation
* Auto port allocation
* Container logs viewer
* GitHub Actions CI/CD integration
* HTTPS support with Let's Encrypt
* Subdomain-based routing
* Deployment monitoring dashboard

---

# 💡 Learning Objectives

This project demonstrates practical knowledge of:

* Docker container lifecycle
* Reverse proxy automation
* Infrastructure automation
* Cloud deployment
* API-driven DevOps workflows

---

# 📜 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

Developed by **Ritesh Kumar Swain**

DevOps | Cloud | Backend Engineering
