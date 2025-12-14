# Development Guidelines

## Code Quality Standards

### Python Backend Standards
- **Function Documentation**: Use triple-quoted docstrings for complex functions
- **Type Safety**: Implement robust type conversion with `to_py()` utility for JSON serialization
- **Error Handling**: Use try-catch blocks with informative error messages and fallback values
- **Global State Management**: Use module-level variables for shared data (DS1, DS2 datasets)
- **Path Management**: Use `os.path.join()` for cross-platform file path construction

### JavaScript Frontend Standards
- **Function Organization**: Group related functions with comment block separators
- **Async/Await Pattern**: Use async/await for all API calls with proper error handling
- **DOM Manipulation**: Cache DOM elements and use consistent class-based styling
- **Event Handling**: Use `addEventListener` for all event bindings
- **Loading States**: Implement loading overlays for all async operations

## Structural Conventions

### File Organization
- **Separation of Concerns**: Keep backend logic in `app.py`, frontend in `static/js/app.js`
- **Data Directory**: Store all models and datasets in dedicated `data/` folder
- **Template Structure**: Use single HTML template with JavaScript-driven content switching

### API Design Patterns
- **RESTful Endpoints**: Use descriptive URL patterns (`/api/student/search`, `/api/department/analyze`)
- **Consistent Response Format**: All endpoints return JSON with `success` boolean and optional `message`
- **Error Handling**: Return appropriate HTTP status codes (400 for client errors, 500 for server errors)
- **Request Validation**: Validate input data with fallback values using `get()` method

## Naming Conventions

### Python Variables
- **Snake Case**: Use lowercase with underscores (`student_row`, `past_avg`, `performance_model`)
- **Descriptive Names**: Use full words over abbreviations (`departments` not `depts`)
- **Constants**: Use uppercase for configuration values (`BASE_DIR`, `DATA_DIR`)

### JavaScript Variables
- **Camel Case**: Use camelCase for variables and functions (`currentStudent`, `analyseStudent`)
- **Global State**: Prefix global variables with descriptive context (`globalStats`, `currentStudentResult`)
- **DOM Elements**: Use descriptive IDs with hyphens (`student-report`, `loading-overlay`)

## Data Processing Patterns

### Pandas Operations
- **Safe Data Access**: Use `.get()` method with default values for dictionary access
- **Type Conversion**: Implement `safe_int()` utility for robust integer conversion
- **NaN Handling**: Check for NaN values using `pd.isna()` before processing
- **DataFrame Operations**: Use `.copy()` when modifying DataFrames to avoid side effects

### Feature Engineering
- **Weighted Calculations**: Use explicit weight coefficients for composite scores
- **Boundary Checking**: Validate division operations to prevent divide-by-zero errors
- **Rounding**: Apply consistent decimal precision using `round()` function

## Machine Learning Integration

### Model Loading
- **Safe Loading**: Use `safe_load()` utility with existence checks and exception handling
- **Model Validation**: Check model availability before making predictions
- **Fallback Responses**: Return "unknown" labels when models are unavailable

### Prediction Pipeline
- **Feature Vector**: Use numpy arrays with `.reshape(1, -1)` for single predictions
- **Label Encoding**: Use inverse_transform for converting numeric predictions to labels
- **Batch Processing**: Process multiple students in loops with individual error handling

## Frontend Architecture Patterns

### Single Page Application
- **Mode Switching**: Use CSS classes (`hidden`, `active`) for content visibility
- **State Management**: Maintain current context in global variables
- **Progressive Enhancement**: Build functionality in layers (basic → interactive → advanced)

### Chart Integration
- **Plotly Configuration**: Use consistent styling with transparent backgrounds
- **Chart Types**: Implement multiple visualization types (line, bar, pie, 3D, gauge)
- **Responsive Design**: Disable mode bar for cleaner presentation

## Security and Configuration

### Email Integration
- **SMTP Configuration**: Use environment variables for sensitive credentials (noted for improvement)
- **Error Handling**: Implement try-catch for email operations with user feedback
- **Rate Limiting**: Limit automated emails to prevent spam (max 5 alerts per batch)

### File Upload Security
- **File Type Validation**: Restrict uploads to CSV and XLSX formats only
- **Size Validation**: Check for empty files before processing
- **Path Security**: Use secure file handling with proper directory structure

## Performance Optimization

### Data Sampling
- **Large Dataset Handling**: Sample datasets over 500 records for college-wide analysis
- **Memory Management**: Use `.copy()` judiciously to balance safety and performance
- **Batch Operations**: Process multiple records efficiently in single operations

### Frontend Optimization
- **Lazy Loading**: Load charts and data only when needed
- **DOM Efficiency**: Minimize DOM queries by caching elements
- **Event Delegation**: Use efficient event handling patterns