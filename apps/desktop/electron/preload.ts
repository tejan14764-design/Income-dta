/**
 * INCOME – Electron Preload Script
 * Exposes a secure, typed bridge between the renderer and the main process.
 * Never exposes raw Node.js or Electron APIs to the renderer.
 */

import { contextBridge, ipcRenderer } from "electron";

// Define the allowed API surface
const incomeAPI = {
  // Config
  getApiUrl: (): Promise<string> => ipcRenderer.invoke("get-api-url"),
  setApiUrl: (url: string): Promise<{ success: boolean; error?: string }> =>
    ipcRenderer.invoke("set-api-url", url),

  // Printers
  getPrinterName: (): Promise<string> => ipcRenderer.invoke("get-printer-name"),
  setPrinterName: (name: string): Promise<{ success: boolean }> =>
    ipcRenderer.invoke("set-printer-name", name),
  getPrinters: (): Promise<Array<{ name: string; isDefault: boolean }>> =>
    ipcRenderer.invoke("get-printers"),

  // Printing
  printReceipt: (options: {
    printerName?: string;
    silent?: boolean;
  }): Promise<{ success: boolean; failureReason?: string }> =>
    ipcRenderer.invoke("print-receipt", options),

  // PDF
  savePdf: (pdfData: ArrayBuffer): Promise<{ success: boolean; path?: string; error?: string }> =>
    ipcRenderer.invoke("save-pdf", pdfData),

  // App info
  getAppVersion: (): Promise<string> => ipcRenderer.invoke("get-app-version"),
  getPlatform: (): Promise<string> => ipcRenderer.invoke("get-platform"),

  // Environment
  isElectron: true,
};

// Expose to renderer under window.income
contextBridge.exposeInMainWorld("income", incomeAPI);

// TypeScript declaration (also in src/electron.d.ts on the renderer side)
export type IncomeAPI = typeof incomeAPI;
