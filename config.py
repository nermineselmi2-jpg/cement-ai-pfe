import os

class Config:
    # رابط قاعدة البيانات (SQLite)
    # الملف سيتم إنشاؤه في مجلد instance تلقائياً
    SQLALCHEMY_DATABASE_URI = 'sqlite:///cement_secure.db'
    SECRET_KEY = 'super-secret-key-for-security'
    SQLALCHEMY_TRACK_MODIFICATIONS = False