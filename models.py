from flask_login import UserMixin
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI'))
db = client.money_tracker

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.password = user_data['password']

    @staticmethod
    def get(user_id):
        user_data = db.users.find_one({'_id': ObjectId(user_id)})
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_email(email):
        user_data = db.users.find_one({'email': email})
        return User(user_data) if user_data else None

    @staticmethod
    def create(email, password):
        user_data = {
            'email': email,
            'password': password
        }
        result = db.users.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        return User(user_data)

class Expense:
    def __init__(self, expense_data):
        self.id = str(expense_data['_id'])
        self.amount = expense_data['amount']
        self.category = expense_data['category']
        self.description = expense_data.get('description', '')
        self.date = expense_data['date']
        self.transaction_type = expense_data['transaction_type']
        self.user_id = expense_data['user_id']
        self.timestamp = expense_data.get('timestamp')

    @staticmethod
    def create(amount, category, description, date, transaction_type, user_id):
        expense_data = {
            'amount': amount,
            'category': category,
            'description': description,
            'date': date,
            'transaction_type': transaction_type,
            'user_id': user_id,
            'timestamp': datetime.utcnow(),
        }
        result = db.expenses.insert_one(expense_data)
        expense_data['_id'] = result.inserted_id
        return Expense(expense_data)

    @staticmethod
    def get_by_user(user_id):
        expenses = db.expenses.find({'user_id': user_id}).sort('date', -1)
        return [Expense(expense) for expense in expenses]

    @staticmethod
    def delete(expense_id, user_id):
        db.expenses.delete_one({'_id': ObjectId(expense_id), 'user_id': user_id})

class Salary:
    def __init__(self, salary_data):
        self.id = str(salary_data['_id'])
        self.amount = salary_data['amount']
        self.date = salary_data['date']
        self.user_id = salary_data['user_id']

    @staticmethod
    def create(amount, date, user_id):
        salary_data = {
            'amount': amount,
            'date': date,
            'user_id': user_id
        }
        result = db.salaries.insert_one(salary_data)
        salary_data['_id'] = result.inserted_id
        return Salary(salary_data)

    @staticmethod
    def get_by_user(user_id):
        salaries = db.salaries.find({'user_id': user_id}).sort('date', -1)
        return [Salary(salary) for salary in salaries]

    @staticmethod
    def delete(salary_id, user_id):
        db.salaries.delete_one({'_id': ObjectId(salary_id), 'user_id': user_id})

class Category:
    @staticmethod
    def get_by_user(user_id):
        # Ensure user_id is an ObjectId
        if not isinstance(user_id, ObjectId):
            try:
                user_id = ObjectId(user_id)
            except Exception:
                pass
        # Return both global and user categories
        return list(db.categories.find({
            '$or': [
                {'is_global': True},
                {'user_id': user_id, 'is_global': False}
            ]
        }))

    @staticmethod
    def create(name, user_id=None, is_global=False):
        doc = {'name': name, 'is_global': is_global}
        if not is_global:
            # Convert user_id to ObjectId if it's not already
            if user_id and not isinstance(user_id, ObjectId):
                try:
                    user_id = ObjectId(user_id)
                except Exception:
                    pass
            doc['user_id'] = user_id
        result = db.categories.insert_one(doc)
        return str(result.inserted_id)

    @staticmethod
    def delete(category_id, user_id):
        db.categories.delete_one({'_id': ObjectId(category_id), 'user_id': user_id}) 