from fastapi import FastAPI, HTTPException, status
from typing import Dict, Any
import uvicorn
import requests

app = FastAPI(title="Lucid Multi-Account Trade Copier")

# Security token to secure your webhook from unauthorized external hits
API_TOKEN = "VvOIjUt332XVdUeoX8Qmmw"

# Prop Firm Terminal Login Credentials
TRADOVATE_USER = "LTT4K26QL4G"
TRADOVATE_PASS = "V^58AvQ0aOqo6"
TRADOVATE_APP_ID = "Tradovate Pulse"  # Bypasses retail developer key restrictions
BASE_API_URL = "https://demo.tradovateapi.com"

def get_tradovate_token():
    """Requests a clean session token using the white-label terminal gateway."""
    auth_url = f"{BASE_API_URL}/v1/auth/accesstokenrequest"
    auth_payload = {
        "name": TRADOVATE_USER,
        "password": TRADOVATE_PASS,
        "appId": TRADOVATE_APP_ID,
        "appVersion": "1.0"
    }
    try:
        response = requests.post(auth_url, json=auth_payload, timeout=5)
        if response.status_code in [200, 201]:
            return response.json().get("accessToken")
        print(f"Prop Firewall Auth Failed! Status: {response.status_code} | Text: {response.text}")
        return None
    except Exception as e:
        print(f"Auth Exception: {str(e)}")
        return None

@app.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_tradingview_webhook(payload: Dict[str, Any]):
    # Validate incoming TradingView webhook token
    incoming_token = payload.get("token")
    if incoming_token != API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    
    print(f"Alert Received! Processing Payload: {payload}")
    
    action = str(payload.get("data", "buy")).lower()
    symbol = payload.get("symbol", "ESU2026")
    quantity = payload.get("quantity", 2)
    
    # Fallback to your two fresh active prop accounts if not passed by the webhook array
    accounts_list = payload.get("multiple_accounts", [])
    if not accounts_list:
        accounts_list = [{"account_id": "LFE10075686900004"}, {"account_id": "LFE10075686900003"}]
    
    # Fetch terminal authorization session token
    broker_token = get_tradovate_token()
    if not broker_token:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Broker gate validation rejected.")
        
    BROKER_API_URL = f"{BASE_API_URL}/v1/order/placeorder" 
    headers = {
        "Authorization": f"Bearer {broker_token}",
        "Content-Type": "application/json"
    }
    
    results = []
    
    # Run the trade copier loop simultaneously across both configurations
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
            print(f"Executing Copier -> Account: {current_id} | Action: {broker_payload['action']}")
            response = requests.post(BROKER_API_URL, json=broker_payload, headers=headers, timeout=5)
            print(f"Account {current_id} Gateway Result: {response.status_code} | {response.text}")
            results.append({"account": current_id, "status": response.status_code, "response": response.text})
        except Exception as e:
            results.append({"account": current_id, "error": str(e)})
            
    return {"status": "multi_executed", "details": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
