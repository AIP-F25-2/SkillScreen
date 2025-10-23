# SkillScreen Production Deployment Guide

## Security Configuration

This deployment requires secure environment variables to be set. **Never commit sensitive information to Git.**

### Required Environment Variables

Before running the production deployment, you must set the following environment variables:

#### Database Configuration
```bash
export POSTGRES_PASSWORD="your_secure_postgres_password_here"
```

#### Monitoring Configuration
```bash
export GRAFANA_PASSWORD="your_secure_grafana_password_here"
```

#### API Keys (Optional)
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
export WOLFRAM_APP_ID="your_wolfram_app_id_here"
export SERPAPI_KEY="your_serpapi_key_here"
```

#### Security Configuration
```bash
export SECRET_KEY="your_secret_key_for_jwt_tokens_here"
export ENCRYPTION_KEY="your_encryption_key_for_sensitive_data_here"
```

### Setting Up Environment Variables

#### Option 1: Using .env file (Recommended for Development)
1. Copy `env.example` to `.env`:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and fill in your actual values:
   ```bash
   nano .env
   ```

3. Load environment variables:
   ```bash
   source .env
   ```

#### Option 2: System Environment Variables (Recommended for Production)
Set the environment variables in your system or container orchestration platform:

```bash
# For Docker Compose
export POSTGRES_PASSWORD="secure_password_123"
export GRAFANA_PASSWORD="secure_grafana_456"

# Then run docker-compose
docker-compose up -d
```

#### Option 3: Docker Secrets (Production)
For production deployments, consider using Docker secrets or your cloud provider's secret management service.

### Deployment Commands

1. **Set environment variables** (see options above)

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Verify deployment**:
   ```bash
   # Check API health
   curl http://localhost:8000/api/health
   
   # Check Grafana (default: http://localhost:3000)
   # Login with admin / your GRAFANA_PASSWORD
   ```

### Security Best Practices

1. **Use strong passwords**: Generate secure, random passwords for all services
2. **Rotate credentials regularly**: Change passwords periodically
3. **Limit access**: Only provide credentials to authorized personnel
4. **Monitor access**: Use audit logs to track who accesses what
5. **Backup securely**: Encrypt database backups

### Troubleshooting

#### "Environment variable not set" errors
- Ensure all required environment variables are set
- Check that `.env` file is loaded with `source .env`
- Verify environment variables are exported: `echo $POSTGRES_PASSWORD`

#### Database connection issues
- Verify `POSTGRES_PASSWORD` is set correctly
- Check that PostgreSQL container is healthy: `docker-compose ps`
- Review logs: `docker-compose logs postgres`

#### Monitoring access issues
- Verify `GRAFANA_PASSWORD` is set correctly
- Check Grafana container status: `docker-compose logs grafana`
- Access Grafana at http://localhost:3000

### Support

For deployment issues, check:
1. Environment variable configuration
2. Docker container logs
3. Network connectivity
4. Resource availability (CPU, memory, disk)
