import os
from dotenv import load_dotenv
from pymongo import MongoClient
from utils_path import resource_path

load_dotenv(resource_path('.env'), override=True)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "AppBaiDoXe")

class MongoDB:
    _client = None
    _db = None

    @classmethod
    def get_db(cls):
        if cls._client is None:
            try:
                cls._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                cls._db = cls._client[DB_NAME]
                # Test kết nối
                cls._client.server_info()
                print(f"[+] Kết nối MongoDB thành công: {DB_NAME}")
            except Exception as e:
                print(f"[-] Không thể kết nối MongoDB: {e}")
                cls._client = None
                cls._db = None
        return cls._db

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            print("[*] Đã ngắt kết nối MongoDB")
