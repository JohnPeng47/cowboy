#!/bin/sh

# Function to display usage
usage() {
    echo "Usage: $0 <dbname> <password> [username] [remote_ip]"
    echo "  dbname: Name of the database to create (required)"
    echo "  password: Password for the user (required)"
    echo "  username: Name of the user to create (optional, defaults to 'postgres')"
    echo "  remote_ip: IP address for remote connections (optional)"
    exit 1
}

# Check if required arguments are provided
if [ $# -lt 2 ]; then
    echo "Error: Insufficient arguments"
    usage
fi

DB_NAME="$1"
DB_PASS="$2"
DB_USER=${3:-postgres}
REMOTE_IP=${4:-}

echo "Starting PostgreSQL setup script..."
echo "Database Name: $DB_NAME"
echo "Username: $DB_USER"
echo "Password: [hidden for security]"
echo "Remote IP: ${REMOTE_IP:-Not provided}"

echo "Updating package list and installing PostgreSQL..."
sudo apt update
sudo apt install -y postgresql postgresql-contrib

echo "Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

echo "Setting up PostgreSQL..."
if [ "$DB_USER" != "postgres" ]; then
    echo "Creating new user: $DB_USER"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
else
    echo "Updating password for existing postgres user"
    sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '$DB_PASS';"
fi

echo "Creating database: $DB_NAME"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"

echo "Granting privileges on $DB_NAME to $DB_USER"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

if [ -n "$REMOTE_IP" ]; then
    echo "Configuring PostgreSQL to listen on all interfaces..."
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
    
    echo "Updating pg_hba.conf to allow password authentication for remote connections..."
    echo "host    $DB_NAME    $DB_USER    $REMOTE_IP/32    md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf
else
    echo "Configuring PostgreSQL to listen on 127.0.0.1..."
    sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '127.0.0.1'/" /etc/postgresql/*/main/postgresql.conf
fi

echo "Updating pg_hba.conf to allow password authentication for local connections..."
echo "host    $DB_NAME    $DB_USER    127.0.0.1/32    md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf

echo "Modifying PostgreSQL to use port 5433..."
sudo sed -i "s/#port = 5432/port = 5433/" /etc/postgresql/*/main/postgresql.conf

echo "Restarting PostgreSQL to apply changes..."
sudo systemctl restart postgresql

echo "PostgreSQL setup completed successfully!"
if [ -n "$REMOTE_IP" ]; then
    echo "You can now connect using the following SQLAlchemy URI:"
    echo "SQLALCHEMY_DATABASE_URI = \"postgresql://$DB_USER:$DB_PASS@$REMOTE_IP:5433/$DB_NAME\""
    echo "Note: Ensure your firewall allows incoming connections on port 5433"
else
    echo "You can now connect using the following SQLAlchemy URI:"
    echo "SQLALCHEMY_DATABASE_URI = \"postgresql://$DB_USER:$DB_PASS@127.0.0.1:5433/$DB_NAME\""
fi