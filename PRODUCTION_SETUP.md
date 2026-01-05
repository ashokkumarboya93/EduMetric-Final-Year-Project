# Production Database Setup for Vercel

## Option 1: PlanetScale (Recommended - Free)

1. Go to https://planetscale.com/
2. Sign up with GitHub
3. Create new database: "edumetric-db"
4. Get connection string from dashboard
5. Add to Vercel environment variables

## Option 2: Railway (Alternative - Free)

1. Go to https://railway.app/
2. Sign up with GitHub
3. Create MySQL database
4. Get connection details

## Option 3: Aiven (Alternative - Free tier)

1. Go to https://aiven.io/
2. Create MySQL service
3. Get connection string

## Environment Variables for Vercel:

DB_HOST=your-cloud-db-host
DB_NAME=edumetric_db
DB_USER=your-username
DB_PASSWORD=your-password
DB_PORT=3306
SECRET_KEY=your-production-secret-key