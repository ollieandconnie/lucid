from fastapi import FastAPI, HTTPException, status
from typing import Dict, Any
import uvicorn
import requests

app = FastAPI(title="Custom Trading Webhook Relay")

# The security token validating incoming alerts from TradingView
API_TOKEN = "VvOIjUt332XVdUeoX8Qmmw"

# Your active, verified master authorization token
MASTER_BROKER_TOKEN = "VvOIjUt332XVdUeoX8Qmmw"

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
    
    # Direct routing via the dedicated API endpoint
    BROKER_API_URL = "https://demo.tradovateapi.com/v1/order/placeorder" 
    
    headers = {
        "Authorization": f"Bearer {MASTER_BROKER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Ensure account format is clean
    clean_account_id = account_id
    if str(account_id).isdigit():
        clean_account_id = int(account_id)
    
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
        
        print(f"Broker Response Status: {response.status_code} | Text: {response.text}")
        return {"status": "processed", "broker_status": response.status_code, "details": response.text}
            
    except Exception as e:
        print(f"Network error trying to transmit to broker: {str(e)}")
        raise HTTPException(status_code=500, detail="Broker transmission failure.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
