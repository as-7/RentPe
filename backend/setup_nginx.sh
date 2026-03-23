#!/bin/bash
set -e

echo "========================================="
echo "  RentPe Nginx + SSL Setup"
echo "========================================="

# ── Nginx Config ──
echo "[1/3] Configuring Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/rentpe > /dev/null << 'NGINXEOF'
server {
    server_name api.rentpe.org;

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

sudo ln -sf /etc/nginx/sites-available/rentpe /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "[2/3] Testing and reloading Nginx..."
sudo nginx -t && sudo systemctl reload nginx

echo "[3/3] Setting up SSL certificate..."
echo "  → This will ask for your email and agreement to Let's Encrypt terms"
sudo certbot --nginx -d api.rentpe.org

echo ""
echo "========================================="
echo "  Nginx + SSL Setup Complete!"
echo "========================================="
echo "  → https://api.rentpe.org should now work"
echo "  → Test: curl https://api.rentpe.org/"
echo ""
