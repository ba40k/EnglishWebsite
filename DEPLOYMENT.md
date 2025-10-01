# DigitalOcean Deployment Guide

## Option 1: App Platform (Recommended - Easiest)

### Prerequisites
1. DigitalOcean account
2. GitHub repository with your code
3. OpenRouter API key

### Steps

1. **Push your code to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin master
   ```

2. **Deploy on App Platform**:
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App"
   - Connect your GitHub repository
   - Select your repository and branch (master)
   - DigitalOcean will auto-detect the configuration from `.do/app.yaml`

3. **Set Environment Variables**:
   - In the App settings, add your environment variable:
     - Key: `OPENROUTER_API_KEY`
     - Value: Your actual OpenRouter API key
     - Mark it as "SECRET"

4. **Deploy**:
   - Click "Next" through the wizard
   - Review your settings
   - Click "Create Resources"
   - Wait 3-5 minutes for deployment

5. **Access Your App**:
   - You'll get a URL like: `https://your-app-name.ondigitalocean.app`

### Cost
- Basic plan starts at **$5/month**
- Auto-scaling available

### Important Notes

⚠️ **SQLite Database Limitation**: 
- App Platform uses ephemeral storage (resets on deploy)
- Your SQLite database will be wiped on each deployment
- **Solution**: Upgrade to PostgreSQL (see below)

### Upgrading to PostgreSQL (Recommended for Production)

1. **Create PostgreSQL database in App Platform**:
   - In your app settings, add a database component
   - Choose PostgreSQL 14 or 15
   - This costs an additional $7/month

2. **Update your code** to use PostgreSQL instead of SQLite:
   
   Update `app/main.py`:
   ```python
   import os
   
   # Replace line 13 with:
   DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{str(BASE_DIR / 'database.db')}")
   
   # For PostgreSQL, remove SQLite-specific connect_args
   if DB_URL.startswith("sqlite"):
       engine = create_engine(DB_URL, connect_args={"check_same_thread": False}, future=True)
   else:
       engine = create_engine(DB_URL, future=True)
   ```

3. **Add psycopg2 to requirements**:
   Add to `requirments.txt`:
   ```
   psycopg2-binary==2.9.9
   ```

---

## Option 2: Droplet (VPS) Deployment

This gives you more control but requires more setup.

### Prerequisites
1. DigitalOcean account
2. SSH key configured

### Steps

1. **Create a Droplet**:
   - Ubuntu 22.04 LTS
   - Basic plan ($6/month for 1GB RAM)
   - Choose a datacenter region near you
   - Add your SSH key

2. **SSH into your Droplet**:
   ```bash
   ssh root@your_droplet_ip
   ```

3. **Initial Server Setup**:
   ```bash
   # Update system
   apt update && apt upgrade -y
   
   # Install Python and dependencies
   apt install python3 python3-pip python3-venv nginx supervisor -y
   
   # Create app user
   adduser --disabled-password --gecos "" appuser
   ```

4. **Deploy Your Application**:
   ```bash
   # Switch to app user
   su - appuser
   
   # Clone your repository
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd YOUR_REPO
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirments.txt
   
   # Create .env file
   echo "OPENROUTER_API_KEY=your_key_here" > .env
   ```

5. **Configure Supervisor** (keeps your app running):
   ```bash
   exit  # Back to root
   nano /etc/supervisor/conf.d/englishapp.conf
   ```
   
   Add this configuration:
   ```ini
   [program:englishapp]
   directory=/home/appuser/YOUR_REPO
   command=/home/appuser/YOUR_REPO/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   user=appuser
   autostart=true
   autorestart=true
   redirect_stderr=true
   stdout_logfile=/var/log/englishapp.log
   environment=PATH="/home/appuser/YOUR_REPO/venv/bin"
   ```
   
   Start the service:
   ```bash
   supervisorctl reread
   supervisorctl update
   supervisorctl start englishapp
   ```

6. **Configure Nginx** (reverse proxy):
   ```bash
   nano /etc/nginx/sites-available/englishapp
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;  # or your droplet IP
   
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   
       location /static {
           alias /home/appuser/YOUR_REPO/app/static;
       }
   }
   ```
   
   Enable and restart:
   ```bash
   ln -s /etc/nginx/sites-available/englishapp /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx
   ```

7. **Configure Firewall**:
   ```bash
   ufw allow 22
   ufw allow 80
   ufw allow 443
   ufw enable
   ```

8. **Optional: Add SSL with Let's Encrypt**:
   ```bash
   apt install certbot python3-certbot-nginx -y
   certbot --nginx -d your_domain.com
   ```

### Cost
- **$6/month** for basic droplet
- More control but more maintenance

---

## Comparison

| Feature | App Platform | Droplet (VPS) |
|---------|-------------|---------------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ Very Easy | ⭐⭐ Moderate |
| **Cost** | $5-12/month | $6+/month |
| **Maintenance** | Automatic | Manual |
| **Scaling** | Automatic | Manual |
| **Control** | Limited | Full |
| **Best For** | Quick deployment, beginners | Custom needs, advanced users |

## Recommendation

**Start with App Platform** - it's easier and handles scaling/security automatically. Upgrade to PostgreSQL if you need data persistence.

## Post-Deployment Checklist

- [ ] App is accessible via URL
- [ ] Environment variables are set
- [ ] AI features work (test article summary)
- [ ] Database persists data (if using PostgreSQL)
- [ ] Static files load correctly
- [ ] Set up custom domain (optional)
- [ ] Enable automatic deployments from GitHub
- [ ] Monitor application logs

## Troubleshooting

### App won't start
- Check build logs in DigitalOcean dashboard
- Verify all dependencies in `requirments.txt`
- Ensure port is correct (8080 for App Platform)

### AI features not working
- Verify `OPENROUTER_API_KEY` environment variable is set
- Check API key is valid

### Database issues
- If using SQLite on App Platform: data will reset on deploy
- Upgrade to PostgreSQL for persistent storage

### Static files not loading
- Ensure `/static` mount path is correct
- Check file permissions

## Need Help?

- [DigitalOcean App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [DigitalOcean Community](https://www.digitalocean.com/community)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)

