#!/usr/bin/env python
#Author: skondla@me.com
#purpose: Build a simple python WebApp & REST API to call database service requests
#coding=utf-8

from fastapi import FastAPI, Form, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from rdsAdmin import RDSDescribe, RDSCreate, RDSDelete
import datetime
import yaml
import ssl
import uvicorn

# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/backup", response_class=HTMLResponse)
async def my_form(request: Request):
    return templates.TemplateResponse("db-backup-tool.html", {"request": request})

@app.get("/backup/create", response_class=HTMLResponse)
async def backup_create(request: Request):
    return templates.TemplateResponse("create-backup.html", {"request": request})

@app.post("/backup/create")
async def create_backup(endpoint: str = Form(...)):
    db_instance = endpoint.strip().split('.')[0]
    today = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    snapshot_name = f"{db_instance}-snapshot-{today}"
    request_db_snapshot = create_snapshot(snapshot_name, db_instance, "snapshot", endpoint)
    snap_status = snapshot_status(snapshot_name, endpoint)
    return {"snapshot_name": snapshot_name, "status": snap_status}

@app.get("/backup/status", response_class=HTMLResponse)
async def backup_check(request: Request):
    return templates.TemplateResponse("check-backup.html", {"request": request})

@app.post("/backup/status")
async def backup_status(snapshotname: str = Form(...), endpoint: str = Form(...)):
    snap_status = snapshot_status(snapshotname.strip(), endpoint.strip())
    return {"snapshot_status": snap_status}

@app.get("/backup/delete", response_class=HTMLResponse)
async def backup_delete(request: Request):
    return templates.TemplateResponse("delete-backup.html", {"request": request})

@app.post("/backup/delete")
async def delete_post(snapshotname: str = Form(...), endpoint: str = Form(...)):
    delete_snapshot(snapshotname.strip(), endpoint.strip())
    return {"message": f"Snapshot {snapshotname} deleting..."}

@app.get("/data")
async def names():
    return JSONResponse(content={"names": ["Sudheer", "Kondla", "Neil", "Nikhil"]})

# Utility functions
def snapshot_status(snapshot_name: str, db_url: str):
    return RDSDescribe().db_cluster_snapshot_status(snapshot_name) if 'cluster' in db_url else RDSDescribe().db_snapshot_status(snapshot_name)

def create_snapshot(snapshot_name: str, instance_name: str, tag_name: str, db_url: str):
    return RDSCreate().rds_create_db_cluster_snapshot(snapshot_name, instance_name, tag_name) if 'cluster' in db_url else RDSCreate().rds_create_db_snapshot(snapshot_name, instance_name, tag_name)

def delete_snapshot(snapshot_name: str, db_url: str):
    return RDSDelete().rds_delete_db_cluster_snapshot(snapshot_name) if 'cluster' in db_url else RDSDelete().delete_db_snapshot(snapshot_name)

def app_config():
    with open("appConfig.yaml", "r") as f:
        doc = yaml.safe_load(f)
        return doc["appConfig"].get("hostname"), doc["appConfig"].get("port"), doc["appConfig"].get("certificate"), doc["appConfig"].get("key")

if __name__ == "__main__":
    hostname, port, certificate, key = app_config()
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain(certificate, key)
    uvicorn.run(app, host=hostname, port=int(port), ssl_keyfile=key, ssl_certfile=certificate)
