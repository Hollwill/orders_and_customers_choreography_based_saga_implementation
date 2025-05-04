from fastapi import FastAPI, Depends, HTTPException
from pymongo.asynchronous.collection import AsyncCollection
from fastapi import status

from src.database import  get_order_history_collection
from src.schemas import  CustomerOrderHistorySchema

app = FastAPI()


@app.get("/customers/{item_id}/orderhistory")
async def get_orders_list(item_id: int, collection: AsyncCollection  = Depends(get_order_history_collection)) -> CustomerOrderHistorySchema:
    customer_orders_history = await collection.find_one(item_id)
    if not customer_orders_history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No customers found")
    return CustomerOrderHistorySchema.model_validate(customer_orders_history)
