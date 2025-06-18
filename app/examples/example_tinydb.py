from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tinydb import TinyDB, Query

app = FastAPI()
db = TinyDB("test_db.json")
User = Query()

class UserModel(BaseModel):
    username: str
    email: str

@app.post("/users/")
def create_user(user: UserModel):
    if db.search(User.username == user.username):
        raise HTTPException(status_code=400, detail="User already exists")
    db.insert(user.dict())
    return {"msg": "User created", "user": user}

@app.get("/users/{username}")
def get_user(username: str):
    result = db.search(User.username == username)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result[0]
