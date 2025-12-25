from fastapi import APIRouter
from app.api import auth, clients, masters, services, products, appointments, payments, reports

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(clients.router)
api_router.include_router(masters.router)
api_router.include_router(services.router)
api_router.include_router(products.router)
api_router.include_router(appointments.router)
api_router.include_router(payments.router)
api_router.include_router(reports.router)
