from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb+srv://nmahendratekion:MHBLpIi6R2VCAGSa@moneytrackerproj.ocpr9tj.mongodb.net/?retryWrites=true&w=majority&appName=moneytrackerproj')
db = client.money_tracker

USER_ID = ObjectId("6811e57b265cbc2a12c06354")  # Convert string to ObjectId

# Update all categories with user_id null and is_global false to have the correct user_id
result = db.categories.update_many(
    {'user_id': None, 'is_global': False},
    {'$set': {'user_id': USER_ID}}
)
print(f"Updated {result.modified_count} user categories with user_id.")

print("User category update complete.") 