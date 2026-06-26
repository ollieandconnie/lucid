from fastapi import FastAPI, HTTPException, status
from typing import Dict, Any
import uvicorn
import requests

app = FastAPI(title="Custom Trading Webhook Relay")

# The secret token you put inside your TradingView text message
API_TOKEN = "VvOIjUt332XVdUeoX8Qmmw"

@app.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_tradingview_webhook(payload: Dict[str, Any]):
    # 1. Extract token safely from the incoming message data
    incoming_token = payload.get("token")
    
    if incoming_token != API_TOKEN:
        print(f"Unauthorized payload attempt blocked. Received token: {incoming_token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid security token credentials."
        )
    
    print(f"Validated Alert Received! Raw Payload Data: {payload}")
    
    # 2. Extract action signals flexibly from the data payload
    action = str(payload.get("data", "buy")).lower()
    symbol = payload.get("symbol", "ESU2026")
    quantity = payload.get("quantity", 1)
    
    # 3. Pull target broker account variables from your multiple account block
    accounts_list = payload.get("multiple_accounts", [])
    if not accounts_list:
        print("Error: No broker account details passed in payload.")
        return {"status": "error", "message": "Missing account definition block"}
        
    broker_token = accounts_list[0].get("token")
    account_id = accounts_list[0].get("account_id")
    
    # 4. Corrected Domain URL for Lucid's Live/Simulation Tradovate API Architecture
    BROKER_API_URL = "https://api.lucidat.com/v1/order/placeorder" 
    
    headers = {
        "Authorization": f"Bearer {broker_token}",
        "Content-Type": "application/json"
    }
    
    # Safely convert account ID values to prevent parsing script errors
    clean_account_id = int(account_id) if str(account_id).isdigit() else account_id
    
    broker_payload = {
        "accountId": clean_account_id,
        "accountSpec": str(account_id),
        "symbol": str(symbol).upper(),
        "action": "Buy" if "buy" in action else "Sell",
        "orderQty": int(quantity),
        "orderType": "Market"
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
