from fastapi import FastAPI, HTTPException, status
from typing import Dict, Any
import uvicorn
import requests

app = FastAPI(title="Direct Master Token Copy-Trader")

# Security key protecting your webhook door from the outside world
API_TOKEN = "VvOIjUt332XVdUeoX8Qmmw"

# =========================================================================
# PASTE YOUR TEMPORARY ACCESSTOKEN HERE (Gleaned from the platform network tab)
# =========================================================================
LIVE_BROKER_BEARER_TOKEN = "PASTE_YOUR_ACTUAL_TRADOVATE_SESSION_TOKEN_HERE"

BASE_API_URL = "https://demo.tradovateapi.com"

@app.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_tradingview_webhook(payload: Dict[str, Any]):
    incoming_token = payload.get("token")
    if incoming_token != API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    
    print(f"Validated Alert Received! Routing to Multi-Account Chain: {payload}")
    
    action = str(payload.get("data", "buy")).lower()
    symbol = payload.get("symbol", "ESU2026")
    quantity = payload.get("quantity", 2)
    
    accounts_list = payload.get("multiple_accounts", [])
    if not accounts_list:
        accounts_list = [{"account_id": "LFE10075686900001"}, {"account_id": "LFE10075686900002"}]
    
    BROKER_API_URL = f"{BASE_API_URL}/v1/order/placeorder" 
    headers = {
        "Authorization": f"Bearer {LIVE_BROKER_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    results = []
    for acc in accounts_list:
        current_id = acc.get("account_id")
        
        clean_account_id = current_id
        if str(current_id).isdigit():
            clean_account_id = int(current_id)
            
        broker_payload = {
            "accountId": clean_account_id,
            "accountSpec": str(current_id),
            "symbol": str(symbol).upper(),
            "action": "Buy" if "buy" in action else "Sell",
            "orderQty": int(quantity),
            "orderType": "Market",
            "isCheck": False
        }
        
        try:
            print(f"Direct Route Executing -> Target: {current_id} | Action: {broker_payload['action']}")
            response = requests.post(BROKER_API_URL, json=broker_payload, headers=headers, timeout=5)
            print(f"Account {current_id} Result Status: {response.status_code} | Msg: {response.text}")
            results.append({"account": current_id, "status": response.status_code, "response": response.text})
        except Exception as e:
            results.append({"account": current_id, "error": str(e)})
            
    return {"status": "direct_processed", "summary": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
