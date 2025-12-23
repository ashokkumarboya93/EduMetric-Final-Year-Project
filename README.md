# EduMetric - Student Performance Analytics System

A comprehensive Flask-based web application for student performance prediction and analytics using machine learning models.

## 🚀 Features

### Core Functionality
- **Student Performance Prediction**: ML-powered predictions for academic performance, risk assessment, and dropout probability
- **Real-time Analytics Dashboard**: Interactive visualizations and insights
- **CRUD Operations**: Complete Create, Read, Update, Delete functionality for student records
- **Batch Data Processing**: Upload and process CSV/Excel files with student data
- **Email Alerts**: Automated mentor notifications for at-risk students
- **PDF Reports**: Generate comprehensive analytics reports with charts

### Analytics Capabilities
- **Individual Student Analysis**: Detailed performance breakdown and predictions
- **Department Analytics**: Department-wise performance insights
- **Year/Batch Analysis**: Cohort-based analytics and trends
- **College-wide Overview**: Institution-level performance metrics
- **Risk Assessment**: Early identification of at-risk students
- **Dropout Prediction**: Proactive intervention for potential dropouts

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Machine Learning**: scikit-learn, pandas, numpy
- **Data Processing**: pandas, joblib
- **Visualization**: matplotlib, plotly
- **PDF Generation**: fpdf
- **Database**: MySQL (optional), CSV-based storage
- **Email**: SMTP integration

## 📁 Project Structure

```
EduMetric-Final-Year-Project/
├── app.py                      # Main Flask application
├── db.py                       # Database configuration
├── migrate_csv_to_mysql.py     # Database migration utility
├── requirements.txt            # Python dependencies
├── data/                       # Data and ML models
│   ├── DS1.csv                # Raw student data
│   ├── DS3_full_report.csv    # Analytics-ready dataset
│   ├── performance_model.pkl   # Performance prediction model
│   ├── risk_model.pkl         # Risk assessment model
│   ├── dropout_model.pkl      # Dropout prediction model
│   └── *_label_encoder.pkl    # Label encoders for models
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css          # Application styles
│   └── js/
│       └── app.js             # Frontend JavaScript
└── templates/
    └── index.html             # Main dashboard template
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ashokkumarboya93/EduMetric-Final-Year-Project.git
   cd EduMetric-Final-Year-Project
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the dashboard**
   Open your browser and navigate to: `http://127.0.0.1:5000`

## 📊 Usage Guide

### Dashboard Navigation
- **Student Search**: Search and analyze individual student performance
- **Department Analytics**: View department-wise performance metrics
- **Year Analysis**: Analyze year/batch performance trends
- **College Overview**: Institution-wide analytics and insights
- **Data Management**: Upload, update, and manage student records

### Key Features

#### 1. Student Performance Prediction
- Enter student details (attendance, marks, behavior scores)
- Get AI-powered predictions for:
  - Academic performance level (High/Medium/Poor)
  - Risk assessment (Low/Medium/High)
  - Dropout probability (Low/Medium/High)

#### 2. Batch Data Upload
- Upload CSV/Excel files with student data
- Automatic data normalization and prediction generation
- Support for both raw data and pre-processed analytics data

#### 3. Analytics Dashboard
- Interactive charts and visualizations
- Drill-down capabilities for detailed analysis
- Export functionality for reports and data

#### 4. Alert System
- Automated email alerts for at-risk students
- Customizable alert criteria
- Mentor notification system

## 🔧 Configuration

### Email Configuration
Update the email settings in `app.py`:
```python
FROM = "your-email@gmail.com"
PASS = "your-app-password"  # Use app-specific password for Gmail
```

### Database Configuration (Optional)
For MySQL integration, update `db.py` with your database credentials:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your-username',
    'password': 'your-password',
    'database': 'edumetric'
}
```

## 📈 Machine Learning Models

The system uses three main ML models:

1. **Performance Model**: Predicts academic performance levels
2. **Risk Model**: Assesses academic risk factors
3. **Dropout Model**: Predicts dropout probability

### Model Features
- Past semester averages
- Internal assessment scores
- Attendance percentages
- Behavior scores
- Performance trends

## 🎯 API Endpoints

### Student Operations
- `POST /api/student/search` - Search student by RNO
- `POST /api/student/predict` - Get ML predictions
- `POST /api/student/create` - Create new student
- `POST /api/student/update` - Update student record
- `POST /api/student/delete` - Delete student record

### Analytics
- `GET /api/stats` - Get basic statistics
- `POST /api/department/analyze` - Department analytics
- `POST /api/year/analyze` - Year-wise analysis
- `GET /api/college/analyze` - College-wide analytics
- `POST /api/batch/analyze` - Batch performance analysis

### Data Management
- `POST /api/batch-upload` - Upload CSV/Excel files
- `POST /api/export-report` - Generate PDF reports
- `POST /api/send-alert` - Send email alerts

## 🔍 Testing

### Local Testing Checklist
✅ **Dashboard loads successfully**
- Navigate to `http://127.0.0.1:5000`
- Verify all sections are visible

✅ **Data is visible**
- Check student statistics
- Verify department and year filters work

✅ **CRUD operations work**
- Test student search functionality
- Try creating, updating, and deleting records
- Upload sample CSV file

### Sample Test Data
The system includes sample student data in `data/DS3_full_report.csv` for testing purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Ashok Kumar Boya** - *Initial work* - [ashokkumarboya93](https://github.com/ashokkumarboya93)

## 🙏 Acknowledgments

- Machine Learning models trained on synthetic student performance data
- Flask framework for rapid web development
- scikit-learn for ML model implementation
- Chart.js and matplotlib for data visualization

## 📞 Support

For support, email ashokkumarboya93@gmail.com or create an issue in the GitHub repository.

---

**EduMetric** - Empowering Educational Institutions with Data-Driven Insights 🎓