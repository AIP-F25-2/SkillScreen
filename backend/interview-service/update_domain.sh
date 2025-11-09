#!/bin/bash

# Script to update domain configuration for Resend
# Usage: ./update_domain.sh yourdomain.com

if [ -z "$1" ]; then
    echo "Usage: ./update_domain.sh yourdomain.com"
    echo "Example: ./update_domain.sh skillscreen-mail.github.io"
    exit 1
fi

DOMAIN=$1
ENV_FILE="/Users/dimanthagoonewardena/Desktop/SkillScreen/backend/interview-service/.env"

echo "Updating domain configuration for: $DOMAIN"
echo ""

# Backup current .env
cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ Backed up current .env file"

# Update FROM_EMAIL
sed -i '' "s/FROM_EMAIL=.*/FROM_EMAIL=interviews@$DOMAIN/" "$ENV_FILE"
echo "✅ Updated FROM_EMAIL to: interviews@$DOMAIN"

# Show updated configuration
echo ""
echo "Updated configuration:"
echo "======================"
grep "FROM_EMAIL\|RESEND_API_KEY" "$ENV_FILE"

echo ""
echo "Next steps:"
echo "1. Restart the interview service:"
echo "   pkill -f 'uvicorn interview:app'"
echo "   cd backend/interview-service && uvicorn interview:app --host 0.0.0.0 --port 8003 --reload"
echo ""
echo "2. Test with your Gmail:"
echo "   curl -X POST http://localhost:8003/api/email/send-invitation \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"candidate_email\": \"goonewardenadimantha@gmail.com\", \"candidate_name\": \"Test\", \"candidate_id\": \"test\", \"session_id\": \"test\"}'"
echo ""
echo "3. Check Resend dashboard: https://resend.com/emails"
