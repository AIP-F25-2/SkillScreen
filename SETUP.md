# SkillScreen Setup Guide

## Environment Configuration

### 1. Create your local `.env` file

Copy the example file:
```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and update the following:

#### Required:
- `RESEND_API_KEY`: Get from https://resend.com (free tier available)
- `DATABASE_URL`: Your PostgreSQL connection string

#### Optional (defaults provided):
- `FROM_EMAIL`: Email sender address (default: interviews@skillscreen.io)
- `FRONTEND_URL`: Frontend URL (default: http://localhost:3000)
- `JWT_SECRET`: Secret for JWT tokens (change in production!)

### 3. Start Services

```bash
docker compose -f docker-compose.dev.yml up -d
```

### 4. Verify Email Service

After uploading a resume, emails will be sent to `dummyintervuai@gmail.com` for testing.

To send to real candidate emails, update the email service configuration in:
`backend/interview-service/services/email_service.py`

## Important Notes

- ⚠️ **Never commit `.env` to Git** - it contains sensitive credentials
- ✅ **Always update `.env.example`** when adding new environment variables
- 🔒 **Use strong secrets** in production environments
- 📧 **Test email delivery** before production deployment

## Troubleshooting

### Emails not sending?
1. Check `RESEND_API_KEY` is set in `.env`
2. Verify API key is valid at https://resend.com/api-keys
3. Check interview-service logs: `docker logs interview-service`

### Database connection issues?
1. Verify `DATABASE_URL` is correct
2. Ensure database server is accessible
3. Check firewall rules for database port (5432)
