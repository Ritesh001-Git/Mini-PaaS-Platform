import docker
import git
import os
import shutil
import subprocess
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()

DOCKERHUB_USERNAME = os.getenv("DOCKERHUB_USERNAME")
DOCKERHUB_PASSWORD = os.getenv("DOCKERHUB_PASSWORD")

DEPLOY_BASE = "./deployments"
NGINX_CONF_DIR = "/etc/nginx/conf.d"

def deploy_project(repo_url, container_name, port):
    try:
        path = os.path.join(DEPLOY_BASE, container_name)

        # -----------------------
        # 1️⃣ Clone Repository
        # -----------------------
        if os.path.exists(path):
            shutil.rmtree(path)

        git.Repo.clone_from(repo_url, path)

        # -----------------------
        # 2️⃣ Build Docker Image
        # -----------------------
        image_tag = f"{DOCKERHUB_USERNAME}/{container_name}:latest"

        print(f"Building image {image_tag}...")
        image, logs = client.images.build(
            path=path,
            tag=image_tag,
            rm=True
        )

        # -----------------------
        # 3️⃣ Login to Docker Hub
        # -----------------------
        client.login(
            username=DOCKERHUB_USERNAME,
            password=DOCKERHUB_PASSWORD
        )

        # -----------------------
        # 4️⃣ Push Image
        # -----------------------
        print("Pushing image to Docker Hub...")
        for line in client.images.push(image_tag, stream=True, decode=True):
            print(line)

        # -----------------------
        # 5️⃣ Run Container
        # -----------------------
        print(f"Running container on port {port}...")

        client.containers.run(
            image_tag,
            detach=True,
            name=container_name,
            ports={'8000/tcp': port},
            restart_policy={"Name": "always"}
        )

        # -----------------------
        # 6️⃣ Generate Nginx Config
        # -----------------------
        nginx_conf = f"""
server {{
    listen 80;
    server_name {container_name}.yourdomain.com;

    location / {{
        proxy_pass http://host.docker.internal:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""

        conf_path = os.path.join(NGINX_CONF_DIR, f"{container_name}.conf")

        with open(conf_path, "w") as f:
            f.write(nginx_conf)

        # -----------------------
        # 7️⃣ Reload Nginx
        # -----------------------
        subprocess.run(["docker", "exec", "mini_paas_nginx", "nginx", "-s", "reload"])

        return True

    except Exception as e:
        print(f"Deployment failed: {e}")
        return False