from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Dict
from decouple import config

# For MySQL
import mysql.connector

# For MongoDB
from pymongo import MongoClient

app = FastAPI()
security = HTTPBasic()

# MySQL configuration
mysql_config = {
    'host': config('SQL_HOST'),
    'user': config('SQL_USER'),
    'password': config('SQL_PASSWORD'),
    'database': config('SQL_DATABASE')
}

# MongoDB configuration
mongo_config = {
    'host': 'mongodb://localhost:27017/',
    'db_name': 'book_db'
}

# Database connection
db = mysql.connector.connect(**mysql_config)
mongo_client = MongoClient(mongo_config['host'])
mongo_db = mongo_client[mongo_config['db_name']]


class BookItem(BaseModel):
    title: str
    description: str
    completed: bool


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = 'admin'
    correct_password = 'password'
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@app.post("/book_app")
def create_book_item(item: BookItem, auth: bool = Depends(authenticate)):
    # MySQL implementation
    cursor = db.cursor()
    query = "INSERT INTO book (title, description, completed) VALUES (%s, %s, %s)"
    values = (item.title, item.description, item.completed)
    cursor.execute(query, values)
    db.commit()
    item_id = cursor.lastrowid
    cursor.close()
    return {"id": item_id, **item.dict()}


@app.get("/book_app/{item_id}")
def read_book_item(item_id: int, auth: bool = Depends(authenticate)):
    # MySQL implementation
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM book WHERE id = %s"
    cursor.execute(query, (item_id,))
    result = cursor.fetchone()
    cursor.close()
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@app.put("/book_app/{item_id}")
def update_book_item(item_id: int, item: BookItem, auth: bool = Depends(authenticate)):
    # MySQL implementation
    cursor = db.cursor()
    query = "UPDATE book SET title = %s, description = %s, completed = %s WHERE id = %s"
    values = (item.title, item.description, item.completed, item_id)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    return {"message": "Item updated"}


@app.delete("/book_app/{item_id}")
def delete_book_item(item_id: int, auth: bool = Depends(authenticate)):
    # MySQL implementation
    cursor = db.cursor()
    query = "DELETE FROM book WHERE id = %s"
    cursor.execute(query, (item_id,))
    db.commit()
    cursor.close()
    return {"message": "Item deleted"}


# MongoDB implementation
@app.post("/book_app/mongodb")
def create_book_item_mongo(item: BookItem, auth: bool = Depends(authenticate)):
    collection = mongo_db['book']
    item_dict = item.dict()
    item_dict.pop('id', None)  # Remove 'id' field if present
    result = collection.insert_one(item_dict)
    return {"id": str(result.inserted_id), **item_dict}


@app.get("/book_app/mongodb/{item_id}")
def read_book_item_mongo(item_id: str, auth: bool = Depends(authenticate)):
    collection = mongo_db['book']
    result = collection.find_one({"_id": item_id})
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@app.put("/book_app/mongodb/{item_id}")
def update_book_item_mongo(item_id: str, item: BookItem, auth: bool = Depends(authenticate)):
    collection = mongo_db['book']
    item_dict = item.dict()
    item_dict.pop('id', None)  # Remove 'id' field if present
    result = collection.update_one({"_id": item_id}, {"$set": item_dict})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item updated"}


@app.delete("/book_app/mongodb/{item_id}")
def delete_book_item_mongo(item_id: str, auth: bool = Depends(authenticate)):
    collection = mongo_db['book']
    result = collection.delete_one({"_id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}
