from fastapi import FastAPI, HTTPException, status
from typing import Dict, Any
import uvicorn
import requests

app = FastAPI(title="Custom Trading Multi-Account Relay")

API_TOKEN = "VvOIjUt332XVdUeoX8Qmmw"
TRADOVATE_USER = "LTT4K26QL4G"
TRADOVATE_PASS = "V^58AvQ0aOqo6"
TRADOVATE_APP_ID = "Lucid Trading" 
BASE_API_URL = "https://demo.tradovateapi.com"

def get_tradovate_token():
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
        return None
    except Exception:
        return None

@app.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_tradingview_webhook(payload: Dict[str, Any]):
    incoming_token = payload.get("token")
    if incoming_token != API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    
    print(f"Validated Alert Received! Processing Multi-Account Payload: {payload}")
    
    action = str(payload.get("data", "buy")).lower()
    symbol = payload.get("symbol", "ESU2026")
    quantity = payload.get("quantity", 2)
    
    # Extract the full list of accounts dynamically
    accounts_list = payload.get("multiple_accounts", [])
    if not accounts_list:
        # Fallback if list is empty
        accounts_list = [{"account_id": "LFE10075686900001"}]
    
    broker_token = get_tradovate_token()
    if not broker_token:
        print("ERROR: Broker rejected master login credentials.")
        return {"status": "auth_error", "message": "Failed broker authorization."}
        
    BROKER_API_URL = f"{BASE_API_URL}/v1/order/placeorder" 
    headers = {
        "Authorization": f"Bearer {broker_token}",
        "Content-Type": "application/json"
    }
    
    results = []
    
    # LOOP THROUGH EVERY ACCOUNT DETECTED IN THE PAYLOAD
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
            print(f"Executing Trade -> Account Target: {current_id} | Action: {broker_payload['action']}")
            response = requests.post(BROKER_API_URL, json=broker_payload, headers=headers, timeout=5)
            results.append({"account": current_id, "status": response.status_code, "response": response.text})
        except Exception as e:
            results.append({"account": current_id, "error": str(e)})
            
    return {"status": "multi_processed", "summary": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
