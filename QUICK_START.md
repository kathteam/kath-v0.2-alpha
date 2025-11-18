# KATH Quick Start Guide

## One-Click Launch

### Windows

**Double-click:** `start-kath.bat`

### Linux/Mac

```bash
chmod +x start-kath.sh && ./start-kath.sh
```

That's it! The script will:

1. Install/start Docker automatically
2. Download KATH (first time only, ~3-4GB)
3. Start the application
4. Open your browser automatically

---

## What You Need

- **Internet connection** (for first-time download)
- **4GB RAM** minimum (8GB recommended)
- **10GB free space**
- **Windows 10+, macOS 10.15+, or Linux**

That's all! The script handles Docker installation.

---

## Accessing KATH

After starting, open your browser to:

**Frontend:** <http://localhost:5173>
**API:** <http://localhost:8080>
**Health Check:** <http://localhost:8080/api/v1/monitoring/health>

---

## Your Data

All your work is saved in:

- `./data/` - Your workspace files
- `./database/` - Database (1.2M+ variants)

**Your data persists** even when you close KATH!

---

## Troubleshooting

### "Docker is not installed"

**Windows/Mac:** Download from <https://docker.com/products/docker-desktop>
**Linux:** Script will show install commands

### "Port already in use"

Another program is using ports 5173 or 8080. Close it or:

```bash
docker stop kath
./start-kath.sh
```

### "Docker won't start"

**Windows/Mac:** Open Docker Desktop, wait 1 minute
**Linux:** `sudo systemctl start docker`

---

## Stopping KATH

Press `Ctrl+C` in the terminal where KATH is running.

---

## Updating

```bash
docker pull cpu64/kath:latest
./start-kath.sh
```

Your data is automatically preserved!

---

## More Documentation

- **Docker Deployment:** See `DOCKER_DEPLOYMENT.md`
- **Full Documentation:** See `README.md`
- **How to Run:** See `HOW_TO_RUN.md`

---

## Need Help?

1. Check health: <http://localhost:8080/api/v1/monitoring/health>
2. View logs: `docker logs kath`
3. Report issues: GitHub Issues
