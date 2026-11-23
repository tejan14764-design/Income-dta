/**
 * INCOME – Window bridge types for Electron IPC.
 * Injected by the preload script.
 */

interface IncomeElectronAPI {
  getApiUrl: () => Promise<string>;
  setApiUrl: (url: string) => Promise<{ success: boolean; error?: string }>;
  getPrinterName: () => Promise<string>;
  setPrinterName: (name: string) => Promise<{ success: boolean }>;
  getPrinters: () => Promise<Array<{ name: string; isDefault: boolean }>>;
  printReceipt: (options: { printerName?: string; silent?: boolean }) => Promise<{ success: boolean; failureReason?: string }>;
  savePdf: (pdfData: ArrayBuffer) => Promise<{ success: boolean; path?: string; error?: string }>;
  getAppVersion: () => Promise<string>;
  getPlatform: () => Promise<string>;
  isElectron: boolean;
}

interface Window {
  income?: IncomeElectronAPI;
}
