#!/bin/bash

# Clear terminal
clear

# Print welcome message
echo "====================================="
echo "Simple Meme Site - Quick Start Script"
echo "====================================="
echo ""

# Print date and user info
current_date=$(date -u +"%Y-%m-%d %H:%M:%S")
echo "Current Date and Time (UTC): $current_date"
echo "Current User's Login: $(whoami)"
echo ""

# Check for existing MySQL containers
echo "Checking for existing MySQL containers..."
EXISTING_MYSQL=$(docker ps --filter "ancestor=mysql" --format "{{.ID}} | {{.Names}} | {{.Status}}")

use_existing=0
existing_container=""
if [ -n "$EXISTING_MYSQL" ]; then
    echo "Found existing MySQL containers:"
    echo "$EXISTING_MYSQL"
    echo ""
    read -p "Do you want to use an existing MySQL container? (y/n): " use_existing_response
    if [[ "$use_existing_response" =~ ^[Yy]$ ]]; then
        use_existing=1
        read -p "Enter the name of the MySQL container to use: " existing_container
        
        # Verify container exists
        if ! docker ps --format "{{.Names}}" | grep -q "^${existing_container}$"; then
            echo "Error: Container '$existing_container' not found."
            exit 1
        fi
        
        echo "Will use existing MySQL container: $existing_container"
    else
        echo "Will create a new MySQL container."
    fi
else
    echo "No existing MySQL containers found. Will create a new one."
fi

# Determine correct repository name
REPO_NAME="jakubcwiora/simple-meme-site"

# Check for GitHub Container Registry authentication
if ! docker pull ghcr.io/${REPO_NAME}:containerized &>/dev/null; then
    echo "Authentication needed for GitHub Container Registry"
    
    # Check for GITHUB_PAT environment variable first
    if [ -n "$GITHUB_PAT" ]; then
        echo "Using GITHUB_PAT environment variable..."
        if ! docker login ghcr.io -u "jakubcwiora" --password-stdin <<< "$GITHUB_PAT"; then
            echo "Authentication with GITHUB_PAT failed."
            echo "Let's try manual authentication..."
            GITHUB_PAT=""
        fi
    fi
    
    # If GITHUB_PAT didn't work or doesn't exist, prompt for credentials
    if [ -z "$GITHUB_PAT" ]; then
        read -p "GitHub Username: " GH_USER
        read -s -p "GitHub Personal Access Token: " GH_TOKEN
        echo ""
        
        # Login securely
        if ! docker login ghcr.io -u "$GH_USER" --password-stdin <<< "$GH_TOKEN"; then
            echo "Authentication failed. Please check your credentials."
            exit 1
        fi
        
        # Clear variables
        unset GH_TOKEN
    fi
    
    # Try pulling again after authentication
    if ! docker pull ghcr.io/${REPO_NAME}:containerized; then
        echo "Failed to pull image. Please check the repository name and tag."
        echo "Attempted to pull: ghcr.io/${REPO_NAME}:containerized"
        exit 1
    fi
fi

# Ask for database info or use defaults
read -p "MySQL User (default: memeuser): " DB_USER
DB_USER=${DB_USER:-memeuser}

read -s -p "MySQL Password (default: memepassword): " DB_PASSWORD
echo ""
DB_PASSWORD=${DB_PASSWORD:-memepassword}

read -p "MySQL Database Name (default: memes): " DB_NAME
DB_NAME=${DB_NAME:-memes}

if [ $use_existing -eq 0 ]; then
    read -s -p "MySQL Root Password (default: rootpassword): " MYSQL_ROOT_PASSWORD
    echo ""
    MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-rootpassword}
fi

echo ""
echo "Creating configuration..."

if [ $use_existing -eq 1 ]; then
    # Create docker-compose file without MySQL (using existing)
    cat > docker-compose.yml << EOF
services:
  web:
    image: ghcr.io/${REPO_NAME}:containerized
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=${existing_container}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
    network_mode: "container:${existing_container}"
    restart: always
EOF
else
    # Create docker-compose file with new MySQL instance
    cat > docker-compose.yml << EOF
services:
  web:
    image: ghcr.io/${REPO_NAME}:containerized
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=mysql
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
    depends_on:
      - mysql
    restart: always

  mysql:
    image: mysql:8.0
    command: --default-authentication-plugin=mysql_native_password
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${DB_NAME}
      - MYSQL_USER=${DB_USER}
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./schema.sql:/docker-entrypoint-initdb.d/schema.sql
    restart: always

volumes:
  mysql_data:
EOF
fi

echo "Starting Simple Meme Site..."
docker compose up -d

if [ $use_existing -eq 1 ]; then
    # Initialize database in existing container if schema.sql exists
    if [ -f schema.sql ]; then
        echo "Initializing database in existing container..."
        cat schema.sql | docker exec -i $existing_container mysql -u$DB_USER -p$DB_PASSWORD $DB_NAME
    fi
fi

echo ""
echo "====================================="
echo "Simple Meme Site is now running!"
echo "Access it at http://localhost:5000"
echo "====================================="
