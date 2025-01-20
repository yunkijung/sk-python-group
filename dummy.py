from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['certificate_db']
users_collection = db['users']

# Dummy data for users
dummy_users = [
    {
        "user_id": "yun",
        "password": "1234",  # You may want to hash the password in a real app
        "name": "YunKi",
        "email": "yun@gmail.com",
        "course": "Python",
        "startDate": datetime(2022, 6, 12).strftime('%Y-%m-%d'),
        "endDate": datetime(2022, 9, 12).strftime('%Y-%m-%d'),
        "role": "student"
    },
    {
        "user_id": "kim",
        "password": "1111",
        "name": "KimHun",
        "email": "kim.hun@example.com",
        "course": "Network",
        "startDate": datetime(2022, 6, 12).strftime('%Y-%m-%d'),
        "endDate": datetime(2022, 12, 18).strftime('%Y-%m-%d'),
        "role": "student"
    },
    {
        "user_id": "admin",
        "password": "admin",
        "name": "Admin",
        "email": "admin@example.com",
        "course": "",
        "startDate": "",
        "endDate": "",
        "role": "admin"
    }
]

# Insert the dummy data into the users collection
result = users_collection.insert_many(dummy_users)

# Print out the IDs of the inserted documents
print(f"Inserted {len(result.inserted_ids)} dummy users into the 'users' collection.")
