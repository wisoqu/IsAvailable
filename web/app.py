from fastapi import FastAPI
from network.ip_resolve import dns_resolve
import uvicorn

app = FastAPI()

@app.post("/check")
async def check(domain: str):
    ip, logs = dns_resolve(domain)

    return {
        "ip" : ip,
        "logs" : logs,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)