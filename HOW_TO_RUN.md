# How to Run KATH

A simple guide to get KATH up and running on your computer.

## Quick Start

### Windows Users

1. **Double-click** one of these files:
   - `start-kath.bat` (recommended for most users)
   - `start-kath.ps1` (for PowerShell users)

2. **Wait** for the system to start (first time may take 5-10 minutes to download)

3. **Your browser will open automatically** to http://localhost:5173

That's it! KATH is now running.

### Mac/Linux Users

1. **Open Terminal** in the KATH folder

2. **Run the script:**
   ```bash
   ./start-kath.sh
   ```

3. **Wait** for the system to start (first time may take 5-10 minutes to download)

4. **Your browser will open automatically** to http://localhost:5173

That's it! KATH is now running.

## First Time Setup

When you run KATH for the first time:

1. The script will check if Docker is installed
2. If Docker is missing, it will help you install it (Mac) or provide instructions (Windows/Linux)
3. It will download the KATH system (about 2-5 GB)
4. It will create a workspace folder on your Desktop called `kath`
5. It will open your web browser to the KATH interface

## What You Need

- **Operating System:** Windows 10/11, macOS, or Linux
- **Internet Connection:** Required for first-time download
- **Disk Space:** At least 10 GB free
- **Docker:** Will be installed automatically (Mac) or with guidance (Windows/Linux)

## Using KATH

Once the browser opens:

- The KATH interface will appear at http://localhost:5173
- Your data will be saved in the `kath` folder on your Desktop
- The system runs completely on your local computer

## Stopping KATH

- **Press `Ctrl+C`** in the terminal/command window where KATH is running
- The system will stop gracefully and clean up

## Troubleshooting

### "Docker is not installed"

**Windows:**
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Install and restart your computer
3. Run the script again

**Mac:**
- The script will attempt to install Docker automatically
- If it fails, download from https://www.docker.com/products/docker-desktop

**Linux:**
- Follow the instructions provided by the script

### "Docker is not running"

- **Windows/Mac:** The script will try to start Docker Desktop automatically
- **Wait 30-60 seconds** for Docker to fully start
- If it doesn't start, open Docker Desktop manually and then run the script again

### Browser doesn't open automatically

- Manually open your browser and go to: **http://localhost:5173**

### Port already in use

If you see an error about ports 5173 or 8080 being in use:
1. Stop the script (`Ctrl+C`)
2. Close any other applications using these ports
3. Run the script again

### Need help?

- Check the terminal/command window for error messages
- Look for red `[ERROR]` messages that explain what went wrong
- Make sure you have a stable internet connection
- Ensure you have enough disk space

## What Happens Behind the Scenes

The scripts automatically:
1. ✅ Check and install Docker
2. ✅ Download the KATH container image
3. ✅ Create a workspace folder for your data
4. ✅ Start the KATH application
5. ✅ Open your web browser
6. ✅ Show you the logs so you can monitor the system

## Data Storage

Your analysis data is stored in the `data` folder inside the KATH directory:
- **Windows:** `<KATH_folder>\data`
- **Mac/Linux:** `<KATH_folder>/data`

This folder contains all your work and analysis results. It's safe to back up and will persist between runs.

## System Requirements

- **Minimum RAM:** 4 GB (8 GB recommended)
- **Processor:** Any modern CPU (ARM or x64)
- **Network:** Required for initial download only

## Advanced Usage

### Sample Limits

The scripts are configured to allow **unlimited sample processing**. The `-v` flag ensures all your data is stored locally in the `data` folder and persists across sessions.

### Manual Docker Command

If you need to run KATH manually, use this command from the KATH directory:

```bash
docker run --name kath -v "./data/:/kath/app/back_end/src/workspace/8d8ac610-566d-4ef0-9c22-186b2a5ed793" -it --rm -p 8080:8080 -p 5173:5173 -e DOMAIN=localhost cpu64/kath:final-amd64-fixed
```

### Checking if KATH is Running

```bash
docker ps
```

Look for a container named `kath`.

---

**Need more help?** Check the main README.md or contact the development team.
