# INCOME Installation Guide

## Windows Desktop Application

### Step 1: Run the installer

1. Double-click `INCOME Setup 1.0.0.exe`
2. If Windows SmartScreen appears, click **More info → Run anyway** (the app is unsigned)
3. Follow the installation wizard
4. Choose installation directory (default: `C:\Program Files\INCOME`)
5. Select whether to create Desktop and Start Menu shortcuts
6. Click **Install** then **Finish**

### Step 2: Launch INCOME

- Double-click the **INCOME** shortcut on your Desktop, or
- Find INCOME in the Start Menu under "INCOME"

### Step 3: Connect to the backend

INCOME requires the Django backend server to be running.

**Option A: Local development (single computer)**

Start the backend before launching the app:
```powershell
cd C:\path\to\Income\backend
.\venv\Scripts\python manage.py runserver
```

The app will connect to `http://localhost:8000` by default.

**Option B: Production server**

After installing, configure the API URL through the app Settings page or by setting `ELECTRON_API_URL` before packaging.

### Step 4: First login

- Username: `admin`
- Password: `Admin@12345!`
- **Change your password immediately.**

---

## Mobile PWA (Android)

1. Open Chrome on your Android device
2. Navigate to your INCOME server URL (e.g., `https://income.yourschool.edu`)
3. Tap the **"Add to Home Screen"** banner, or tap the Chrome menu → **Add to Home Screen**
4. The INCOME icon will appear on your home screen
5. Tap it to open INCOME as a standalone app

---

## Uninstallation

**Windows:**  
Control Panel → Programs and Features → INCOME → Uninstall  
Or: Start Menu → INCOME → Uninstall INCOME

The uninstaller removes the application files. User data stored on the backend server is not affected.
