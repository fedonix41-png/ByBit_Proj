#!/bin/bash
#
# Database Backup Script for ByBit P2P Automation
# Usage: ./scripts/backup_db.sh [options]
#
# Options:
#   --container   Backup from Docker container (default)
#   --local       Backup from local PostgreSQL
#   --restore     Restore from backup file
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DB_NAME="${POSTGRES_DB:-p2p_automation}"
DB_USER="${POSTGRES_USER:-p2p_user}"
CONTAINER_NAME="${POSTGRES_CONTAINER:-p2p_postgres}"

# Timestamp for backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/p2p_backup_${TIMESTAMP}.sql.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log_info "Created backup directory: $BACKUP_DIR"
    fi
}

# Backup from Docker container
backup_docker() {
    log_info "Starting backup from Docker container: $CONTAINER_NAME"
    
    # Check if container is running
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        log_error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
    
    # Create backup
    docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists | gzip > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        log_info "Backup created: $BACKUP_FILE"
        log_info "Size: $(du -h "$BACKUP_FILE" | cut -f1)"
    else
        log_error "Backup failed"
        exit 1
    fi
}

# Backup from local PostgreSQL
backup_local() {
    log_info "Starting local PostgreSQL backup"
    
    # Check if pg_dump exists
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump not found. Please install PostgreSQL client tools."
        exit 1
    fi
    
    # Create backup
    pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists | gzip > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        log_info "Backup created: $BACKUP_FILE"
        log_info "Size: $(du -h "$BACKUP_FILE" | cut -f1)"
    else
        log_error "Backup failed"
        exit 1
    fi
}

# Restore from backup
restore_backup() {
    local RESTORE_FILE="$1"
    
    if [ -z "$RESTORE_FILE" ]; then
        log_error "Please specify backup file to restore"
        echo "Usage: $0 --restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$RESTORE_FILE" ]; then
        log_error "Backup file not found: $RESTORE_FILE"
        exit 1
    fi
    
    log_warn "This will REPLACE the current database!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled"
        exit 0
    fi
    
    log_info "Restoring from: $RESTORE_FILE"
    
    # Check if file is gzipped
    if [[ "$RESTORE_FILE" == *.gz ]]; then
        gunzip -c "$RESTORE_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"
    else
        docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" < "$RESTORE_FILE"
    fi
    
    if [ $? -eq 0 ]; then
        log_info "Restore completed successfully"
    else
        log_error "Restore failed"
        exit 1
    fi
}

# Rotate old backups
rotate_backups() {
    log_info "Rotating backups older than $RETENTION_DAYS days"
    
    local deleted_count=$(find "$BACKUP_DIR" -name "p2p_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
    
    if [ "$deleted_count" -gt 0 ]; then
        log_info "Deleted $deleted_count old backup(s)"
    fi
}

# List backups
list_backups() {
    log_info "Available backups in $BACKUP_DIR:"
    
    if [ -d "$BACKUP_DIR" ]; then
        ls -lh "$BACKUP_DIR"/p2p_backup_*.sql.gz 2>/dev/null || log_info "No backups found"
    else
        log_info "Backup directory does not exist"
    fi
}

# Main
main() {
    create_backup_dir
    
    case "${1:-}" in
        --container)
            backup_docker
            ;;
        --local)
            backup_local
            ;;
        --restore)
            restore_backup "$2"
            ;;
        --list)
            list_backups
            ;;
        --rotate)
            rotate_backups
            ;;
        *)
            # Default: Docker backup + rotation
            backup_docker
            rotate_backups
            list_backups
            ;;
    esac
}

main "$@"
