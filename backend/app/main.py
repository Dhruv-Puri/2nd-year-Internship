# from fastapi import app
from typing import List
from fastapi import FastAPI

api = FastAPI()

# creating endpoints - 

@api.post("/register")
def register(user_in):
    pass

@api.post("/clubs"):
def login(form_data):
    pass
    
