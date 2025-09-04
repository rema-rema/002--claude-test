#!/bin/bash

# Docker Manager Script for Multi-Session Development
# Usage: ./scripts/docker-manager.sh <command> [session]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
SESSIONS=("session1" "session2" "session3" "session4" "staging")
ALL_SERVICES=("postgres-session1" "redis-session1" "postgres-session2" "redis-session2" "postgres-session3" "redis-session3" "postgres-session4" "redis-session4" "postgres-staging" "redis-staging")

print_usage() {
    echo "Usage: $0 <command> [session]"
    echo ""
    echo "Commands:"
    echo "  start [session]    - Start all services or specific session"
    echo "  stop [session]     - Stop all services or specific session"
    echo "  restart [session]  - Restart all services or specific session"
    echo "  status [session]   - Show status of all services or specific session"
    echo "  logs [session]     - Show logs for all services or specific session"
    echo "  clean [session]    - Clean volumes for all services or specific session"
    echo "  reset [session]    - Reset (stop, clean, start) all services or specific session"
    echo "  tools              - Start management tools (pgAdmin, Redis Commander)"
    echo "  backup [session]   - Backup database for specific session"
    echo "  restore [session]  - Restore database for specific session"
    echo ""
    echo "Sessions: session1, session2, session3, session4, staging, all"
    echo ""
    echo "Examples:"
    echo "  $0 start session1     # Start only session1 environment"
    echo "  $0 start all          # Start all environments"
    echo "  $0 status session2    # Check session2 status"
    echo "  $0 logs session1      # View session1 logs"
    echo "  $0 backup session1    # Backup session1 database"
}

get_services_for_session() {
    local session=$1
    case $session in
        "session1") echo "postgres-session1 redis-session1" ;;
        "session2") echo "postgres-session2 redis-session2" ;;
        "session3") echo "postgres-session3 redis-session3" ;;
        "session4") echo "postgres-session4 redis-session4" ;;
        "staging") echo "postgres-staging redis-staging" ;;
        "all") echo "${ALL_SERVICES[@]}" ;;
        *) echo ""; return 1 ;;
    esac
}

validate_session() {
    local session=$1
    if [[ "$session" == "all" ]] || [[ " ${SESSIONS[@]} " =~ " $session " ]]; then
        return 0
    else
        echo -e "${RED}Error: Invalid session '$session'${NC}"
        echo -e "Valid sessions: ${SESSIONS[@]} all"
        return 1
    fi
}

start_services() {
    local session=${1:-"all"}
    
    if ! validate_session "$session"; then
        return 1
    fi
    
    local services=$(get_services_for_session "$session")
    
    echo -e "${GREEN}Starting $session environment...${NC}"
    docker compose -f $COMPOSE_FILE up -d $services
    
    echo -e "${GREEN}Waiting for services to be ready...${NC}"
    sleep 5
    
    docker compose -f $COMPOSE_FILE ps $services
}

stop_services() {
    local session=${1:-"all"}
    
    if ! validate_session "$session"; then
        return 1
    fi
    
    local services=$(get_services_for_session "$session")
    
    echo -e "${YELLOW}Stopping $session environment...${NC}"
    docker compose -f $COMPOSE_FILE stop $services
}

restart_services() {
    local session=${1:-"all"}
    
    echo -e "${YELLOW}Restarting $session environment...${NC}"
    stop_services "$session"
    sleep 2
    start_services "$session"
}

show_status() {
    local session=${1:-"all"}
    
    if ! validate_session "$session"; then
        return 1
    fi
    
    local services=$(get_services_for_session "$session")
    
    echo -e "${BLUE}Status for $session environment:${NC}"
    docker compose -f $COMPOSE_FILE ps $services
    
    # Health check
    echo -e "\n${BLUE}Health Status:${NC}"
    for service in $services; do
        health=$(docker inspect --format='{{.State.Health.Status}}' $service 2>/dev/null || echo "no-healthcheck")
        if [[ "$health" == "healthy" ]]; then
            echo -e "  $service: ${GREEN}$health${NC}"
        elif [[ "$health" == "unhealthy" ]]; then
            echo -e "  $service: ${RED}$health${NC}"
        else
            echo -e "  $service: ${YELLOW}$health${NC}"
        fi
    done
}

