/**
 * Google Analytics gtag type declarations
 */

declare global {
  interface Window {
    gtag: (
      command: 'config' | 'event' | 'js' | 'set',
      targetId: string | Date,
      config?: {
        [key: string]: any;
      }
    ) => void;
    dataLayer: any[];
    fbq: (action: string, ...args: any[]) => void;
  }
}

export {};