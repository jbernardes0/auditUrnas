import pymongo
import pymongo.errors

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

def find(db_conn, collection, filter_expr=None):  
    mycoll = db_conn[collection]
    if not filter_expr:
        x = mycoll.find()
    else:
        x = mycoll.find(filter_expr)
    return list(x)


def updateOne(db_conn, collection, filter, new_values):
    mycoll = db_conn[collection]
    x = mycoll.update_one(filter, {"$set": new_values}, upsert=True)
    return x

# Consultas especificas do schema
def getBUdetails(db_conn):
    mycoll = db_conn['zonas_eleitorais']
    pipeline = [
        {"$group": {"_id": "$SG_UF", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
        ]
    x = mycoll.aggregate(pipeline)
    return list(x)