from flask import Flask, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Expense, Salary, db, Category
from flask_cors import CORS
import jwt
from functools import wraps
from bson import ObjectId

app = Flask(__name__)
CORS(app, 
     supports_credentials=True,
     resources={r"/api/*": {
         "origins": "*",  # Allow all origins
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "expose_headers": ["Content-Type", "Authorization"],
         "max_age": 3600
     }}
)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'message': 'Unauthorized access'}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

login_manager = LoginManager()
login_manager.init_app(app)

def generate_token(user):
    try:
        payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }
        app.logger.debug(f"Generating token with payload: {payload}")
        token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        app.logger.debug(f"Generated token: {token}")
        return token
    except Exception as e:
        app.logger.error(f"Error generating token: {str(e)}")
        raise

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            payload = jwt.decode(
                token,
                app.config['JWT_SECRET_KEY'],
                algorithms=['HS256'],
                options={
                    'verify_signature': True,
                    'verify_exp': True,
                    'require': ['exp', 'user_id', 'email']
                }
            )
            user = User.get(payload['user_id'])
            if not user:
                return jsonify({'message': 'User not found'}), 401
            return f(user, *args, **kwargs)
        except Exception as e:
            app.logger.error(f"Token validation error: {str(e)}")
            return jsonify({'message': 'Invalid token'}), 401
            
    return decorated

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.get_by_email(email)
    
    if user and check_password_hash(user.password, password):
        token = generate_token(user)
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'token': token
        })
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    
    # Validate email format
    if not email or '@' not in email or '.' not in email:
        return jsonify({'message': 'Invalid email format'}), 400
    
    # Validate username
    if not username or len(username) < 3:
        return jsonify({'message': 'Username must be at least 3 characters long'}), 400
    
    if not password or len(password) < 6:
        return jsonify({'message': 'Password must be at least 6 characters long'}), 400
    
    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400
    
    if User.get_by_email(email):
        return jsonify({'message': 'Email already exists'}), 400
    
    if User.get_by_username(username):
        return jsonify({'message': 'Username already exists'}), 400
    
    hashed_password = generate_password_hash(password)
    user = User.create(email, username, hashed_password)
    
    token = generate_token(user)
    return jsonify({
        'message': 'Registration successful',
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username
        },
        'token': token
    }), 201

@app.route('/api/logout', methods=['POST'])
@token_required
def logout(user):
    return jsonify({'message': 'Logout successful'})

@app.route('/api/dashboard', methods=['GET'])
@token_required
def get_dashboard(user):
    try:
        app.logger.info(f"Fetching dashboard data for user: {user.email}")
        expenses = Expense.get_by_user(user.id)
        app.logger.debug(f"Found {len(expenses)} expenses")

        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year

        # Filter expenses for current month
        current_month_expenses = [
            expense for expense in expenses
            if expense.date.month == current_month and expense.date.year == current_year
        ]

        total_credit = sum(expense.amount for expense in current_month_expenses if expense.transaction_type == 'CR')
        total_debit = sum(expense.amount for expense in current_month_expenses if expense.transaction_type == 'DR')

        days_in_month = current_date.day
        avg_daily_spend = total_debit / days_in_month if days_in_month > 0 else 0

        # Calculate category-wise spending for current month
        category_spending = {}
        for expense in current_month_expenses:
            if expense.transaction_type == 'DR':
                category = expense.category
                if category not in category_spending:
                    category_spending[category] = 0
                category_spending[category] += expense.amount

        response_data = {
            'total_credit': total_credit,
            'total_debit': total_debit,
            'avg_daily_spend': avg_daily_spend,
            'current_month_name': current_date.strftime('%B %Y'),
            'category_spending': category_spending,
            'expenses': [{
                'id': expense.id,
                'amount': expense.amount,
                'category': expense.category,
                'description': expense.description,
                'date': expense.date.isoformat(),
                'transaction_type': expense.transaction_type,
                'timestamp': expense.timestamp.isoformat() if expense.timestamp else None
            } for expense in expenses]
        }
        app.logger.debug(f"Dashboard response data: {response_data}")

        return jsonify(response_data)
    except Exception as e:
        app.logger.error(f"Error fetching dashboard data: {str(e)}", exc_info=True)
        return jsonify({'message': 'Error fetching dashboard data', 'error': str(e)}), 500

