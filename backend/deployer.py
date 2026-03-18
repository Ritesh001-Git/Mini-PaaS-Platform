import docker
import git
import os
import shutil
import socket
from dotenv import load_dotenv

load_dotenv()

client = docker.from_env()

DOCKERHUB_USERNAME = os.getenv("DOCKERHUB_USERNAME")
DOCKERHUB_PASSWORD = os.getenv("DOCKERHUB_PASSWORD")

DEPLOY_BASE = "./deployments"
NGINX_CONF_DIR = "/etc/nginx/conf.d"


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def deploy_project(repo_url, container_name, port):

    try:

        if port_in_use(port):
            raise Exception(f"Port {port} already in use")

        path = os.path.join(DEPLOY_BASE, container_name)

        # 1️⃣ Clone repo
        if os.path.exists(path):
            shutil.rmtree(path)

        git.Repo.clone_from(repo_url, path)

        # 2️⃣ Check Dockerfile
        dockerfile_path = os.path.join(path, "Dockerfile")
        if not os.path.exists(dockerfile_path):
            raise Exception("No Dockerfile found")

        # 3️⃣ Build image
        image_tag = f"{DOCKERHUB_USERNAME}/{container_name}:latest"

        print(f"Building {image_tag}")
        client.images.build(path=path, tag=image_tag, rm=True)

        # 4️⃣ Login
        client.login(
            username=DOCKERHUB_USERNAME,
            password=DOCKERHUB_PASSWORD
        )

        # 5️⃣ Push
        for line in client.images.push(image_tag, stream=True, decode=True):
            print(line)

        # 6️⃣ Remove old container
        try:
            old = client.containers.get(container_name)
            old.stop()
            old.remove()
        except:
            pass

        # 7️⃣ Run container
        print(f"Running {container_name}")

        container = client.containers.run(
            image_tag,
            detach=True,
            name=container_name,
            network="mini-paas-platform_default",   # 🔥 REQUIRED
            ports={'8000/tcp': port},               # 🔥 KEEP THIS
            restart_policy={"Name": "always"}
        )

        # 8️⃣ Generate nginx config
        nginx_conf = f"""
server {{
    listen 80;

    location /{container_name}/ {{
        proxy_pass http://{container_name}:8000/;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""

        conf_path = os.path.join(NGINX_CONF_DIR, f"{container_name}.conf")

        # remove old config if exists
        if os.path.exists(conf_path):
            os.remove(conf_path)

        with open(conf_path, "w") as f:
            f.write(nginx_conf)

        # 9️⃣ Reload nginx
        nginx = client.containers.get("mini_paas_nginx")
        nginx.exec_run("nginx -s reload")

        return {
            "docker_id": container.id,
            "image": image_tag,
            "url": f"/{container_name}/"
        }

    except Exception as e:
        print("Deployment failed:", e)
        return {"error": str(e)}