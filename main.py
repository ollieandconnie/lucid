from fastapi import FastAPI, HTTPException, status
from typing import Dict, Any
import uvicorn
import requests

app = FastAPI(title="Custom Trading Webhook Relay")

# Security Token for TradingView validation
API_TOKEN = "VvOIjUt332XVdUeoX8Qmmw"

# Your Secure Lucid Trading / Tradovate Platform Credentials
TRADOVATE_USER = "LTT4K26QL4G"
TRADOVATE_PASS = "V^58AvQ0aOqo6"

# Change this to "https://live.tradovateapi.com" if trading on real live capital
BASE_API_URL = "https://demo.tradovateapi.com"

def get_tradovate_token():
    """Authenticates with Tradovate and fetches a fresh bearer token dynamically."""
    auth_url = f"{BASE_API_URL}/v1/auth/accesstokenrequest"
    auth_payload = {
        "name": TRADOVATE_USER,
        "password": TRADOVATE_PASS
    }
    try:
        response = requests.post(auth_url, json=auth_payload, timeout=5)
        if response.status_code in [200, 201]:
            return response.json().get("accessToken")
        else:
            print(f"Tradovate Login Authentication Failed: {response.text}")
            return None
    except Exception as e:
        print(f"Network error during authentication: {str(e)}")
        return None

@app.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_tradingview_webhook(payload: Dict[str, Any]):
    incoming_token = payload.get("token")
    if incoming_token != API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    
    print(f"Validated Alert Received! Payload: {payload}")
    
    action = str(payload.get("data", "buy")).lower()
    symbol = payload.get("symbol", "ESU2026")
    quantity = payload.get("quantity", 2)
    
    accounts_list = payload.get("multiple_accounts", [])
    account_id = accounts_list[0].get("account_id") if accounts_list else "LFE10075686900001"
    
    # Generate token dynamically right now
    broker_token = get_tradovate_token()
    if not broker_token:
        raise HTTPException(status_code=500, detail="Could not authorize with Tradovate.")
        
    BROKER_API_URL = f"{BASE_API_URL}/v1/order/placeorder" 
    headers = {
        "Authorization": f"Bearer {broker_token}",
        "Content-Type": "application/json"
    }
    
    clean_account_id = int(account_id) if str(account_id).isdigit() else 568690
    
    broker_payload = {
        "accountId": clean_account_id,
        "accountSpec": str(account_id),
        "symbol": str(symbol).upper(),
        "action": "Buy" if "buy" in action else "Sell",
        "orderQty": int(quantity),
        "orderType": "Market",
        "isCheck": False
    }
    
    try:
        print(f"Forwarding trade to broker -> Account: {account_id} | Action: {broker_payload['action']}")
        response = requests.post(BROKER_API_URL, json=broker_payload, headers=headers, timeout=5)
        
        if response.status_code in [200, 201]:
            print(f"Broker Order Placed Successfully: {response.text}")
            return {"status": "success", "broker_response": response.json()}
        else:
            print(f"Broker Server Rejected Order Parameters: {response.text}")
            return {"status": "broker_error", "details": response.text}
            
    except Exception as e:
        print(f"Network error trying to transmit to broker: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Broker server transmission failure.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
