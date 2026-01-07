#!/bin/bash

# Nexus Prime Production Deployment Script
# This script sets up the production environment for Nexus Prime

set -e

echo "🚀 Starting Nexus Prime Production Deployment"
echo "=============================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root"
   exit 1
fi

# Check required environment variables
required_vars=(
    "COSMOS_ENDPOINT"
    "COSMOS_KEY"
    "AZURE_OPENAI_ENDPOINT"
    "AZURE_OPENAI_API_KEY"
    "SECRET_KEY"
    "JWT_SECRET_KEY"
)

echo "🔍 Checking required environment variables..."
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ Required environment variable $var is not set"
        echo "Please set all required variables in .env.production"
        exit 1
    fi
done
echo "✅ All required environment variables are set"

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    certbot \
    python3-certbot-nginx \
    redis-server \
    supervisor

# Create application user
echo "👤 Creating application user..."
if ! id "nexus" &>/dev/null; then
    sudo useradd -m -s /bin/bash nexus
    sudo usermod -aG www-data nexus
fi

# Create application directories
echo "📁 Creating application directories..."
sudo mkdir -p /opt/nexus-prime
sudo mkdir -p /var/log/nexus-prime
sudo mkdir -p /var/run/nexus-prime
sudo chown -R nexus:nexus /opt/nexus-prime
sudo chown -R nexus:nexus /var/log/nexus-prime
sudo chown -R nexus:nexus /var/run/nexus-prime

# Copy application files
echo "📋 Copying application files..."
sudo cp -r . /opt/nexus-prime/
sudo chown -R nexus:nexus /opt/nexus-prime

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd /opt/nexus-prime
sudo -u nexus python3.11 -m venv venv
sudo -u nexus ./venv/bin/pip install --upgrade pip
sudo -u nexus ./venv/bin/pip install -r backend/requirements-production.txt

# Copy environment file
echo "⚙️ Setting up environment configuration..."
if [[ -f ".env.production" ]]; then
    sudo -u nexus cp .env.production backend/.env
else
    echo "❌ .env.production file not found"
    echo "Please create .env.production with your production settings"
    exit 1
fi

# Set up database containers (if needed)
echo "🗄️ Setting up database containers..."
cd /opt/nexus-prime
sudo -u nexus ./venv/bin/python backend/scripts/init_cosmos_containers.py

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/nexus-prime.service > /dev/null <<EOF
[Unit]
Description=Nexus Prime API Server
After=network.target

[Service]
Type=simple
User=nexus
Group=nexus
WorkingDirectory=/opt/nexus-prime
Environment=PATH=/opt/nexus-prime/venv/bin
ExecStart=/opt/nexus-prime/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nexus-prime

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/nexus-prime > /dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME:-nexus-prime.local};

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=webhook:10m rate=100r/s;

    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Webhook endpoints (higher rate limit)
    location /api/v1/ingest/webhook/ {
        limit_req zone=webhook burst=200 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 30s;
    }

    # WebSocket endpoints
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # Frontend (if serving from same domain)
    location / {
        root /opt/nexus-prime/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/nexus-prime /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Set up SSL certificate (if domain is provided)
if [[ -n "${DOMAIN_NAME}" ]]; then
    echo "🔒 Setting up SSL certificate..."
    sudo certbot --nginx -d ${DOMAIN_NAME} --non-interactive --agree-tos --email ${ADMIN_EMAIL:-admin@${DOMAIN_NAME}}
fi

# Configure log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/nexus-prime > /dev/null <<EOF
/var/log/nexus-prime/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 nexus nexus
    postrotate
        systemctl reload nexus-prime
    endscript
}
EOF

# Set up monitoring (basic)
echo "📊 Setting up basic monitoring..."
sudo tee /etc/cron.d/nexus-prime-health > /dev/null <<EOF
# Check Nexus Prime health every 5 minutes
*/5 * * * * nexus curl -f http://localhost:8000/health || systemctl restart nexus-prime
EOF

# Start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable nexus-prime
sudo systemctl start nexus-prime
sudo systemctl enable nginx
sudo systemctl restart nginx
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 10

# Health check
echo "🏥 Performing health check..."
if curl -f http://localhost:8000/health; then
    echo "✅ Nexus Prime is running successfully!"
else
    echo "❌ Health check failed. Check logs:"
    echo "   sudo journalctl -u nexus-prime -f"
    exit 1
fi

# Display status
echo ""
echo "🎉 Nexus Prime Production Deployment Complete!"
echo "=============================================="
echo ""
echo "📊 Service Status:"
sudo systemctl status nexus-prime --no-pager -l
echo ""
echo "🌐 Access URLs:"
echo "   API: http://${DOMAIN_NAME:-localhost}/api/v1/docs"
echo "   Health: http://${DOMAIN_NAME:-localhost}/health"
echo "   Dashboard: http://${DOMAIN_NAME:-localhost}"
echo ""
echo "📝 Useful Commands:"
echo "   View logs: sudo journalctl -u nexus-prime -f"
echo "   Restart service: sudo systemctl restart nexus-prime"
echo "   Check status: sudo systemctl status nexus-prime"
echo "   Nginx logs: sudo tail -f /var/log/nginx/access.log"
echo ""
echo "🔧 Next Steps:"
echo "   1. Test webhook endpoints with your monitoring tools"
echo "   2. Configure DNS to point to this server"
echo "   3. Set up monitoring and alerting"
echo "   4. Configure backup procedures"
echo "   5. Review security settings"
echo ""
echo "🆘 Support:"
echo "   Documentation: https://docs.nexus-prime.com"
echo "   Support: support@nexus-prime.com"
echo ""