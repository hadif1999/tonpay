

from mongoengine import (connect, Document, StringField, DateTimeField, IntField, 
                         FloatField, ListField, DictField)
import os, datetime as dt


connect(host = os.getenv("DB_URI") or "mongodb://127.0.0.1:27017/tonpay")

CHATID = StringField(required=True, min_length=10,
                          max_length=100, unique=True,
                          primary_key=True)


class User(Document):
    chat_id = CHATID
    email = StringField(regex=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
                        required=False, min_length=5, 
                        max_length=200, unique=True, 
                        default=None, sparse=True)
    

class Wallet(Document):
    date_created = DateTimeField(required=True,
                                 default=DateTimeField(default=dt.datetime.now(dt.UTC)))
    chat_id = CHATID
    

# wallet on blockchain
class External_Wallet(Wallet):
    address = StringField(required=True, min_length=10,
                          max_length=200, unique=True)
    seeds = StringField(required=True, unique=True, # SHA256(chat_id:date_created("Y-M-D_H:MM:S"):salt)
                        min_length=10, max_length=1000) 


# wallet inside the platform
class Internal_Wallet(Wallet):
    balance = FloatField(min_value=0, default=0)
    address = StringField(required=True, unique=True,  # SHA256(chat_id:date_created("Y-M-D_H:MM:S"):address)
                          min_length=10, max_length=1000) 
    

class Transactions(Document):
    src = DictField() # "src":{"address": --- , "chat_id": --- }
    dest = DictField() # "dest":{"address":---, "chat_id": --- }
    amount = FloatField(min_value=1, default=0)
    datetime = DateTimeField(required=True,
                             default=DateTimeField(default=dt.datetime.now(dt.UTC)))
    id = StringField(required=True, unique=True, # SHA256(src.chat_id:dest.chat_id:datetime("Y-M-D_H:MM:S"))
                     min_length=10, max_length=1000) 

    
    
    
    