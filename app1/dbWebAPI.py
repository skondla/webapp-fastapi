#!/usr/bin/env python
#Author: skondla@me.com
#purpose: Build a simple python WebApp & REST API with FastAPI to call database service requests
#coding=utf-8
#Run: uvicorn dbWebAPI:app --reload --host 0.0.0.0 --port 8000 --reload --ssl-keyfile=cert/key.pem --ssl-certfile=cert/certificate.pem
#Run: uvicorn dbWebAPI:app --reload --host localhost --port 25443 --reload --ssl-keyfile=cert/key.pem --ssl-certfile=cert/certificate.pem

from fastapi import FastAPI, Form, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
# from fastapi.templating import Jinja2Templates
from starlette.templating import Jinja2Templates  # ✅ Correct
from lib.rdsAdmin import RDSDescribe, RDSCreate, RDSDelete
import datetime
import yaml
import ssl
import uvicorn

# Define constants
SNAPSHOT = "snapshot"
CLUSTER = "cluster"

# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def my_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/backup", response_class=HTMLResponse)
async def my_form(request: Request):
    return templates.TemplateResponse("db-backup-tool.html", {"request": request})

@app.get("/backup/create", response_class=HTMLResponse)
async def backup_create(request: Request):
    return templates.TemplateResponse("create-backup.html", {"request": request})

@app.post("/backup/create")
async def create_backup(endpoint: str = Form(...)):
    try:
        db_instance = endpoint.strip().split('.')[0]
        today = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        snapshot_name = f"{db_instance}-snapshot-{today}"
        await create_snapshot(snapshot_name, db_instance, SNAPSHOT, endpoint)
        snap_status = await snapshot_status(snapshot_name, endpoint)
        return {"snapshot_name": snapshot_name, "status": snap_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backup/status", response_class=HTMLResponse)
async def backup_check(request: Request):
    return templates.TemplateResponse("check-backup.html", {"request": request})

@app.post("/backup/status")
async def backup_status(snapshotname: str = Form(...), endpoint: str = Form(...)):
    try:
        snap_status = await snapshot_status(snapshotname.strip(), endpoint.strip())
        return {"snapshot_status": snap_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backup/delete", response_class=HTMLResponse)
async def backup_delete(request: Request):
    return templates.TemplateResponse("delete-backup.html", {"request": request})

@app.post("/backup/delete")
async def delete_post(snapshotname: str = Form(...), endpoint: str = Form(...)):
    try:
        await delete_snapshot(snapshotname.strip(), endpoint.strip())
        return {"message": f"Snapshot {snapshotname} deleting..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data")
async def names():
    return JSONResponse(content={"names": ["Sudheer", "Kondla", "Neil", "Nikhil"]})

# Utility functions
async def snapshot_status(snapshot_name: str, db_url: str):
    return await (RDSDescribe().db_cluster_snapshot_status(snapshot_name) if CLUSTER in db_url else RDSDescribe().db_snapshot_status(snapshot_name))

async def create_snapshot(snapshot_name: str, instance_name: str, tag_name: str, db_url: str):
    return await (RDSCreate().rds_create_db_cluster_snapshot(snapshot_name, instance_name, tag_name) if CLUSTER in db_url else RDSCreate().rds_create_db_snapshot(snapshot_name, instance_name, tag_name))

async def delete_snapshot(snapshot_name: str, db_url: str):
    return await (RDSDelete().rds_delete_db_cluster_snapshot(snapshot_name) if CLUSTER in db_url else RDSDelete().delete_db_snapshot(snapshot_name))

def app_config():
    with open("appConfig.yaml", "r") as f:
        doc = yaml.safe_load(f)
        return doc["appConfig"].get("hostname"), doc["appConfig"].get("port"), doc["appConfig"].get("certificate"), doc["appConfig"].get("key")

if __name__ == "__main__":
    hostname, port, certificate, key = app_config()
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain(certificate, key)
    uvicorn.run(app, host=hostname, port=int(port), ssl_keyfile=key, ssl_certfile=certificate)