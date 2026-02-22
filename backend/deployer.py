import docker
import git
import os
import shutil

# Initialize Docker client using the socket from docker-compose volume
client = docker.from_env()

def deploy_project(repo_url, container_name, port):
    path = f"./deployments/{container_name}"
    nginx_config_path = f"/etc/nginx/conf.d/{container_name}.conf"

    try:
        # 1. Clone the repository
        if os.path.exists(path):
            shutil.rmtree(path)
        git.Repo.clone_from(repo_url, path)

        # 2. Build the Docker image
        # Uses the Dockerfile located in the cloned repo
        print(f"Building image: {container_name}...")
        image, logs = client.images.build(path=path, tag=container_name, rm=True)

        # 3. Run the container
        # Maps the host port to the container port (defaulting to 8000 based on your Dockerfile)
        print(f"Starting container: {container_name} on port {port}...")
        client.containers.run(
            container_name,
            detach=True,
            name=container_name,
            ports={'8000/tcp': port},
            restart_policy={"Name": "always"}
        )

        # 4. Generate Nginx Config for Reverse Proxy
        # This writes to the volume shared with the Nginx container
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
        with open(nginx_config_path, "w") as f:
            f.write(nginx_conf)

        return True

    except Exception as e:
        print(f"Deployment failed: {e}")
        return False