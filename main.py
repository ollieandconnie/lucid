from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List
import uvicorn
import requests

app = FastAPI(title="Custom Trading Webhook Relay")

API_TOKEN = "VvOIjUt332XVdUeoX8Qmmw"

class AccountConfig(BaseModel):
    token: str
    account_id: str
    risk_percentage: int
    quantity_multiplier: int

class TradingViewPayload(BaseModel):
    symbol: str
    strategy_name: str
    date: str
    data: str  
    quantity: int
    price: str
    token: str
    multiple_accounts: List[AccountConfig]

@app.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_tradingview_webhook(payload: TradingViewPayload):
    if payload.token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid security token credentials."
        )
    
    print(f"Verified Alert Received: {payload.strategy_name} - Action: {payload.data.upper()}")
    
    order_side = payload.data.lower()  
    order_qty = payload.quantity
    
    # Replace this URL with Lucid/Tradovate's actual API endpoint when ready
    BROKER_API_URL = "https://api.lucidtrading.com/v1/orders" 
    
    headers = {
        "Authorization": f"Bearer {payload.multiple_accounts[0].token}",
        "Content-Type": "application/json"
    }
    
    broker_payload = {
        "account": payload.multiple_accounts[0].account_id,
        "action": "BUY" if order_side == "buy" else "SELL",
        "symbol": payload.symbol,
        "orderQty": order_qty,
        "orderType": "Market"
    }
    
    try:
        response = requests.post(BROKER_API_URL, json=broker_payload, headers=headers, timeout=5)
        if response.status_code in [200, 201]:
            return {"status": "success", "broker_response": response.json()}
        else:
            return {"status": "broker_error", "details": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broker transmission failure: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
