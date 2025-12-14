# Technology Stack

## Programming Languages
- **Python 3.x**: Primary backend language
- **JavaScript**: Frontend interactivity
- **HTML5/CSS3**: Web interface markup and styling

## Backend Framework
- **Flask 3.0.0**: Lightweight web framework
  - Route handling and API endpoints
  - Template rendering
  - Request/response processing

## Data Science & ML
- **pandas 2.1.3**: Data manipulation and analysis
- **numpy 1.26.2**: Numerical computing
- **joblib 1.3.2**: Model serialization and loading
- **scikit-learn**: Machine learning models (implied by pickle files)

## Visualization & Reporting
- **plotly 5.18.0**: Interactive data visualizations
- **fpdf 1.7.2**: PDF report generation

## Configuration Management
- **python-dotenv 1.0.0**: Environment variable management

## Development Commands

### Setup
```bash
pip install -r requirements.txt
```

### Run Application
```bash
python app.py
```

### Environment Configuration
- Copy `.env.example` to `.env`
- Configure email credentials for alert system
- Set database paths if needed

## File Formats Supported
- **CSV**: Primary data format for student records
- **Excel (.xlsx)**: Alternative upload format
- **Pickle (.pkl)**: Serialized ML models and encoders

## API Architecture
- **RESTful endpoints**: JSON request/response format
- **POST/GET methods**: Standard HTTP operations
- **Error handling**: Structured error responses
- **File upload**: Multipart form data support

## Data Storage
- **CSV files**: Persistent data storage
- **In-memory processing**: pandas DataFrames
- **Model persistence**: joblib serialization