import pandas as pd
import matplotlib.pyplot as plt
from supabase_db import load_students_df

def run_analytics():
    """
    This function demonstrates how to fetch data from Supabase and perform
    some basic analytical operations.
    """
    print("Loading student data from Supabase...")
    students_df = load_students_df()

    if students_df.empty:
        print("No data available to perform analytics.")
        return

    print("\nFirst 5 rows of the student data:")
    print(students_df.head())

    # Example 1: Calculate the average performance of students in each department.
    print("\nCalculating average performance by department...")
    avg_performance_by_dept = students_df.groupby('DEPT')['PERFORMANCE_OVERALL'].mean()
    print("Average performance by department:")
    print(avg_performance_by_dept)

    # Example 2: Get the number of students at high risk of dropping out.
    print("\nCounting students at high risk of dropping out...")
    high_risk_students = students_df[students_df['DROPOUT_LABEL'] == 'high']
    num_high_risk_students = len(high_risk_students)
    print(f"Number of students at high risk of dropping out: {num_high_risk_students}")

    # Example 3: Visualize the distribution of students by year.
    print("\nGenerating a plot for the distribution of students by year...")
    year_distribution = students_df['YEAR'].value_counts()

    plt.figure(figsize=(10, 6))
    year_distribution.sort_index().plot(kind='bar')
    plt.title('Distribution of Students by Year')
    plt.xlabel('Year')
    plt.ylabel('Number of Students')
    plt.xticks(rotation=0)
    plt.savefig('student_distribution_by_year.png')
    print("Plot saved to student_distribution_by_year.png")

if __name__ == '__main__':
    run_analytics()
