import pandas as pd

def find_student_by_reg(df, reg_number):
    """Find student by registration number (unique identifier)"""
    return df[df.iloc[:, 0] == reg_number]

def check_duplicate_names(df):
    """Check for students with same names but different reg numbers"""
    name_col = df.columns[2]  # Name column
    duplicates = df[df.duplicated(subset=[name_col], keep=False)]
    return duplicates.groupby(name_col).size()

def safe_student_lookup(df, identifier):
    """Safe lookup using reg number as primary key"""
    # Always use reg number (first column) for unique identification
    result = df[df.iloc[:, 0] == identifier]
    return result if not result.empty else None

# Example usage
if __name__ == "__main__":
    df = pd.read_csv('data/DS3_full_report.csv')
    
    # Find specific student by reg number
    student = find_student_by_reg(df, '26G31B8805')
    print(f"Found: {student.iloc[0, 2] if not student.empty else 'Not found'}")
    
    # Check for name duplicates
    name_duplicates = check_duplicate_names(df)
    print(f"Students with duplicate names: {len(name_duplicates)}")