from pymongo import MongoClient
import certifi

MONGO_URI = "mongodb+srv://akshaykumarpatil58_db_user:pmOtmW4Unnsy7awO@career.vqrlmzl.mongodb.net/"

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=10000)

    # Force connection
    client.server_info()
    print("✅ MongoDB Connected Successfully")

    db = client["users"]
    collection = db["authentication"]

    count = collection.count_documents({})
    print(f"📊 Documents in 'authentication' collection: {count}")

    test_data = {
        "name": "Test User",
        "email": "test@example.com"
    }

    result = collection.insert_one(test_data)
    print("✅ Test data inserted successfully")
    print("Inserted ID:", result.inserted_id)

    # Verify read
    data = collection.find_one({"email": "test@example.com"})
    print("📥 Fetched:", data)

    # Clean up test data
    collection.delete_one({"_id": result.inserted_id})
    print("🧹 Test document cleaned up")

except Exception as e:
    print("❌ Error:", str(e))
