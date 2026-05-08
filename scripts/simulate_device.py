import asyncio
import httpx
import json
import time
import random
import os
from typing import Optional

API_URL = "http://localhost:8000/v1"
INGEST_URL = "http://localhost:8001/v1/ingest"

async def login() -> str:
    print("1. Logging in...")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(f"{API_URL}/auth/login", json={
                "email": "test@example.com",
                "password": "Password123!"
            })
            res.raise_for_status()
            data = res.json()
            return data["access_token"]
        except Exception as e:
            print(f"Login failed: {e}. Please ensure you have created an account.")
            exit(1)

async def get_project(token: str) -> str:
    print("2. Fetching project...")
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{API_URL}/projects", headers={"Authorization": f"Bearer {token}"})
        data = res.json()
        if not data or len(data) == 0:
            print("No projects found.")
            exit(1)
        return data[0]["id"]

async def provision_device(token: str, project_id: str) -> dict:
    print("3. Provisioning simulator device...")
    async with httpx.AsyncClient() as client:
        # Check if device already exists
        res = await client.get(f"{API_URL}/projects/{project_id}/devices", headers={"Authorization": f"Bearer {token}"})
        devices = res.json().get("data", [])
        simulator = next((d for d in devices if d["name"] == "Simulator-01"), None)
        
        if simulator:
            print(f"   Using existing Simulator device: {simulator['id']}")
            return {"device_id": simulator["id"], "http_token": "UNKNOWN_REPROVISION_NEEDED"}

        # Create new
        res = await client.post(f"{API_URL}/projects/{project_id}/devices", 
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Simulator-01",
                "description": "Auto-generated simulator device",
                "labels": {"type": "simulator"}
            }
        )
        data = res.json()
        return {
            "device_id": data["device"]["id"],
            "http_token": data["credentials"]["http_token"]
        }

async def simulate_telemetry(project_id: str, device_id: str, http_token: str):
    print("\n--- Starting Simulation ---")
    print(f"Sending data to {INGEST_URL}")
    print("Press Ctrl+C to stop.\n")
    
    async with httpx.AsyncClient() as client:
        while True:
            temp = round(random.uniform(20.0, 60.0), 2)
            hum = round(random.uniform(30.0, 80.0), 2)
            
            payload = {
                "temperature": temp,
                "humidity": hum
            }
            
            try:
                res = await client.post(
                    INGEST_URL,
                    headers={
                        "Authorization": f"Bearer {http_token}",
                        "X-Project-ID": project_id
                    },
                    json=payload
                )
                if res.status_code == 202:
                    print(f"[{time.strftime('%H:%M:%S')}] Sent: Temp={temp}°C, Hum={hum}%")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Failed: {res.status_code} - {res.text}")
            except Exception as e:
                print(f"Error sending telemetry: {e}")
                
            await asyncio.sleep(2)

async def main():
    token = await login()
    project_id = await get_project(token)
    device_info = await provision_device(token, project_id)
    
    if device_info["http_token"] == "UNKNOWN_REPROVISION_NEEDED":
        print("\nWARNING: Found an existing Simulator device but I don't have its HTTP Token.")
        print("Please delete the 'Simulator-01' device in the UI and run this script again,")
        print("or hardcode the token in the script if you saved it.")
        return

    await simulate_telemetry(project_id, device_info["device_id"], device_info["http_token"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
