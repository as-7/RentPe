#!/bin/bash
set -e

echo "========================================="
echo "  RentPe EC2 Server Setup Script (Amazon Linux)"
echo "========================================="

# ── 1. System Update ──
echo "[1/8] Updating system packages..."
sudo yum update -y

# ── 2. Install Dependencies ──
echo "[2/8] Installing Python, Nginx, Git..."
sudo yum install -y python3 python3-pip git nginx
# Amazon Linux 2023 provides python3 and pip by default.

# ── 3. Clone Repository ──
echo "[3/8] Cloning RentPe repository..."
cd /home/ec2-user
if [ -d "RentPe" ]; then
    echo "  → RentPe directory exists, pulling latest..."
    cd RentPe && git pull origin main
else
    git clone https://github.com/as-7/RentPe.git
    cd RentPe
fi

# ── 4. Setup Python Virtual Environment ──
echo "[4/8] Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── 5. Create .env file ──
echo "[5/8] Creating production .env file..."
echo ""
echo "  ⚠️  You need to fill in the values below:"
echo ""

if [ ! -f .env ]; then
cat > .env << 'ENVEOF'
# RentPe Production Environment
DATABASE_URL=postgresql+asyncpg://postgres.hlwggvtdjdxeypdowftq:YOUR_SUPABASE_PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
SECRET_KEY=CHANGE_ME_TO_A_RANDOM_64_CHAR_STRING
FIREBASE_SERVICE_ACCOUNT_KEY=serviceAccountKey.json
ENVEOF
echo "  → .env file created at /home/ec2-user/RentPe/backend/.env"
echo "  → EDIT IT NOW: nano /home/ec2-user/RentPe/backend/.env"
echo "  → Replace YOUR_SUPABASE_PASSWORD with the real password"
echo "  → Replace CHANGE_ME with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
else
    echo "  → .env file already exists, skipping..."
fi

# ── 6. Copy serviceAccountKey.json reminder ──
echo ""
echo "[6/8] Firebase Service Account Key"
if [ ! -f serviceAccountKey.json ]; then
    echo "  ⚠️  serviceAccountKey.json NOT FOUND!"
    echo "  → Copy it from your local machine:"
    echo "  → scp -i your-key.pem /path/to/serviceAccountKey.json ec2-user@<EC2_IP>:/home/ec2-user/RentPe/backend/"
else
    echo "  → serviceAccountKey.json found ✓"
fi

# ── 7. Run Alembic Migrations ──
echo ""
echo "[7/8] Running database migrations..."
echo "  (This will fail if .env is not configured — that's OK, run manually after)"
source venv/bin/activate
alembic upgrade heads 2>/dev/null && echo "  → Migrations complete ✓" || echo "  → Migrations skipped (configure .env first, then run: cd /home/ec2-user/RentPe/backend && source venv/bin/activate && alembic upgrade heads)"

# ── 8. Setup Systemd Service ──
echo ""
echo "[8/8] Setting up systemd service..."
sudo tee /etc/systemd/system/rentpe.service > /dev/null << 'SERVICEEOF'
[Unit]
Description=RentPe FastAPI Backend
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/RentPe/backend
Environment="PATH=/home/ec2-user/RentPe/backend/venv/bin"
EnvironmentFile=/home/ec2-user/RentPe/backend/.env
ExecStart=/home/ec2-user/RentPe/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable rentpe

echo ""
echo "========================================="
echo "  Setup Complete! Next Steps:"
echo "========================================="
echo ""
echo "  1. Edit .env:        nano /home/ec2-user/RentPe/backend/.env"
echo "  2. Copy Firebase key: scp serviceAccountKey.json to /home/ec2-user/RentPe/backend/"
echo "  3. Run migrations:   cd /home/ec2-user/RentPe/backend && source venv/bin/activate && alembic upgrade heads"
echo "  4. Start service:    sudo systemctl start rentpe"
echo "  5. Check status:     sudo systemctl status rentpe"
echo "  6. Run nginx setup:  bash /home/ec2-user/RentPe/backend/setup_nginx.sh"
echo ""
