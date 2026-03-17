import docker
import git
import os
import shutil
import subprocess
import socket
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()

DOCKERHUB_USERNAME = os.getenv("DOCKERHUB_USERNAME")
DOCKERHUB_PASSWORD = os.getenv("DOCKERHUB_PASSWORD")

DEPLOY_BASE = "./deployments"
NGINX_CONF_DIR = "/etc/nginx/conf.d"


# -------------------------
# Check if port is free
# -------------------------
def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


# -------------------------
# Main Deployment Function
# -------------------------
def deploy_project(repo_url, container_name, port):

    try:

        if port_in_use(port):
            raise Exception(f"Port {port} already in use")

        path = os.path.join(DEPLOY_BASE, container_name)

        # -------------------------
        # 1️⃣ Clone Repository
        # -------------------------
        if os.path.exists(path):
            shutil.rmtree(path)

        git.Repo.clone_from(repo_url, path)

        # -------------------------
        # 2️⃣ Check Dockerfile
        # -------------------------
        dockerfile_path = os.path.join(path, "Dockerfile")

        if not os.path.exists(dockerfile_path):
            raise Exception("Repository does not contain a Dockerfile")

        # -------------------------
        # 3️⃣ Build Docker Image
        # -------------------------
        image_tag = f"{DOCKERHUB_USERNAME}/{container_name}:latest"

        print(f"Building image {image_tag}")

        image, logs = client.images.build(
            path=path,
            tag=image_tag,
            rm=True
        )

        # -------------------------
        # 4️⃣ Login to Docker Hub
        # -------------------------
        client.login(
            username=DOCKERHUB_USERNAME,
            password=DOCKERHUB_PASSWORD
        )

        # -------------------------
        # 5️⃣ Push Image
        # -------------------------
        print("Pushing image to Docker Hub")

        for line in client.images.push(image_tag, stream=True, decode=True):
            print(line)

        # -------------------------
        # 6️⃣ Remove Old Container
        # -------------------------
        try:
            old_container = client.containers.get(container_name)
            old_container.stop()
            old_container.remove()
        except:
            pass

        # -------------------------
        # 7️⃣ Run Container
        # -------------------------
        print(f"Running container {container_name} on port {port}")

        container = client.containers.run(
            image_tag,
            detach=True,
            name=container_name,
            ports={'8000/tcp': port},
            restart_policy={"Name": "always"}
        )

        docker_id = container.id

        # -------------------------
        # 8️⃣ Generate Nginx Config
        # -------------------------
        nginx_conf = f"""
server {{
    listen 80;
    server_name {container_name}.localhost;

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

        # -------------------------
        # 9️⃣ Reload Nginx
        # -------------------------
        container = client.containers.get("mini_paas_nginx")
        container.exec_run("nginx -s reload")

        # -------------------------
        # 🔟 Return Deployment Info
        # -------------------------
        run_command = f"docker run -p {port}:8000 {image_tag}"

        return {
            "docker_id": docker_id,
            "image": image_tag,
            "run_command": run_command
        }

    except Exception as e:

        print("Deployment failed:", e)

        return {
            "error": str(e)
        }