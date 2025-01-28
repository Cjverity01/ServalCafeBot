from pymongo import MongoClient
import os

# Get the MongoDB URI from environment variables
mongo_uri = os.getenv("DATABASE_URI")  # Replace with your actual URI if necessary

# Create a MongoClient and connect to the database
client = MongoClient(mongo_uri)
db = client.get_database('loa_requests_db')  # Use your database name
collection = db.get_collection('requests')  # Use your collection name

# Now you can import `collection` in other files
