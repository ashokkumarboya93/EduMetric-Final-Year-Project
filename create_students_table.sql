-- EduMetric Students Table Creation Script
-- Run this in Supabase SQL Editor to create the students table

-- Create the students table
CREATE TABLE IF NOT EXISTS public.students (
    id SERIAL PRIMARY KEY,
    rno VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    dept VARCHAR(100),
    year INTEGER,
    curr_sem INTEGER,
    batch_year INTEGER,
    sem1 DECIMAL(5,2) DEFAULT 0,
    sem2 DECIMAL(5,2) DEFAULT 0,
    sem3 DECIMAL(5,2) DEFAULT 0,
    sem4 DECIMAL(5,2) DEFAULT 0,
    sem5 DECIMAL(5,2) DEFAULT 0,
    sem6 DECIMAL(5,2) DEFAULT 0,
    sem7 DECIMAL(5,2) DEFAULT 0,
    sem8 DECIMAL(5,2) DEFAULT 0,
    internal_marks DECIMAL(5,2) DEFAULT 20,
    total_days_curr DECIMAL(5,2) DEFAULT 90,
    attended_days_curr DECIMAL(5,2) DEFAULT 80,
    prev_attendance_perc DECIMAL(5,2) DEFAULT 85,
    behavior_score_10 DECIMAL(5,2) DEFAULT 7,
    mentor VARCHAR(255),
    mentor_email VARCHAR(255),
    performance_overall DECIMAL(5,2),
    performance_label VARCHAR(20),
    risk_score DECIMAL(5,2),
    risk_label VARCHAR(20),
    dropout_score DECIMAL(5,2),
    dropout_label VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (for development)
CREATE POLICY "Allow all operations on students" ON public.students
    FOR ALL USING (true) WITH CHECK (true);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_rno ON public.students(rno);
CREATE INDEX IF NOT EXISTS idx_students_dept ON public.students(dept);
CREATE INDEX IF NOT EXISTS idx_students_year ON public.students(year);
CREATE INDEX IF NOT EXISTS idx_students_performance ON public.students(performance_label);
CREATE INDEX IF NOT EXISTS idx_students_risk ON public.students(risk_label);

-- Insert sample data (optional)
INSERT INTO public.students (rno, name, email, dept, year, curr_sem, batch_year, sem1, sem2, sem3, sem4, internal_marks, total_days_curr, attended_days_curr, prev_attendance_perc, behavior_score_10, mentor, mentor_email, performance_overall, performance_label, risk_score, risk_label, dropout_score, dropout_label) VALUES
('22CSE001', 'John Doe', 'john.doe@college.edu', 'CSE', 3, 5, 2022, 85, 88, 82, 90, 25, 90, 85, 90, 8, 'Dr. Smith', 'smith@college.edu', 85.5, 'high', 15.2, 'low', 12.8, 'low'),
('22ECE002', 'Jane Smith', 'jane.smith@college.edu', 'ECE', 2, 3, 2022, 78, 82, 75, 0, 22, 90, 80, 85, 7, 'Dr. Johnson', 'johnson@college.edu', 78.3, 'medium', 25.4, 'medium', 18.7, 'medium'),
('22MECH003', 'Bob Wilson', 'bob.wilson@college.edu', 'MECH', 4, 7, 2022, 92, 89, 94, 91, 28, 90, 88, 92, 9, 'Dr. Brown', 'brown@college.edu', 91.2, 'high', 8.9, 'low', 7.3, 'low'),
('22CSE004', 'Alice Johnson', 'alice.johnson@college.edu', 'CSE', 1, 1, 2022, 65, 0, 0, 0, 18, 90, 70, 75, 6, 'Dr. Davis', 'davis@college.edu', 65.8, 'medium', 35.2, 'high', 28.4, 'high'),
('22IT005', 'Charlie Brown', 'charlie.brown@college.edu', 'IT', 2, 4, 2022, 88, 85, 87, 89, 26, 90, 82, 88, 8, 'Dr. Wilson', 'wilson@college.edu', 87.1, 'high', 12.7, 'low', 10.9, 'low');

-- Verify the table was created
SELECT COUNT(*) as total_students FROM public.students;
SELECT DISTINCT dept FROM public.students ORDER BY dept;
SELECT DISTINCT year FROM public.students ORDER BY year;