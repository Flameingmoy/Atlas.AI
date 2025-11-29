#!/bin/bash
#
# Atlas.AI - DuckDB to PostGIS Migration Script
# 
# Usage: ./scripts/migrate.sh [options]
#
# Options:
#   --start-db    Start PostGIS container before migration
#   --env FILE    Use custom .env file (default: .env)
#   --help        Show this help message
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENV_FILE="$PROJECT_ROOT/.env"
START_DB=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --start-db)
            START_DB=true
            shift
            ;;
        --env)
            ENV_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Atlas.AI - DuckDB to PostGIS Migration Script"
            echo ""
            echo "Usage: ./scripts/migrate.sh [options]"
            echo ""
            echo "Options:"
            echo "  --start-db    Start PostGIS container before migration"
            echo "  --env FILE    Use custom .env file (default: .env)"
            echo "  --help        Show this help message"
            echo ""
            echo "Environment variables (can be set in .env):"
            echo "  DB_HOST       PostGIS host (default: localhost)"
            echo "  DB_PORT       PostGIS port (default: 5433)"
            echo "  DB_USER       PostGIS user (default: atlas)"
            echo "  DB_PASSWORD   PostGIS password (default: atlas_secret)"
            echo "  DB_NAME       PostGIS database (default: atlas_db)"
            echo "  DUCKDB_PATH   Path to DuckDB file (default: ./data/delhi.db)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}       Atlas.AI - DuckDB to PostGIS Migration${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}Loading environment from: $ENV_FILE${NC}"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo -e "${YELLOW}Warning: .env file not found at $ENV_FILE${NC}"
    echo -e "${YELLOW}Using default values...${NC}"
fi

# Set defaults if not provided
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${DB_USER:-atlas}"
DB_PASSWORD="${DB_PASSWORD:-atlas_secret}"
DB_NAME="${DB_NAME:-atlas_db}"
DUCKDB_PATH="${DUCKDB_PATH:-$PROJECT_ROOT/data/delhi.db}"

# Convert relative path to absolute
if [[ ! "$DUCKDB_PATH" = /* ]]; then
    DUCKDB_PATH="$PROJECT_ROOT/$DUCKDB_PATH"
fi

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  PostGIS: $DB_HOST:$DB_PORT/$DB_NAME"
echo "  DuckDB:  $DUCKDB_PATH"
echo ""

# Check if DuckDB file exists
if [ ! -f "$DUCKDB_PATH" ]; then
    echo -e "${RED}Error: DuckDB file not found at $DUCKDB_PATH${NC}"
    exit 1
fi

# Start PostGIS if requested
if [ "$START_DB" = true ]; then
    echo -e "${YELLOW}Starting PostGIS container...${NC}"
    
    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^atlas-postgis$"; then
        echo "Container 'atlas-postgis' already exists, starting it..."
        docker start atlas-postgis
    else
        echo "Creating new PostGIS container..."
        docker run -d \
            --name atlas-postgis \
            -e POSTGRES_USER="$DB_USER" \
            -e POSTGRES_PASSWORD="$DB_PASSWORD" \
            -e POSTGRES_DB="$DB_NAME" \
            -p "$DB_PORT:5432" \
            postgis/postgis:16-3.4-alpine
    fi
    
    # Wait for PostGIS to be ready
    echo -e "${YELLOW}Waiting for PostGIS to be ready...${NC}"
    for i in {1..30}; do
        if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &>/dev/null; then
            echo -e "${GREEN}PostGIS is ready!${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}Timeout waiting for PostGIS${NC}"
            exit 1
        fi
        sleep 1
    done
    echo ""
fi

# Check Python dependencies
echo -e "${YELLOW}Checking Python dependencies...${NC}"
python3 -c "import duckdb, psycopg2" 2>/dev/null || {
    echo -e "${YELLOW}Installing required Python packages...${NC}"
    pip install duckdb psycopg2-binary
}

# Run migration
echo ""
echo -e "${GREEN}Starting migration...${NC}"
echo ""

cd "$PROJECT_ROOT"
export DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME DUCKDB_PATH

python3 backend/scripts/migrate_to_postgis.py

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}       Migration Complete!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "You can now start the full stack with:"
echo -e "  ${BLUE}docker compose up -d${NC}"
echo ""
echo -e "Or verify the migration with:"
echo -e "  ${BLUE}PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \"SELECT COUNT(*) FROM delhi_points;\"${NC}"
