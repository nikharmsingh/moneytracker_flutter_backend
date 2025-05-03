# Money Tracker

A Flask-based web application for tracking personal finances, expenses, and income. Built with MongoDB for data storage.

## Features

- User authentication (login/register)
- Track expenses and income (CR/DR transactions)
- Categorize transactions
- View spending breakdown with interactive pie chart
- Track salary/income
- Calculate total balance
- Responsive design with Bootstrap
- MongoDB database integration

## Tech Stack

- **Backend**: Python, Flask
- **Database**: MongoDB
- **Frontend**: HTML, CSS, Bootstrap 5
- **Authentication**: Flask-Login
- **Data Visualization**: Chart.js

## Prerequisites

- Python 3.9 or higher
- MongoDB Atlas account (or local MongoDB instance)
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd money-tracker
```

2. Create and activate a virtual environment:
```bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following content:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
MONGODB_URI=your-mongodb-uri-here
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
money-tracker/
├── app.py              # Main application file
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── .gitignore         # Git ignore file
├── templates/         # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── add_expense.html
│   └── add_salary.html
└── static/            # Static files (CSS, JS, images)
```

## Usage

1. **Registration & Login**
   - Create a new account
   - Log in with your credentials

2. **Adding Transactions**
   - Click "Add Transaction" to add new expenses or income
   - Select transaction type (Credit/Debit)
   - Enter amount, category, and description
   - Choose date (defaults to current date)

3. **Viewing Transactions**
   - Dashboard shows summary cards
   - Interactive pie chart shows spending by category
   - Transaction list shows all entries
   - Delete transactions as needed

4. **Managing Salary**
   - Add salary entries
   - View total salary and balance
   - Delete salary entries

## Deployment

The application is configured for deployment on Render.com:

1. **Create a Render.com Account**
   - Sign up at [Render.com](https://render.com)
   - Connect your GitHub account

2. **Create a New Web Service**
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository
   - Select the branch to deploy (usually `main` or `master`)

3. **Configure the Service**
   - Name: `money-tracker` (or your preferred name)
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

4. **Set Environment Variables**
   - Click on "Environment" tab
   - Add the following variables:
     ```
     FLASK_APP=app.py
     FLASK_ENV=production
     MONGODB_URI=your-mongodb-uri-here
     ```
   - For `SECRET_KEY`, you can use Render's "Generate Value" feature
   - For `MONGODB_URI`, paste your MongoDB Atlas connection string

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically deploy your application
   - The deployment URL will be provided once complete

6. **Post-Deployment**
   - Monitor the deployment logs for any issues
   - Test the application using the provided URL
   - Set up automatic deployments for future updates

Note: Make sure your MongoDB Atlas database allows connections from Render's IP addresses. You may need to:
- Add `0.0.0.0/0` to your MongoDB Atlas IP whitelist
- Or add specific Render IP addresses to your whitelist

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask for the web framework
- MongoDB for the database
- Bootstrap for the UI components
- Chart.js for data visualization 