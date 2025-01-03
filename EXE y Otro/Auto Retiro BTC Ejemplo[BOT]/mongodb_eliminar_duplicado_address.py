from pymongo import MongoClient

client = MongoClient("mongodb://animeflv:Onyx01091995@onyx.i234.me:27017/")
db = client["admin"]
collection = db["vulnerable_wallet"]

# Usar aggregation para encontrar duplicados con opción de usar disco
pipeline = [
    {"$group": {"_id": "$address", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
    {"$match": {"count": {"$gt": 1}}}
]

# Ejecutar la agregación
duplicados = list(collection.aggregate(pipeline, allowDiskUse=True))  # Permite usar disco si es necesario

for doc in duplicados:
    address = doc["_id"]  # _id contiene el valor de "address"
    count = doc["count"]  # Número de duplicados
    print(f"Address: {address} tiene {count} duplicados")

    # Eliminar todos los duplicados, dejando el primero
    ids_a_eliminar = doc["ids"][1:]  # Salta el primer ID, ya que lo queremos conservar
    collection.delete_many({"_id": {"$in": ids_a_eliminar}})


print("Duplicados eliminados.")