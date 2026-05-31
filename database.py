import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from utils_path import resource_path

def get_env_path():
    if getattr(sys, 'frozen', False):
        # Khi chạy bằng file .exe, file .env nằm cùng cấp với file .exe
        return os.path.join(os.path.dirname(sys.executable), '.env')
    else:
        # Khi chạy bằng mã nguồn, file .env nằm ở thư mục gốc
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), '.env')

load_dotenv(get_env_path(), override=True)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "AppBaiDoXe")

class MongoDB:
    _client = None
    _db = None
    _connection_failed = False  # Ghi nhớ trạng thái kết nối lỗi

    @classmethod
    def get_db(cls):
        if cls._connection_failed:
            return None
            
        if cls._client is None:
            try:
                # Giảm timeout xuống 2s để kiểm tra nhanh hơn
                cls._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
                cls._db = cls._client[DB_NAME]
                # Test kết nối
                cls._client.server_info()
                print(f"[+] Kết nối MongoDB thành công: {DB_NAME}")
            except Exception as e:
                print(f"[-] Không thể kết nối MongoDB: {e}. Hệ thống sẽ bỏ qua kết nối MongoDB ở các khung hình sau để tránh lag giao diện.")
                cls._client = None
                cls._db = None
                cls._connection_failed = True  # Đánh dấu đã lỗi kết nối
        return cls._db

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            print("[*] Đã ngắt kết nối MongoDB")
