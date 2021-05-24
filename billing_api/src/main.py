import uvicorn
from fastapi import FastAPI
from src.api.v1.service import service_router
from src.api.v1.user import user_router
from src.core.tortoise import TORTOISE_CFG
from src.orm.utils import tortoise_init, tortoise_release

app = FastAPI()
app.include_router(service_router, prefix="/api")
app.include_router(user_router, prefix="/api")


@app.on_event("startup")
async def startup():
    await tortoise_init(config=TORTOISE_CFG)


@app.on_event("shutdown")
async def shutdown():
    await tortoise_release()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888)
