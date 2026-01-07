# EduMetric - Intelligent Student Performance Analytics

A comprehensive Machine Learning-powered platform for predicting student performance, identifying at-risk students, and enabling proactive educational interventions.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8 or higher
- Internet connection for Supabase
- Modern web browser

### 2. Installation
```bash
# Install required packages
pip install -r requirements.txt
```

### 3. Database Setup

#### Option A: Manual Supabase Setup (Recommended)
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the SQL script from `create_students_table.sql`
4. This will create the students table with sample data

#### Option B: Use Sample Data
1. Run the sample data generator:
```bash
python create_sample_data.py
```
2. Use the Batch Upload feature in the app to upload `sample_students.csv`

### 4. Configuration
Your `.env` file is already configured with Supabase credentials:
```
SUPABASE_URL=https://jmylnuhdxsbktbibjurv.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5. Run the Application
```bash
# Option 1: Use the startup script
python start_app.py

# Option 2: Run directly
python app.py
```

### 6. Access the Application
Open your browser and go to: http://localhost:5000

## 📊 Features

### Core Analytics
- **Student Performance Prediction**: AI-powered individual student analysis
- **Risk Assessment**: Early identification of at-risk students
- **Dropout Prevention**: Predictive modeling for student retention
- **Department Analytics**: Comprehensive departmental insights
- **Year-wise Analysis**: Cohort performance tracking
- **College-wide Reports**: Institution-level analytics

### Advanced Features
- **Batch Data Processing**: Upload and process large datasets
- **CRUD Operations**: Complete student data management
- **AI Chat Assistant**: Natural language analytics queries
- **Automated Alerts**: Email notifications for high-risk students
- **Interactive Dashboards**: Real-time visualizations
- **Export Capabilities**: PDF and CSV report generation

## 🎯 Usage Guide

### 1. Student Analytics
- **Existing Student**: Search by register number for instant analysis
- **New Student**: Add student details for prediction
- **Results**: View performance metrics, risk assessment, and recommendations

### 2. Department Analytics
- Select department and optional year filter
- View comprehensive departmental performance
- Identify trends and patterns

### 3. Batch Upload
- **Normalize Mode**: Upload raw student data for processing
- **Analytics Mode**: View processed data with predictions
- Supports CSV and Excel formats

### 4. CRUD Operations
- **Create**: Add new students to the database
- **Read**: Search and view student details
- **Update**: Modify existing student information
- **Delete**: Remove student records

### 5. AI Chat Assistant
- Ask natural language questions about analytics
- Examples:
  - "Show top performers in CSE"
  - "Who are the high-risk students?"
  - "Give me analytics for 22CSE001"

## 🔧 Technical Details

### Technology Stack
- **Backend**: Python Flask
- **Database**: Supabase (PostgreSQL)
- **ML Libraries**: Scikit-learn, Pandas, NumPy
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualization**: Plotly.js
- **Authentication**: Simple admin login

### Machine Learning Models
- **Performance Prediction**: Multi-feature regression model
- **Risk Assessment**: Classification model for academic risk
- **Dropout Prediction**: Binary classification for retention
- **Feature Engineering**: Automated calculation of performance metrics

### Data Processing
- Automated data normalization
- Feature extraction from academic records
- Real-time prediction generation
- Comprehensive analytics computation

## 📁 Project Structure
```
EduMetric/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── db.py                 # Supabase database operations
├── supabase_db.py        # Alternative database interface
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── data/                 # ML models and encoders
├── static/               # CSS and JavaScript files
├── templates/            # HTML templates
├── sample_students.csv   # Sample data for testing
└── create_students_table.sql # Database setup script
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify Supabase credentials in `.env`
   - Check internet connection
   - Ensure students table exists

2. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **No Student Data**
   - Run SQL script in Supabase
   - Upload sample data via Batch Upload
   - Create students manually via CRUD

4. **Port Already in Use**
   - Change port in `app.py`: `app.run(port=5001)`
   - Or kill existing process

### Verification Steps
```bash
# Test setup
python verify_setup.py

# Create sample data
python create_sample_data.py

# Start application
python start_app.py
```

## 🔐 Security Notes

- Default admin credentials: `admin` / `admin123`
- Change credentials in production
- Supabase RLS policies are enabled
- Environment variables store sensitive data

## 📈 Performance Optimization

- Database indexes on key fields
- Batch processing for large datasets
- Efficient ML model loading
- Optimized frontend rendering

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all setup steps
3. Ensure database connectivity
4. Review console logs for errors

## 📄 License

This is a Final Year Academic Project for educational purposes.

---

**EduMetric** - Transforming Education Through Intelligent Analytics