# Melody API

A music API with role-based authentication for managing tracks, artists, and albums.

## Features

- User authentication with JWT tokens
- Role-based access control
- Music search and discovery
- Integration with Spotify and Audius APIs
- MongoDB database for data storage

## Docker Setup

### Prerequisites

- Docker and Docker Compose installed on your system
- API keys for external services (see `.env.example`)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd melody_BE
   ```

2. Copy the example environment file and configure your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your actual API keys and secrets
   ```

3. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

4. The API will be available at http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Default admin user: `admin` with password `admin123`

### MongoDB Connection

The application is configured to connect to the MongoDB container automatically with authentication:

- MongoDB is accessible at `mongodb://admin:password@mongo:27017/melody_db` within the Docker network
- Initial database and collections are created automatically via init scripts
- Data is persisted in a Docker volume named `mongo-data`

To connect to the MongoDB instance from outside Docker:

```bash
# Connect using the mongo shell
mongo mongodb://localhost:27017/melody_db -u admin -p password

# Or using MongoDB Compass
# Connection string: mongodb://admin:password@localhost:27017/melody_db
```

### Development

In development mode, you can use the volume mounts to see changes immediately:

```bash
docker-compose up
```

Any changes to the code will be reflected immediately due to the volume mount.

### Deployment

For deployment, use the provided script:

```bash
./scripts/deploy.sh
```

This script will pull the latest changes, build and start the containers.

## API Documentation

Once the server is running, you can access the Swagger UI documentation at:

```
http://localhost:8000/docs
```

### Authentication

To authenticate, use the `/api/v1/auth/login` endpoint with your username and password to get a JWT token. Then use this token in the Authorization header of your requests:

```
Authorization: Bearer <your-token>
```

## Technology Stack

- FastAPI: Web framework
- MongoDB: Database
- Docker: Containerization
- JWT: Authentication
- Swagger UI: API documentation

## License

[MIT License](LICENSE) 