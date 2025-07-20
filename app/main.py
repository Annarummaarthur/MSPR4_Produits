# app/main.py
import os
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv
import aio_pika

from app.db import Base, engine
from app.routes import router as product_router
from app.messaging.broker import MessageBroker

load_dotenv()

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL", "amqp://admin:password@host.docker.internal:5672/"
)
SERVICE_NAME = "product-api"

broker = MessageBroker(RABBITMQ_URL, SERVICE_NAME)


async def handle_external_events(message: aio_pika.IncomingMessage):
    """Handler pour les événements provenant des autres services"""
    async with message.process():
        try:
            event = json.loads(message.body.decode())
            event_type = event.get("event_type")
            data = event.get("data", {})

            print(f"📨 Received event: {event_type} from {event.get('service')}")

            if event_type == "customer.created":
                customer_id = data.get("customer_id")
                print(f"New customer created: {customer_id}")

            elif event_type == "order.created":
                order_data = data.get("order_data", {})
                print(f"New order created: {order_data}")

            elif event_type == "order.cancelled":
                order_id = data.get("order_id")
                print(f"Order cancelled: {order_id}")

        except json.JSONDecodeError:
            print("❌ Error: Invalid JSON in message")
        except Exception as e:
            print(f"❌ Error processing event: {str(e)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Products API...")

    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

    try:
        await broker.connect()
        print("✅ Connected to message broker")

        await broker.subscribe_to_events(
            event_patterns=[
                "customer.created",
                "customer.updated",
                "customer.deleted",
                "order.created",
                "order.updated",
                "order.cancelled",
            ],
            callback=handle_external_events,
        )
        print("✅ Subscribed to external events")

    except Exception as e:
        print(f"❌ Failed to connect to message broker: {str(e)}")

    app.state.broker = broker

    yield

    print("🛑 Shutting down Products API...")
    if broker.connection and not broker.connection.is_closed:
        await broker.connection.close()
        print("✅ Message broker connection closed")


app = FastAPI(
    title="API Gestion des Produits",
    description="API REST pour la gestion des produits PayeTonKawa",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(product_router)


@app.get("/")
def read_root():
    return {"message": "Products API is running"}


@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé"""
    broker_status = (
        "connected"
        if broker.connection and not broker.connection.is_closed
        else "disconnected"
    )
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "message_broker": broker_status,
    }
