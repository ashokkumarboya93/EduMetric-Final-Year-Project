# EduMetric - Intelligent Student Performance Analytics

A comprehensive web-based analytics platform that predicts student academic performance, identifies at-risk students, and provides early intervention capabilities for educational institutions.

## 🎓 Features

- **Performance Prediction**: ML-powered prediction of student academic performance using historical data
- **Risk Assessment**: Identifies students at risk of poor performance or dropout
- **Dropout Prevention**: Early warning system for potential student dropouts
- **Department Analytics**: Comprehensive analysis by department and academic year
- **Individual Student Search**: Quick lookup and prediction for specific students
- **Batch Processing**: Upload and analyze multiple student records simultaneously
- **Alert System**: Automated email notifications to mentors for high-risk students
- **Interactive Dashboard**: Real-time visualizations and statistics
- **CRUD Operations**: Complete student data management system

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "Final Year"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## 🎯 How to Use

### Landing Page
- The application opens with a beautiful, educational-themed landing page
- Click **"Enter Dashboard"** to access the analytics platform directly
- No login credentials required - 100% open access

### Dashboard Features

#### 1. Student Analytics
- **Existing Student**: Search by register number, department, or year
- **New Student**: Add and analyze new student data with semester marks
- Get comprehensive performance predictions and risk assessments

#### 2. Department Analytics
- Select department and year filter
- View department-wide performance statistics
- Interactive charts with drill-down capabilities

#### 3. Year-wise Analytics
- Analyze entire academic year performance
- Cross-departmental insights and trends
- Performance distribution analysis

#### 4. Batch Analytics
- Cohort-based analysis by graduation year
- Semester trend analysis
- Batch-specific insights and recommendations

#### 5. College Analytics
- Institution-wide performance overview
- Sampling-based analysis for large datasets
- Strategic insights for college administration

#### 6. Batch Upload
- **Normalize Data**: Upload raw CSV/Excel files for processing
- **Analytics**: View processed data and generate insights
- Automated data cleaning and feature engineering

#### 7. CRUD Operations
- **Create**: Add new students to the system
- **Read**: Search and view student details
- **Update**: Modify existing student information
- **Delete**: Remove students from the database

## 📊 Analytics Capabilities

### Machine Learning Models
- **Performance Prediction**: Predicts academic performance levels (High/Medium/Poor)
- **Risk Assessment**: Identifies students at risk of academic failure
- **Dropout Prediction**: Early warning system for potential dropouts

### Interactive Visualizations
- Semester-wise performance trends
- Risk assessment radar charts
- Performance distribution donuts
- 3D scatter plots for multi-dimensional analysis
- Gauge charts for performance metrics

### Smart Insights
- AI-generated summaries and recommendations
- Automated intervention suggestions
- Risk-based alert systems
- Performance trend analysis

## 🔧 Technical Stack

- **Backend**: Python Flask 3.0.0
- **Data Processing**: Pandas 2.1.3, NumPy 1.26.2
- **Machine Learning**: Scikit-learn (via joblib)
- **Visualization**: Plotly 5.18.0
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Modern CSS with gradients and animations

## 📁 Project Structure

```
Final Year/
├── app.py                          # Main Flask application
├── dashboard_file.py               # Additional dashboard functionality
├── data/                           # ML models and datasets
│   ├── DS1.csv                     # Primary student dataset
│   ├── DS2_ml_ready.csv           # ML training data
│   ├── DS3_full_report.csv        # Analysis results
│   ├── performance_model.pkl       # Performance prediction model
│   ├── risk_model.pkl             # Risk assessment model
│   └── dropout_model.pkl          # Dropout prediction model
├── static/
│   ├── css/style.css              # Application styling
│   ├── js/app.js                  # Main application logic
│   └── js/landing.js              # Landing page functionality
├── templates/index.html            # Main web interface
└── requirements.txt               # Python dependencies
```

## 🎨 Design Features

### Landing Page
- Professional educational theme with blue and teal gradients
- Animated floating elements and smooth transitions
- Feature cards with hover effects and ripple animations
- Comprehensive about section with technology stack
- Statistics showcase and benefits overview
- Responsive design for all devices

### Dashboard
- Modern card-based layout with glassmorphism effects
- Interactive sidebar with mini-sidebar for mobile
- Comprehensive KPI displays with color-coded indicators
- Professional chart styling with consistent theming
- Responsive grid layouts for optimal viewing

## 📈 Data Processing

### Input Formats
- CSV files with student academic data
- Excel (.xlsx) files for batch uploads
- Manual data entry through web forms

### Feature Engineering
- Attendance percentage calculations
- Internal marks normalization
- Behavior score integration
- Semester-wise performance tracking
- Risk score computation

### Model Integration
- Real-time prediction pipeline
- Batch processing capabilities
- Model validation and fallback handling
- Label encoding for categorical predictions

## 🚨 Alert System

- Automated email notifications for high-risk students
- Customizable alert thresholds
- Mentor notification system
- Detailed alert reports with intervention suggestions

## 🔒 Security Features

- Input validation and sanitization
- File type restrictions for uploads
- Error handling with user-friendly messages
- Safe data processing with fallback values

## 📱 Responsive Design

- Mobile-first approach
- Tablet and desktop optimizations
- Touch-friendly interface elements
- Adaptive chart sizing and layouts

## 🎯 Target Users

- **Academic Administrators**: Monitor institutional performance
- **Faculty Members**: Track student progress
- **Student Mentors**: Receive alerts and provide support
- **Department Heads**: Analyze departmental trends

## 🔄 Future Enhancements

- Advanced ML model integration
- Real-time data streaming
- Mobile application development
- Advanced reporting features
- Integration with existing college management systems

## 📞 Support

For technical support or questions about the system, please refer to the comprehensive documentation within the application or contact the development team.

---

**EduMetric** - Empowering educational institutions with intelligent analytics for student success.