@app.route('/api/expenses', methods=['POST'])
@token_required
def add_expense(user):
    try:
        app.logger.info(f"Adding expense for user: {user.email}")
        data = request.get_json()
        app.logger.debug(f"Request data: {data}")
        
        if not data:
            app.logger.error("No data provided in request")
            return jsonify({'message': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['amount', 'category', 'date', 'transaction_type']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            app.logger.error(f"Missing required fields: {missing_fields}")
            return jsonify({
                'message': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400

        # Validate and convert amount
        try:
            amount = float(data['amount'])
            app.logger.debug(f"Amount validated: {amount}")
        except (ValueError, TypeError):
            app.logger.error(f"Invalid amount value: {data['amount']}")
            return jsonify({'message': 'Invalid amount value'}), 400

        # Validate transaction type
        if data['transaction_type'] not in ['CR', 'DR']:
            app.logger.error(f"Invalid transaction type: {data['transaction_type']}")
            return jsonify({
                'message': 'Invalid transaction type',
                'valid_types': ['CR', 'DR']
            }), 400

        # Validate and parse date
        try:
            date = datetime.fromisoformat(data['date'])
            app.logger.debug(f"Date validated: {date}")
        except (ValueError, TypeError):
            app.logger.error(f"Invalid date format: {data['date']}")
            return jsonify({'message': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400

        # Get optional fields with defaults
        category = data['category']
        description = data.get('description', '')
        
        app.logger.info(f"Creating expense: amount={amount}, category={category}, date={date}, type={data['transaction_type']}")
        expense = Expense.create(amount, category, description, date, data['transaction_type'], user.id)
        app.logger.info(f"Expense created successfully with ID: {expense.id}")
        
        return jsonify({
            'message': 'Expense added successfully',
            'expense': {
                'id': expense.id,
                'amount': expense.amount,
                'category': expense.category,
                'description': expense.description,
                'date': expense.date.isoformat(),
                'transaction_type': expense.transaction_type,
                'timestamp': expense.timestamp.isoformat() if expense.timestamp else None
            }
        }), 201
    except Exception as e:
        app.logger.error(f"Error adding expense: {str(e)}", exc_info=True)
        return jsonify({'message': 'Error adding expense', 'error': str(e)}), 500

@app.route('/api/salary', methods=['POST'])
@token_required
def add_salary(user):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['amount', 'date']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'message': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400

        # Validate and convert amount
        try:
            amount = float(data['amount'])
        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid amount value'}), 400

        # Validate and parse date
        try:
            date = datetime.fromisoformat(data['date'])
        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
        
        salary = Salary.create(amount, date, user.id)
        
        return jsonify({
            'message': 'Salary added successfully',
            'salary': {
                'id': salary.id,
                'amount': salary.amount,
                'date': salary.date.isoformat()
            }
        }), 201
    except Exception as e:
        app.logger.error(f"Error adding salary: {str(e)}")
        return jsonify({'message': 'Error adding salary', 'error': str(e)}), 500

@app.route('/api/expenses/<id>', methods=['DELETE'])
@token_required
def delete_expense(user, id):
    Expense.delete(id, user.id)
    return jsonify({'message': 'Expense deleted successfully'})

@app.route('/api/salary/<id>', methods=['DELETE'])
@token_required
def delete_salary(user, id):
    Salary.delete(id, user.id)
    return jsonify({'message': 'Salary deleted successfully'})

@app.route('/api/salary/visualization', methods=['GET'])
@token_required
def get_salary_visualization(user):
    salaries = Salary.get_by_user(user.id)
    expenses = Expense.get_by_user(user.id)
    
    # Group salaries by month
    monthly_salaries = {}
    for salary in salaries:
        month = salary.date.strftime('%Y-%m')
        if month not in monthly_salaries:
            monthly_salaries[month] = 0
        monthly_salaries[month] += salary.amount
    
    # Sort by month
    sorted_months = sorted(monthly_salaries.keys())
    
    # Get current month data
    current_date = datetime.now()
    current_month = current_date.strftime('%Y-%m')
    
    current_month_salary = monthly_salaries.get(current_month, 0)
    current_month_credits = sum(
        expense.amount for expense in expenses 
        if expense.date.strftime('%Y-%m') == current_month 
        and expense.transaction_type == 'CR'
    )
    current_month_debits = sum(
        expense.amount for expense in expenses 
        if expense.date.strftime('%Y-%m') == current_month 
        and expense.transaction_type == 'DR'
    )
    
    return jsonify({
        'salary_data': {
            'months': [datetime.strptime(month, '%Y-%m').strftime('%b %Y') for month in sorted_months],
            'amounts': [monthly_salaries[month] for month in sorted_months]
        },
        'current_salary': current_month_salary,
        'current_month_name': current_date.strftime('%B %Y'),
        'total_credits': current_month_credits,
        'total_debits': current_month_debits
    })

@app.route('/api/health')
def health_check():
    try:
        db.command('ping')
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    health_data = {
        "status": "up",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "version": "1.0.0"
    }
    
    return jsonify(health_data)

@app.route('/api/categories', methods=['GET'])
@token_required
def get_categories(user):
    try:
        # Ensure user_id is ObjectId
        user_obj_id = ObjectId(user.id) if not isinstance(user.id, ObjectId) else user.id
        categories = Category.get_by_user(user_obj_id)
        app.logger.info(f"Fetched categories for user {user.id}: {categories}")
        return jsonify([{
            'id': str(cat['_id']), 
            'name': cat['name'],
            'is_global': cat.get('is_global', False)
        } for cat in categories])
    except Exception as e:
        app.logger.error(f"Error fetching categories: {e}")
        return jsonify({'message': 'Error fetching categories', 'error': str(e)}), 500

@app.route('/api/categories', methods=['POST'])
@token_required
def add_category(user):
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'message': 'Category name is required'}), 400
    cat_id = Category.create(name, user.id, is_global=False)
    return jsonify({'id': cat_id, 'name': name, 'is_global': False}), 201

@app.route('/api/categories/<id>', methods=['DELETE'])
@token_required
def delete_category(user, id):
    try:
        cat = db.categories.find_one({'_id': ObjectId(id)})
        if not cat:
            return jsonify({'message': 'Category not found'}), 404
        if cat.get('is_global', False):
            return jsonify({'message': 'Cannot delete global category'}), 403
        
        # Convert both IDs to string for comparison
        category_user_id = str(cat.get('user_id'))
        current_user_id = str(user.id)
        
        if category_user_id != current_user_id:
            return jsonify({'message': 'You can only delete your own categories'}), 403
            
        Category.delete(id, user.id)
        return jsonify({'message': 'Category deleted successfully'})
    except Exception as e:
        app.logger.error(f"Error deleting category: {e}")
        return jsonify({'message': 'Error deleting category', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 