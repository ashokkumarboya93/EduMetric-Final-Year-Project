# Project Structure

## Directory Organization

### Core Application
- **app.py**: Main Flask application with API routes and ML prediction logic
- **dashboard_file.Py**: Additional dashboard functionality

### Data Layer
- **data/**: Machine learning models and datasets
  - **DS1.csv**: Primary student dataset
  - **DS2_ml_ready.csv**: Preprocessed ML training data
  - **DS3_full_report.csv**: Comprehensive analysis results
  - **performance_model.pkl**: Trained performance prediction model
  - **risk_model.pkl**: Risk assessment model
  - **dropout_model.pkl**: Dropout prediction model
  - ***_label_encoder.pkl**: Label encoders for categorical data

### Frontend Assets
- **static/**: Client-side resources
  - **css/style.css**: Application styling
  - **js/app.js**: Frontend JavaScript functionality
- **templates/index.html**: Main web interface

### Configuration
- **requirements.txt**: Python dependencies
- **.env.example**: Environment configuration template
- **README.md**: Project documentation

### Development Files
- **Final_Year_Project_code.ipynb**: Jupyter notebook for model development
- **Student_PRD_dataset.csv**: Raw dataset for analysis

## Core Components

### Machine Learning Pipeline
- Feature engineering from student academic data
- Multi-model prediction system (performance, risk, dropout)
- Real-time scoring and classification

### Web Application
- Flask-based REST API
- Single-page application frontend
- Real-time data visualization

### Data Processing
- CSV/Excel file upload handling
- Data validation and cleaning
- Batch processing capabilities

## Architectural Patterns
- **MVC Architecture**: Clear separation of data, logic, and presentation
- **RESTful API Design**: Standardized endpoint structure
- **Model-View-Template**: Flask templating for frontend
- **Service Layer Pattern**: Centralized business logic in prediction functions