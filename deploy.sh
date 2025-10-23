#!/bin/bash

# CloudTasker Deployment Script
# This script automates the deployment process

set -e  # Exit on error

echo "=================================="
echo "CloudTasker Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file from .env.example"
    exit 1
fi

echo -e "${GREEN}Step 1: Installing dependencies...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}Step 2: Checking database connection...${NC}"
python -c "from config import db_config; import pymysql; pymysql.connect(**db_config); print('Database connection successful!')"

echo -e "${GREEN}Step 3: Creating/updating database tables...${NC}"
python -c "from app import init_db; init_db(); print('Database initialized!')"

echo -e "${GREEN}Step 4: Running application tests...${NC}"
# Add your test commands here
# python -m pytest tests/

echo -e "${GREEN}Step 5: Starting application...${NC}"
if [ "$1" == "production" ]; then
    echo "Starting in production mode with Gunicorn..."
    gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --daemon app:app
    echo -e "${GREEN}Application started on port 5000${NC}"
else
    echo "Starting in development mode..."
    python app.py
fi

echo "=================================="
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "=================================="