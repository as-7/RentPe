#!/bin/bash
set -e

echo "========================================="
echo "  RentPe Nginx + SSL Setup (Amazon Linux)"
echo "========================================="

# ── 1. Install Certbot for Amazon Linux 2023 ──
echo "[1/4] Installing Certbot..."
sudo python3.11 -m venv /opt/certbot/
sudo /opt/certbot/bin/pip install --upgrade pip
sudo /opt/certbot/bin/pip install certbot certbot-nginx
sudo ln -sf /opt/certbot/bin/certbot /usr/bin/certbot

# ── Nginx Config ──
echo "[2/4] Configuring Nginx reverse proxy..."

# Amazon Linux nginx config is placed directly in conf.d
sudo tee /etc/nginx/conf.d/rentpe.conf > /dev/null << 'NGINXEOF'
server {
    server_name api.rentpe.org;
    listen 80;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINXEOF

echo "[3/4] Testing and starting Nginx..."
sudo systemctl enable nginx
sudo systemctl start nginx
sudo nginx -t && sudo systemctl reload nginx

echo "[4/4] Setting up SSL certificate..."
echo "  → This will ask for your email and agreement to Let's Encrypt terms"
sudo certbot --nginx -d api.rentpe.org

echo ""
echo "========================================="
echo "  Nginx + SSL Setup Complete!"
echo "========================================="
echo "  → https://api.rentpe.org should now work"
echo "  → Test: curl https://api.rentpe.org/"
echo ""
