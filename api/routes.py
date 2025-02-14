from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from .middleware import verify_api_key, RateLimiter
from services.data_access import DataAccessService
from agents.aura import AuraAgent
from agents.myca import MycaAgent
from agents.infy import InfyAgent

app = FastAPI(title="Cynix API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimiter)


@app.get("/")
async def root():
    return {
        "name": "Cynix API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.post("/api/v1/analyze/code")
async def analyze_code(
        data: Dict[str, Any],
        api_key: str = Depends(verify_api_key)
):
    """Analyze GitHub repository and code quality"""
    try:
        agent = AuraAgent(
            model_path="models/cynix-code-analyzer",
            config=app.state.config
        )
        await agent.initialize()

        result = await agent.process_data(data)
        await agent.cleanup()

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/api/v1/analyze/meme")
async def analyze_meme(
        data: Dict[str, Any],
        api_key: str = Depends(verify_api_key)
):
    """Analyze meme virality and originality"""
    try:
        agent = MycaAgent(
            model_path="models/cynix-meme-analyzer",
            config=app.state.config
        )
        await agent.initialize()

        result = await agent.process_data(data)
        await agent.cleanup()

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/api/v1/analyze/influencer")
async def analyze_influencer(
        data: Dict[str, Any],
        api_key: str = Depends(verify_api_key)
):
    """Analyze influencer credibility"""
    try:
        agent = InfyAgent(
            model_path="models/cynix-influencer-analyzer",
            config=app.state.config
        )
        await agent.initialize()

        result = await agent.process_data(data)
        await agent.cleanup()

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/api/v1/data/{data_type}")
async def get_data(
        data_type: str,
        wallet_address: str,
        params: Dict[str, Any] = None,
        api_key: str = Depends(verify_api_key)
):
    """Get raw data access based on token stake"""
    try:
        data_service = DataAccessService(
            config=app.state.config,
            cynix_token=app.state.cynix_token
        )

        result = await data_service.get_raw_data(
            wallet_address,
            data_type,
            params
        )

        if "error" in result:
            raise HTTPException(
                status_code=403,
                detail=result["error"]
            )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/api/v1/webhook")
async def webhook_handler(
        request: Request,
        api_key: str = Depends(verify_api_key)
):
    """Handle incoming webhooks"""
    try:
        payload = await request.json()
        event_type = request.headers.get("X-Cynix-Event")

        if not event_type:
            raise HTTPException(
                status_code=400,
                detail="Missing event type header"
            )

        # Process webhook based on event type
        result = await process_webhook(event_type, payload)

        return {
            "status": "processed",
            "event_type": event_type,
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


async def process_webhook(
        event_type: str,
        payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Process different webhook events"""
    handlers = {
        "new_alpha": handle_alpha_webhook,
        "new_meme": handle_meme_webhook,
        "price_alert": handle_price_webhook
    }

    handler = handlers.get(event_type)
    if not handler:
        raise ValueError(f"Unsupported event type: {event_type}")

    return await handler(payload)