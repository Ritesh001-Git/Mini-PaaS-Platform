import subprocess

def deploy_project(repo_url, container_name, port):
    subprocess.run(["git", "clone", repo_url, container_name])
    subprocess.run(["docker", "build", "-t", container_name, container_name])
    subprocess.run([
        "docker", "run", "-d",
        "-p", f"{port}:8000",
        "--name", container_name,
        container_name
    ])