-- Create the students table with the exact structure from your data
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
    internal_pct DECIMAL(5,2) DEFAULT 66.67,
    attendance_pct DECIMAL(5,2) DEFAULT 86.22,
    behavior_pct DECIMAL(5,2) DEFAULT 70.0,
    performance_overall DECIMAL(5,2),
    performance_label VARCHAR(20),
    risk_score DECIMAL(5,2),
    risk_label VARCHAR(20),
    dropout_score DECIMAL(5,2),
    dropout_label VARCHAR(20),
    past_avg DECIMAL(5,2),
    past_count INTEGER,
    performance_trend DECIMAL(5,2),
    present_att DECIMAL(5,2),
    prev_att DECIMAL(5,2),
    internal_marks DECIMAL(5,2) DEFAULT 20,
    total_days_curr DECIMAL(5,2) DEFAULT 90,
    attended_days_curr DECIMAL(5,2) DEFAULT 80,
    prev_attendance_perc DECIMAL(5,2) DEFAULT 85,
    behavior_score_10 DECIMAL(5,2) DEFAULT 7,
    mentor VARCHAR(255),
    mentor_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enable Row Level Security
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

-- Insert your existing data (sample from what you provided)
INSERT INTO public.students (
    rno, name, email, dept, year, curr_sem, batch_year, sem1, 
    internal_pct, attendance_pct, behavior_pct, performance_overall, 
    performance_label, risk_score, risk_label, dropout_score, dropout_label,
    past_avg, past_count, performance_trend, present_att, prev_att,
    internal_marks, total_days_curr, attended_days_curr, prev_attendance_perc, behavior_score_10
) VALUES 
('23G31B9891', 'Ramesh Malhotra', 'ramesh.malhotra763@gmail.com', 'CIVIL', 1, 2, 2028, 72, 66.67, 86.22, 70.0, 72.43, 'high', 27.57, 'low', 18.78, 'low', 72.0, 1, 0.0, 88.89, 85.0, 20, 90, 80, 85, 7),
('23G31B4787', 'Anjali Agarwal', 'anjali.agarwal608@gmail.com', 'CIVIL', 1, 2, 2028, 62, 66.67, 86.22, 70.0, 67.43, 'high', 32.57, 'low', 19.78, 'low', 62.0, 1, 0.0, 88.89, 85.0, 20, 90, 80, 85, 7),
('23G31A1497', 'Sanjay Verma', 'sanjay.verma396@gmail.com', 'CIVIL', 1, 2, 2028, 41, 66.67, 86.22, 70.0, 56.93, 'high', 43.07, 'normal', 21.88, 'low', 41.0, 1, 0.0, 88.89, 85.0, 20, 90, 80, 85, 7),
('23G31A1368', 'Meera Rao', 'meera.rao743@gmail.com', 'CSE', 1, 2, 2028, 92, 66.67, 86.22, 70.0, 82.43, 'high', 17.57, 'low', 16.78, 'low', 92.0, 1, 0.0, 88.89, 85.0, 20, 90, 80, 85, 7),
('23G31B8275', 'Ashok Menon', 'ashok.menon415@gmail.com', 'CSE(AI)', 1, 2, 2028, 79, 66.67, 86.22, 70.0, 75.93, 'high', 24.07, 'low', 18.08, 'low', 79.0, 1, 0.0, 88.89, 85.0, 20, 90, 80, 85, 7);

-- Verify the table was created and data inserted
SELECT COUNT(*) as total_students FROM public.students;
SELECT DISTINCT dept FROM public.students ORDER BY dept;
SELECT rno, name, dept, performance_label FROM public.students LIMIT 5;