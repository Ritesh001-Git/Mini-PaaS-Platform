@app.post("/deploy")
def deploy(data: DeployRequest):
    deploy_project(data.repo_url, data.name, data.port)
    return {"message": "Deployment started"}