show_logs() {
    local session=${1:-"all"}
    
    if ! validate_session "$session"; then
        return 1
    fi
    
    local services=$(get_services_for_session "$session")
    
    echo -e "${BLUE}Logs for $session environment:${NC}"
    docker compose -f $COMPOSE_FILE logs --tail=50 -f $services
}

clean_volumes() {
    local session=${1:-"all"}
    
    if ! validate_session "$session"; then
        return 1
    fi
    
    echo -e "${RED}Warning: This will delete all data for $session environment!${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        local services=$(get_services_for_session "$session")
        
        # Stop services first
        docker compose -f $COMPOSE_FILE stop $services
        
        # Remove volumes
        case $session in
            "session1") docker volume rm $(docker volume ls -q | grep "postgres_session1\|redis_session1") 2>/dev/null || true ;;
            "session2") docker volume rm $(docker volume ls -q | grep "postgres_session2\|redis_session2") 2>/dev/null || true ;;
            "session3") docker volume rm $(docker volume ls -q | grep "postgres_session3\|redis_session3") 2>/dev/null || true ;;
            "session4") docker volume rm $(docker volume ls -q | grep "postgres_session4\|redis_session4") 2>/dev/null || true ;;
            "staging") docker volume rm $(docker volume ls -q | grep "postgres_staging\|redis_staging") 2>/dev/null || true ;;
            "all") docker compose -f $COMPOSE_FILE down -v ;;
        esac
        
        echo -e "${GREEN}Volumes cleaned for $session${NC}"
    else
        echo -e "${YELLOW}Cancelled${NC}"
    fi
}

reset_environment() {
    local session=${1:-"all"}
    
    echo -e "${YELLOW}Resetting $session environment...${NC}"
    stop_services "$session"
    clean_volumes "$session"
    start_services "$session"
}

start_tools() {
    echo -e "${GREEN}Starting management tools...${NC}"
    docker compose -f $COMPOSE_FILE up -d pgadmin redis-commander
    
    echo -e "${GREEN}Management tools started:${NC}"
    echo -e "  pgAdmin: ${BLUE}http://localhost:8080${NC} (admin@example.com / admin123)"
    echo -e "  Redis Commander: ${BLUE}http://localhost:8081${NC}"
}

backup_database() {
    local session=$1
    
    if [[ -z "$session" ]] || [[ "$session" == "all" ]]; then
        echo -e "${RED}Error: Please specify a session for backup${NC}"
        return 1
    fi
    
    if ! validate_session "$session"; then
        return 1
    fi
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="./backups/${session}_backup_${timestamp}.sql"
    
    echo -e "${GREEN}Backing up $session database...${NC}"
    
    case $session in
        "session1") docker exec postgres-session1 pg_dump -U session1_user session1_dev > "$backup_file" ;;
        "session2") docker exec postgres-session2 pg_dump -U session2_user session2_dev > "$backup_file" ;;
        "session3") docker exec postgres-session3 pg_dump -U session3_user session3_dev > "$backup_file" ;;
        "session4") docker exec postgres-session4 pg_dump -U session4_user session4_dev > "$backup_file" ;;
        "staging") docker exec postgres-staging pg_dump -U staging_user staging_db > "$backup_file" ;;
    esac
    
    echo -e "${GREEN}Backup completed: $backup_file${NC}"
}

# Main command handling
case $1 in
    "start")
        start_services "$2"
        ;;
    "stop")
        stop_services "$2"
        ;;
    "restart")
        restart_services "$2"
        ;;
    "status")
        show_status "$2"
        ;;
    "logs")
        show_logs "$2"
        ;;
    "clean")
        clean_volumes "$2"
        ;;
    "reset")
        reset_environment "$2"
        ;;
    "tools")
        start_tools
        ;;
    "backup")
        backup_database "$2"
        ;;
    "restore")
        echo -e "${YELLOW}Restore feature coming soon...${NC}"
        ;;
    *)
        print_usage
        exit 1
        ;;
esac