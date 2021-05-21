import uvicorn
from api.v1.service import service_router
from api.v1.user import user_router
from fastapi import FastAPI
from orm.utils import tortoise_init, tortoise_release
from settings import TORTOISE_CFG

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
