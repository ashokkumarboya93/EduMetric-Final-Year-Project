# EduMetric - Student Performance Analytics System

A comprehensive AI-powered student performance analytics platform built with Flask and Supabase for predicting academic outcomes and identifying at-risk students.

## 🚀 Features

- **AI-Powered Predictions**: Machine learning models for performance, risk, and dropout prediction
- **Real-time Analytics**: Interactive dashboards for students, departments, and college-wide analysis
- **Smart Alerts**: Automated email notifications for at-risk students
- **Comprehensive Reports**: PDF export with visual charts and recommendations
- **Chat Assistant**: Natural language queries for analytics insights
- **CRUD Operations**: Complete student data management system

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: Supabase (PostgreSQL)
- **ML Models**: scikit-learn
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Chart.js, matplotlib
- **PDF Generation**: fpdf2
- **Deployment**: Vercel-ready

## 📋 Prerequisites

- Python 3.8+
- Supabase account
- Gmail account (for email alerts)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/edumetric.git
   cd edumetric
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   - Copy `.env.example` to `.env`
   - Get your Supabase credentials from: https://supabase.com/dashboard
   - Update `.env` with your actual values:
   ```env
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=your-supabase-anon-key
   EMAIL_USER=your-gmail@gmail.com
   EMAIL_PASSWORD=your-gmail-app-password
   ```

4. **Database Setup**
   - Create a `students` table in your Supabase database
   - Import sample data or use the batch upload feature

## 🚀 Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Access the application**
   - Open http://localhost:5000 in your browser

3. **Key Features**
   - **Student Search**: Enter roll number to get individual analytics
   - **Department Analysis**: Filter by department and year
   - **College Analytics**: Overall performance insights
   - **Chat Assistant**: Ask questions like "show top performers in CSE"
   - **Data Upload**: Batch import student data via CSV/Excel

## 📊 API Endpoints

### Student Operations
- `POST /api/student/search` - Search student by roll number
- `POST /api/student/predict` - Get AI predictions for student
- `POST /api/student/create` - Create new student record
- `POST /api/student/update` - Update student information
- `POST /api/student/delete` - Delete student record

### Analytics
- `GET /api/stats` - Get database statistics
- `POST /api/department/analyze` - Department-wise analysis
- `POST /api/year/analyze` - Year-wise analysis
- `GET /api/college/analyze` - College-wide analysis

### Advanced Features
- `POST /api/chat` - Natural language analytics queries
- `POST /api/export-report` - Generate PDF reports
- `POST /api/send-alert` - Send mentor alerts
- `POST /api/batch-upload` - Bulk data import

## 🤖 Machine Learning Models

The system uses three trained models:
- **Performance Prediction**: Classifies students as High/Medium/Low performers
- **Risk Assessment**: Identifies students at academic risk
- **Dropout Prediction**: Predicts likelihood of student dropout

Models are trained on features including:
- Past semester performance
- Attendance patterns
- Internal assessment scores
- Behavioral indicators

## 📁 Project Structure

```
edumetric/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── db.py                 # Database operations
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── data/                 # ML models directory
│   ├── performance_model.pkl
│   ├── risk_model.pkl
│   └── dropout_model.pkl
├── templates/
│   └── index.html        # Main frontend template
├── static/
│   ├── css/
│   └── js/
└── README.md
```

## 🔮 Sample Usage

### Individual Student Analytics
```python
# Search for student
POST /api/student/search
{
    "rno": "22G31A3167"
}

# Get predictions
POST /api/student/predict
{
    "RNO": "22G31A3167",
    "SEM1": 85,
    "SEM2": 88,
    "INTERNAL_MARKS": 25,
    "ATTENDANCE_PCT": 90
}
```

### Chat Assistant
```
"Show top 5 performers in CSE department"
"Analytics for 22G31A3167"
"High risk students in 3rd year"
"Department comparison"
```

## 🚀 Deployment

### Vercel Deployment
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="your-url"
export SUPABASE_KEY="your-key"

# Run application
python app.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Built for Final Year Project
- Inspired by the need for proactive student support systems
- Thanks to the open-source community for the amazing tools

## 📞 Support

For support, email your-email@example.com or create an issue in this repository.

---

**EduMetric** - Empowering Education Through Analytics 🎓