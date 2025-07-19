from pymongo import MongoClient
from urllib.parse import quote_plus

# Encode username and password
username = quote_plus("aamanoj743")
password = quote_plus("nihalmanoj")

# Construct the connection string
connection_string = f"mongodb+srv://aamanoj743:nihalmanoj@cluster0.5lnuo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Connect to the MongoDB cluster
client = MongoClient(connection_string)

# Access a database and collection
db = client["mydatabase"]
collection = db["mycollection"]

# Example: Insert a document
data = {"name": "John", "age": 30, "city": "New York"}
collection.insert_one(data)

print("Data inserted successfully!")
