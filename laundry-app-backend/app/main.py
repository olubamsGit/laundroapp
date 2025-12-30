from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.models import OAuthFlows, OAuth2
from fastapi.security import OAuth2PasswordBearer


# DB & Models
from app.db.session import engine
from app.db.base import Base
from app.models.user import User

# Routers
from app.models import user, order

from app.api.auth import router as auth_router
from app.api.test_secure import router as secure_test_router
from app.api.orders import router as orders_router



# ========= CREATE APP FIRST =========
app = FastAPI(
    title="Tradon Clothing Laundry Pickup & Delivery API",
    description="Mobile laundry backend with JWT auth",
    version="1.0.0",
    servers=[{"url": "http://127.0.0.1:8000"}],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ========= STARTUP DB INIT =========
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


# ========= ROUTES =========
app.include_router(auth_router)
app.include_router(secure_test_router)
app.include_router(orders_router)


# ========= ROOT TEST =========
@app.get("/")
def root():
    return {"message": "Laundry App Backend is running!"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/auth/login",
                    "scopes": {}
                }
            }
        }
    }

    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
