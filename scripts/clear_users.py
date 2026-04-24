"""
Script to clear all documents from the MongoDB 'authentication' collection
in the 'users' database on MongoDB Atlas.
"""
import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from pymongo import MongoClient
import certifi

def clear_users():
    print(f"Connecting to MongoDB: {settings.MONGODB_URL[:40]}...")
    client = MongoClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=8000,
        tlsCAFile=certifi.where(),
    )

    # Verify connection
    client.admin.command("ping")
    print("✅ Connected to MongoDB Atlas successfully.")

    db = client[settings.MONGODB_DB_NAME]  # 'users' database
    collection = db["authentication"]       # 'authentication' collection

    count_before = collection.count_documents({})
    print(f"\n📦 Current documents in 'authentication' collection: {count_before}")

    if count_before == 0:
        print("ℹ️  Collection is already empty. Nothing to delete.")
        return

    confirm = input(f"\n⚠️  This will permanently delete ALL {count_before} user(s).\nType 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("❌ Aborted. No data was deleted.")
        return

    result = collection.delete_many({})
    print(f"\n✅ Deleted {result.deleted_count} document(s) from 'authentication'.")
    print("🎉 Collection cleared. You can now register fresh users.")

    client.close()

if __name__ == "__main__":
    clear_users()
