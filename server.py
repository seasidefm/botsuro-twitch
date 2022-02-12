import os

from sanic import Sanic, json
from dotenv import load_dotenv

from db import DB

load_dotenv()

app = Sanic("bot_companion")

app.db = DB()


@app.get("/")
def root(request):
    return "<p>Hello, world</p>"


@app.get("/status")
def status(request):
    return json({
        "status": "OK",
        "more-stats": ["something here"]
    })


@app.get("/requests")
async def requests(request):
    rq = await app.db.get_requests()
    return json(rq)


if __name__ == "__main__":
    print("[Server] Starting bot companion server")
    is_dev = os.environ.get('SERVER_ENV') == "development"
    app.run(host="0.0.0.0", debug=is_dev, auto_reload=is_dev)
