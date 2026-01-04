# EduMetric - Student Performance Analytics System

A comprehensive web-based analytics platform for predicting student performance, dropout risk, and academic outcomes using machine learning algorithms.

## Features

- **Performance Prediction**: Predict student academic performance based on various factors
- **Dropout Risk Assessment**: Identify students at risk of dropping out
- **Risk Analysis**: Comprehensive risk assessment for academic intervention
- **Interactive Dashboard**: User-friendly web interface for data input and visualization
- **Machine Learning Models**: Pre-trained models for accurate predictions

## Technology Stack

- **Backend**: Python Flask
- **Database**: MySQL
- **Machine Learning**: Scikit-learn, Pandas, NumPy
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: PythonAnywhere

## Project Structure

```
EduMetric-Final-Year-Project/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── db.py                 # Database connection and operations
├── wsgi.py              # WSGI configuration for deployment
├── requirements.txt      # Python dependencies
├── runtime.txt          # Python version specification
├── DEPLOYMENT.md        # Deployment instructions
├── data/                # Pre-trained ML models
│   ├── dropout_model.pkl
│   ├── dropout_label_encoder.pkl
│   ├── performance_model.pkl
│   ├── performance_label_encoder.pkl
│   ├── risk_model.pkl
│   └── risk_label_encoder.pkl
├── static/              # Static files (CSS, JS)
│   ├── css/
│   └── js/
└── templates/           # HTML templates
    └── index.html
```

## Installation & Setup

### Prerequisites

- Python 3.10+
- MySQL Server
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ashokkumarboya93/EduMetric-Final-Year-Project.git
   cd EduMetric-Final-Year-Project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MySQL database**
   ```sql
   CREATE DATABASE edumetric_db;
   ```

5. **Configure environment variables**
   Create a `.env` file in the project root:
   ```
   DB_HOST=localhost
   DB_NAME=edumetric_db
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_PORT=3306
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Home Page**: Navigate to the main dashboard
2. **Input Student Data**: Enter student information including:
   - Academic performance metrics
   - Demographic information
   - Behavioral indicators
3. **Get Predictions**: View predictions for:
   - Academic performance
   - Dropout risk
   - Overall risk assessment
4. **Analyze Results**: Review detailed analytics and recommendations

## Machine Learning Models

The system uses three pre-trained models:

- **Performance Model**: Predicts academic performance levels
- **Dropout Model**: Assesses dropout probability
- **Risk Model**: Evaluates overall academic risk

Models are stored in the `data/` directory and loaded automatically when the application starts.

## API Endpoints

- `GET /`: Main dashboard
- `POST /predict`: Submit student data for prediction
- `GET /health`: Application health check

## Deployment

For production deployment on PythonAnywhere, refer to [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

- **Author**: Ashok Kumar Boya
- **GitHub**: [ashokkumarboya93](https://github.com/ashokkumarboya93)
- **Project Repository**: [EduMetric-Final-Year-Project](https://github.com/ashokkumarboya93/EduMetric-Final-Year-Project)

## Acknowledgments

- Thanks to all contributors and supporters of this project
- Special thanks to the academic community for providing research insights
- Machine learning libraries: Scikit-learn, Pandas, NumPy

---

**Note**: This is a final year project developed for educational purposes and academic research in student performance analytics.