import asyncio
import uvicorn
from fastapi import FastAPI
from api.routes import app
from utils.config import Config
from utils.logger import get_logger
from blockchain.token import CynixToken
from services.telegram import CynixTelegramBot
from services.twitter import CynixTwitterBot

logger = get_logger(__name__)


async def startup():
    """Initialize application services"""
    logger.info("Starting Cynix services...")

    config = Config()
    app.state.config = config.config_data

    app.state.cynix_token = CynixToken(
        config.get("solana_rpc_url"),
        config.get("cynix_token_address"),
        config.get("admin_keypair")
    )

    app.state.telegram_bot = CynixTelegramBot(
        config.get("telegram_bot_token"),
        app.state.cynix_token,
        config.config_data
    )

    app.state.twitter_bot = CynixTwitterBot(
        config.config_data,
        app.state.model
    )

    # Start services
    await app.state.telegram_bot.start()
    logger.info("All services started successfully")


async def shutdown():
    logger.info("Shutting down Cynix services...")

    if hasattr(app.state, "telegram_bot"):
        await app.state.telegram_bot.stop()

    if hasattr(app.state, "cynix_token"):
        await app.state.cynix_token.close()

    logger.info("All services shut down successfully")


app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )