/**
 * INCOME – Electron Main Process
 * - contextIsolation: true  (renderer cannot access Node APIs)
 * - nodeIntegration: false  (renderer has no direct Node access)
 * - sandbox: false          (required for preload to use contextBridge)
 * - Uses electron-store v8  (CommonJS compatible)
 */

import { app, BrowserWindow, ipcMain, dialog, shell } from "electron";
import * as path from "path";
import * as fs from "fs";
import Store from "electron-store";

interface StoreSchema {
  apiUrl: string;
  printerName: string;
}

const store = new Store<StoreSchema>({
  defaults: {
    apiUrl: process.env.ELECTRON_API_URL ?? "",
    printerName: "",
  },
});

const isDev = process.env.NODE_ENV === "development" || !app.isPackaged;
const RENDERER_URL = isDev ? "http://localhost:5173" : undefined;

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1024,
    minHeight: 640,
    title: "Bright Future Pre-School",
    backgroundColor: "#0f172a",
    show: false,
    // Use the generated icon
    icon: path.join(__dirname, "../assets/icon.png"),
    webPreferences: {
      contextIsolation: true,   // Keep renderer isolated from Node
      nodeIntegration: false,   // Renderer cannot use Node APIs
      sandbox: false,           // Must be false for contextBridge in preload
      webSecurity: !isDev,      // Relax only in dev to allow localhost API calls
      allowRunningInsecureContent: false,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  // Remove the default menu in production
  if (!isDev) {
    mainWindow.setMenuBarVisibility(false);
  }

  if (RENDERER_URL) {
    // Development: load from Vite dev server
    mainWindow.loadURL(RENDERER_URL);
    mainWindow.webContents.openDevTools();
  } else {
    // Production: load the bundled index.html
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
  }

  // Show only when fully loaded — prevents white flash
  mainWindow.once("ready-to-show", () => {
    mainWindow!.show();
    mainWindow!.focus();
  });

  // Open external links in the system browser, not in Electron
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

// ---- IPC Handlers ----

ipcMain.handle("get-api-url", () => {
  return store.get("apiUrl");
});

ipcMain.handle("set-api-url", (_, url: string) => {
  if (
    typeof url === "string" &&
    (url.startsWith("http://") || url.startsWith("https://"))
  ) {
    store.set("apiUrl", url);
    return { success: true };
  }
  return { success: false, error: "Invalid URL — must start with http:// or https://" };
});

ipcMain.handle("get-printer-name", () => store.get("printerName"));

ipcMain.handle("set-printer-name", (_, name: string) => {
  store.set("printerName", name);
  return { success: true };
});

ipcMain.handle("get-printers", async () => {
  if (!mainWindow) return [];
  const printers = await mainWindow.webContents.getPrintersAsync();
  return printers.map((p) => ({ name: p.name, isDefault: p.isDefault }));
});

ipcMain.handle(
  "print-receipt",
  async (_, options: { printerName?: string; silent?: boolean }) => {
    if (!mainWindow) return { success: false, error: "No window" };
    const printerName = options.printerName || store.get("printerName");

    return new Promise((resolve) => {
      mainWindow!.webContents.print(
        {
          silent: options.silent ?? true,
          printBackground: true,
          deviceName: printerName || undefined,
          // 80mm thermal receipt size in microns
          pageSize: { width: 80000, height: 200000 },
          margins: { marginType: "none" },
          copies: 1,
          collate: true,
        },
        (success, failureReason) => {
          resolve({ success, failureReason: failureReason ?? null });
        }
      );
    });
  }
);

ipcMain.handle("save-pdf", async (_, pdfData: ArrayBuffer) => {
  const { canceled, filePath } = await dialog.showSaveDialog({
    title: "Save Receipt PDF",
    defaultPath: "receipt.pdf",
    filters: [{ name: "PDF Files", extensions: ["pdf"] }],
  });
  if (canceled || !filePath) return { success: false };
  try {
    fs.writeFileSync(filePath, Buffer.from(pdfData));
    return { success: true, path: filePath };
  } catch (err) {
    return { success: false, error: String(err) };
  }
});

ipcMain.handle("get-app-version", () => app.getVersion());
ipcMain.handle("get-platform", () => process.platform);
