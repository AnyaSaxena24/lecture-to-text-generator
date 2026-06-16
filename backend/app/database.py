import os
import json
import logging
import socket
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from bson import ObjectId

logger = logging.getLogger(__name__)

# --- Mock JSON Database fallback engine ---

class MockCollection:
    def __init__(self, name: str):
        self.name = name
        self.filename = os.path.join(os.getcwd(), f"db_{name}.json")
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                json.dump([], f)

    def _read(self) -> list:
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _write(self, data: list):
        try:
            with open(self.filename, "w") as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Failed writing to mock database file: {e}")

    async def insert_one(self, doc: dict):
        data = self._read()
        if "_id" not in doc:
            doc["_id"] = str(ObjectId())
        else:
            doc["_id"] = str(doc["_id"])
        data.append(doc)
        self._write(data)
        
        class InsertResult:
            inserted_id = doc["_id"]
        return InsertResult()

    async def find_one(self, query: dict) -> dict:
        data = self._read()
        for doc in data:
            match = True
            for k, v in query.items():
                val = str(v) if isinstance(v, ObjectId) else v
                if str(doc.get(k)) != str(val):
                    match = False
                    break
            if match:
                return doc
        return None

    def find(self, query: dict):
        data = self._read()
        results = []
        for doc in data:
            match = True
            for k, v in query.items():
                val = str(v) if isinstance(v, ObjectId) else v
                if str(doc.get(k)) != str(val):
                    match = False
                    break
            if match:
                results.append(doc)

        class MockCursor:
            def __init__(self, items):
                self.items = items
            def sort(self, key, direction=1):
                return self
            def __aiter__(self):
                self.index = 0
                return self
            async def __anext__(self):
                if self.index >= len(self.items):
                    raise StopAsyncIteration
                item = self.items[self.index]
                self.index += 1
                return item
        return MockCursor(results)

    async def update_one(self, query: dict, update: dict) -> bool:
        data = self._read()
        for doc in data:
            match = True
            for k, v in query.items():
                val = str(v) if isinstance(v, ObjectId) else v
                if str(doc.get(k)) != str(val):
                    match = False
                    break
            if match:
                if "$set" in update:
                    for uk, uv in update["$set"].items():
                        doc[uk] = uv
                self._write(data)
                return True
        return False

    async def delete_one(self, query: dict) -> bool:
        data = self._read()
        initial_len = len(data)
        data = [
            doc for doc in data 
            if not all(str(doc.get(k)) == str(str(v) if isinstance(v, ObjectId) else v) for k, v in query.items())
        ]
        self._write(data)
        return len(data) < initial_len


class MockDatabase:
    def __init__(self):
        self.lectures = MockCollection("lectures")
        self.users = MockCollection("users")


# --- Main Database Loader ---

class Database:
    client: AsyncIOMotorClient = None
    db = None
    is_mock: bool = False

db_instance = Database()

def is_mongodb_reachable(url_str: str) -> bool:
    """
    Performs a raw socket connection check to test if MongoDB port is reachable.
    Avoids loading async loop tasks or running threadpools.
    """
    try:
        # Extract host and port from connection string (e.g. mongodb://localhost:27017)
        netloc = url_str.split("://")[-1]
        host_port = netloc.split("/")[0]
        if "@" in host_port:
            host_port = host_port.split("@")[-1]
            
        parts = host_port.split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 27017
        
        # Open socket with 1.0 second timeout
        s = socket.create_connection((host, port), timeout=1.0)
        s.close()
        return True
    except Exception:
        return False

def get_database():
    if db_instance.db is None:
        if is_mongodb_reachable(settings.MONGODB_URL):
            try:
                logger.info(f"MongoDB port is reachable. Connecting to {settings.MONGODB_URL}...")
                db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL)
                db_instance.db = db_instance.client[settings.DATABASE_NAME]
                db_instance.is_mock = False
                logger.info("Successfully connected to live MongoDB server.")
            except Exception as e:
                logger.warning(f"Error initializing Motor client: {e}. Falling back to local JSON database.")
                db_instance.db = MockDatabase()
                db_instance.is_mock = True
        else:
            logger.warning(
                f"MongoDB server is unreachable at {settings.MONGODB_URL}.\n"
                "Falling back to local persistent JSON files (db_lectures.json, db_users.json)."
            )
            db_instance.db = MockDatabase()
            db_instance.is_mock = True
            
    return db_instance.db

def close_database():
    if db_instance.client is not None and not db_instance.is_mock:
        db_instance.client.close()
        db_instance.db = None
        db_instance.client = None
        logger.info("Closed MongoDB connection.")
