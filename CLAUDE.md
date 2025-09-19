# Development Notes for Claude

## Important: Use Containerized Environment

**Always use the containerized environment for both backend and frontend development and testing.**

### Frontend Development
- **Do NOT run the frontend locally** - it will have React Query cache issues that prevent proper data flow
- **Always use the containerized frontend** via `docker-compose up --build -d`
- The containerized frontend properly handles API data transformation and avoids cache staleness
- Local development can lead to stale React Query cache that persists even after API fixes
- **NOTE**: Port 3000 is occupied by another service, so the frontend runs on **port 3001** when run locally with `npm run dev`

### Backend Development
- Backend runs in Docker container with Gemma 3:27b model
- Use `docker logs research-agent -f` to monitor backend logs
- Model has 128K context window capability

### Testing
- Use Playwright browser automation for frontend testing
- Test against containerized services, not local development servers
- Frontend is available at http://localhost:3001 when running locally (port 3000 is taken)

### Common Issues
- **React Query Cache**: If frontend shows old data after backend changes, rebuild containers
- **API Format Mismatch**: Ensure API client requests JSON format explicitly
- **Session Management**: Ollama client uses persistent sessions to prevent closure errors
- **Port Conflicts**: Port 3000 is occupied, frontend auto-switches to port 3001

### Commands
```bash
# Start all services
docker-compose up --build -d

# Monitor backend logs
docker logs research-agent -f

# Rebuild frontend to clear cache issues
docker-compose down && docker-compose up --build -d

# For local development (not recommended but if needed)
cd research-agent-frontend && npm run dev
# Access at http://localhost:3001

# Test with Playwright
# Navigate to http://localhost:3001 for testing
```