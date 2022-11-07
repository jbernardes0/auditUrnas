import pymongo
import pymongo.errors

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["audit_eleicao_2022"]

def mongodb_conn(server_uri):
    try:
        return pymongo.MongoClient(server_uri)
    except:
        print("Could not connect to server")

def insertOne(db_conn, collection, some_dict):
    mycoll = db_conn[collection]
    x = mycoll.insert_one(some_dict)
    return x.inserted_id

def insertMany(db_conn, collection, list_of_dicts):
    mycoll = db_conn[collection]
    x = mycoll.insert_many(list_of_dicts)
    return x.inserted_ids