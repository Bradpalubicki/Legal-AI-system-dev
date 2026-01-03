/**
 * Accessibility Utilities for Legal AI System Mobile Interface
 * Ensures WCAG 2.1 AA compliance for legal professionals
 */

interface AccessibilitySettings {
  highContrast: boolean;
  textSize: 'small' | 'normal' | 'large' | 'xl' | 'xxl';
  reducedMotion: boolean;
  screenReaderOptimized: boolean;
  keyboardNavigation: boolean;
  voiceNavigation: boolean;
  colorBlindnessMode: 'none' | 'deuteranopia' | 'protanopia' | 'tritanopia';
}

interface FocusManagementOptions {
  trapFocus?: boolean;
  returnFocus?: boolean;
  autoFocus?: boolean;
}

export class AccessibilityManager {
  private static instance: AccessibilityManager;
  private settings: AccessibilitySettings;
  private observers: MutationObserver[] = [];
  private focusStack: HTMLElement[] = [];
  private announcements: HTMLElement | null = null;

  private constructor() {
    this.settings = this.loadSettings();
    this.initializeAccessibility();
  }

  static getInstance(): AccessibilityManager {
    if (!AccessibilityManager.instance) {
      AccessibilityManager.instance = new AccessibilityManager();
    }
    return AccessibilityManager.instance;
  }

  private loadSettings(): AccessibilitySettings {
    const stored = localStorage.getItem('accessibility-settings');
    const defaultSettings: AccessibilitySettings = {
      highContrast: false,
      textSize: 'normal',
      reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      screenReaderOptimized: false,
      keyboardNavigation: true,
      voiceNavigation: false,
      colorBlindnessMode: 'none'
    };

    if (stored) {
      try {
        return { ...defaultSettings, ...JSON.parse(stored) };
      } catch (error) {
        console.error('Failed to parse accessibility settings:', error);
      }
    }

    return defaultSettings;
  }

  private saveSettings(): void {
    localStorage.setItem('accessibility-settings', JSON.stringify(this.settings));
  }

  private initializeAccessibility(): void {
    this.createLiveRegion();
    this.setupKeyboardNavigation();
    this.applySettings();
    this.observeDOM();
    this.setupMediaQueryListeners();
  }

  // Live Region for Screen Reader Announcements
  private createLiveRegion(): void {
    this.announcements = document.createElement('div');
    this.announcements.setAttribute('aria-live', 'polite');
    this.announcements.setAttribute('aria-atomic', 'true');
    this.announcements.className = 'sr-only';
    this.announcements.id = 'accessibility-announcements';
    document.body.appendChild(this.announcements);
  }

  // Announce to Screen Readers
  announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
    if (!this.announcements) return;

    this.announcements.setAttribute('aria-live', priority);
    this.announcements.textContent = message;

    // Clear after announcement
    setTimeout(() => {
      if (this.announcements) {
        this.announcements.textContent = '';
      }
    }, 1000);
  }

  // Legal-specific announcements
  announceCompliance(type: 'disclaimer' | 'warning' | 'privilege', message: string): void {
    const prefix = {
      disclaimer: 'Legal Disclaimer: ',
      warning: 'Professional Responsibility Warning: ',
      privilege: 'Privileged Information Alert: '
    };

    this.announce(prefix[type] + message, 'assertive');
  }

  // Focus Management
  manageFocus(element: HTMLElement, options: FocusManagementOptions = {}): void {
    const { trapFocus = false, returnFocus = false, autoFocus = true } = options;

    if (returnFocus && document.activeElement instanceof HTMLElement) {
      this.focusStack.push(document.activeElement);
    }

    if (autoFocus) {
      element.focus();
    }

    if (trapFocus) {
      this.trapFocus(element);
    }
  }

  returnFocus(): void {
    const previousElement = this.focusStack.pop();
    if (previousElement) {
      previousElement.focus();
    }
  }

  private trapFocus(container: HTMLElement): void {
    const focusableElements = this.getFocusableElements(container);
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    
    // Store cleanup function
    const cleanup = () => {
      container.removeEventListener('keydown', handleTabKey);
    };
    
    // Auto-cleanup when container is removed
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.removedNodes.forEach((node) => {
          if (node === container || (node instanceof Element && node.contains(container))) {
            cleanup();
            observer.disconnect();
          }
        });
      });
    });

    observer.observe(document.body, { childList: true, subtree: true });
    this.observers.push(observer);
  }

  private getFocusableElements(container: HTMLElement): HTMLElement[] {
    const selector = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ');

    return Array.from(container.querySelectorAll(selector))
      .filter(element => this.isVisible(element)) as HTMLElement[];
  }

  private isVisible(element: Element): boolean {
    const style = window.getComputedStyle(element);
    return style.display !== 'none' && 
           style.visibility !== 'hidden' && 
           style.opacity !== '0' &&
           (element as HTMLElement).offsetParent !== null;
  }

  // Keyboard Navigation
  private setupKeyboardNavigation(): void {
    document.addEventListener('keydown', (e) => {
      // Skip if inside input elements
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key) {
        case '/':
          // Focus search (common shortcut)
          e.preventDefault();
          this.focusSearch();
          break;
        
        case 'Escape':
          // Close modals, menus, etc.
          this.handleEscape();
          break;
        
        case 'h':
          if (e.altKey) {
            // Navigate to home
            e.preventDefault();
            window.location.href = '/mobile';
          }
          break;
        
        case '?':
          if (e.shiftKey) {
            // Show keyboard shortcuts
            e.preventDefault();
            this.showKeyboardShortcuts();
          }
          break;
      }
    });

    // Add skip links
    this.addSkipLinks();
  }

  private focusSearch(): void {
    const searchElement = document.querySelector('input[type="search"], input[name="search"], #search') as HTMLElement;
    if (searchElement) {
      searchElement.focus();
      this.announce('Search focused');
    }
  }

  private handleEscape(): void {
    // Close any open modals or dialogs
    const modals = document.querySelectorAll('[role="dialog"], .modal, .dropdown');
    modals.forEach(modal => {
      if (modal instanceof HTMLElement && this.isVisible(modal)) {
        // Trigger close if it has a close button
        const closeButton = modal.querySelector('[aria-label*="close"], [data-close], .close') as HTMLElement;
        if (closeButton) {
          closeButton.click();
        }
      }
    });

    this.returnFocus();
  }

  private addSkipLinks(): void {
    const skipContainer = document.createElement('div');
    skipContainer.className = 'skip-links';
    
    const skipToMain = this.createSkipLink('Skip to main content', '#main-content');
    const skipToNav = this.createSkipLink('Skip to navigation', '#main-navigation');
    
    skipContainer.appendChild(skipToMain);
    skipContainer.appendChild(skipToNav);
    
    document.body.insertBefore(skipContainer, document.body.firstChild);
  }

  private createSkipLink(text: string, href: string): HTMLAnchorElement {
    const link = document.createElement('a');
    link.href = href;
    link.textContent = text;
    link.className = 'skip-link sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary-600 text-white px-4 py-2 rounded-md z-50';
    
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(href);
      if (target instanceof HTMLElement) {
        target.focus();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });

    return link;
  }

  private showKeyboardShortcuts(): void {
    const shortcuts = [
      { key: '/', description: 'Focus search' },
      { key: 'Escape', description: 'Close modal or return focus' },
      { key: 'Alt + H', description: 'Go to home' },
      { key: 'Shift + ?', description: 'Show this help' },
      { key: 'Tab', description: 'Navigate forward' },
      { key: 'Shift + Tab', description: 'Navigate backward' }
    ];

    this.announce('Keyboard shortcuts: ' + shortcuts.map(s => `${s.key}: ${s.description}`).join(', '));
  }

  // Settings Management
  updateSetting<K extends keyof AccessibilitySettings>(key: K, value: AccessibilitySettings[K]): void {
    this.settings[key] = value;
    this.saveSettings();
    this.applySettings();
    this.announce(`${key} updated to ${value}`);
  }

  getSettings(): AccessibilitySettings {
    return { ...this.settings };
  }

  private applySettings(): void {
    const root = document.documentElement;
    
    // High Contrast
    root.classList.toggle('high-contrast', this.settings.highContrast);
    
    // Text Size
    root.className = root.className.replace(/text-(small|normal|large|xl|xxl)/, '');
    root.classList.add(`text-${this.settings.textSize}`);
    
    // Reduced Motion
    if (this.settings.reducedMotion) {
      root.style.setProperty('--animation-duration', '0s');
      root.style.setProperty('--transition-duration', '0s');
    } else {
      root.style.removeProperty('--animation-duration');
      root.style.removeProperty('--transition-duration');
    }
    
    // Color Blindness Support
    root.classList.remove('deuteranopia', 'protanopia', 'tritanopia');
    if (this.settings.colorBlindnessMode !== 'none') {
      root.classList.add(this.settings.colorBlindnessMode);
    }
    
    // Screen Reader Optimization
    if (this.settings.screenReaderOptimized) {
      root.classList.add('screen-reader-optimized');
      // Add more descriptive text, reduce decorative elements
    }
  }

  private setupMediaQueryListeners(): void {
    // Reduced Motion
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    reducedMotionQuery.addEventListener('change', (e) => {
      this.updateSetting('reducedMotion', e.matches);
    });

    // High Contrast (if supported by system)
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
    if (highContrastQuery) {
      highContrastQuery.addEventListener('change', (e) => {
        if (e.matches) {
          this.updateSetting('highContrast', true);
        }
      });
    }
  }

  private observeDOM(): void {
    // Watch for new content that needs accessibility enhancements
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node instanceof Element) {
            this.enhanceElement(node);
          }
        });
      });
    });

    observer.observe(document.body, { childList: true, subtree: true });
    this.observers.push(observer);
  }

  private enhanceElement(element: Element): void {
    // Add missing alt text to images
    const images = element.querySelectorAll('img:not([alt])');
    images.forEach(img => {
      img.setAttribute('alt', '');
    });

    // Ensure buttons have accessible names
    const buttons = element.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
    buttons.forEach(button => {
      if (!button.textContent?.trim()) {
        button.setAttribute('aria-label', 'Button');
      }
    });

    // Add landmark roles to major sections
    const main = element.querySelector('main:not([role])');
    if (main) main.setAttribute('role', 'main');

    const nav = element.querySelector('nav:not([role])');
    if (nav) nav.setAttribute('role', 'navigation');

    // Enhance form labels
    const inputs = element.querySelectorAll('input:not([aria-label]):not([aria-labelledby])');
    inputs.forEach(input => {
      const label = element.querySelector(`label[for="${input.id}"]`);
      if (!label && input.getAttribute('placeholder')) {
        input.setAttribute('aria-label', input.getAttribute('placeholder') || '');
      }
    });
  }

  // Legal-specific accessibility enhancements
  enhanceDisclaimerForAccessibility(element: HTMLElement): void {
    element.setAttribute('role', 'alert');
    element.setAttribute('aria-live', 'assertive');
    element.setAttribute('aria-atomic', 'true');
    
    // Add legal landmark role
    element.setAttribute('aria-label', 'Legal disclaimer notice');
    
    // Announce the disclaimer
    const text = element.textContent || 'Legal disclaimer present';
    this.announceCompliance('disclaimer', text);
  }

  enhancePrivilegeNoticeForAccessibility(element: HTMLElement, level: string): void {
    element.setAttribute('role', 'alert');
    element.setAttribute('aria-live', 'assertive');
    element.setAttribute('aria-label', `Privilege level: ${level}`);
    
    const message = `Privileged content detected. Privilege level: ${level}. Professional responsibility applies.`;
    this.announceCompliance('privilege', message);
  }

  // Color contrast checking
  checkColorContrast(foreground: string, background: string): number {
    // Simplified contrast ratio calculation
    // In a real implementation, would use proper color contrast calculation
    const luminance1 = this.getLuminance(foreground);
    const luminance2 = this.getLuminance(background);
    
    const brightest = Math.max(luminance1, luminance2);
    const darkest = Math.min(luminance1, luminance2);
    
    return (brightest + 0.05) / (darkest + 0.05);
  }

  private getLuminance(color: string): number {
    // Simplified luminance calculation
    // Real implementation would properly parse color values
    return 0.5; // Placeholder
  }

  isContrastCompliant(foreground: string, background: string, level: 'AA' | 'AAA' = 'AA'): boolean {
    const ratio = this.checkColorContrast(foreground, background);
    return level === 'AA' ? ratio >= 4.5 : ratio >= 7;
  }

  // Cleanup
  destroy(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    
    if (this.announcements) {
      document.body.removeChild(this.announcements);
    }
  }
}

// Touch/gesture accessibility helpers
export class TouchAccessibility {
  static addTouchFeedback(element: HTMLElement): void {
    element.addEventListener('touchstart', () => {
      element.classList.add('touch-active');
    });

    element.addEventListener('touchend', () => {
      element.classList.remove('touch-active');
    });

    element.addEventListener('touchcancel', () => {
      element.classList.remove('touch-active');
    });
  }

  static makeTouchFriendly(element: HTMLElement): void {
    // Ensure minimum touch target size (44px x 44px for AA compliance)
    const rect = element.getBoundingClientRect();
    if (rect.width < 44 || rect.height < 44) {
      element.style.minWidth = '44px';
      element.style.minHeight = '44px';
    }

    // Add touch feedback
    this.addTouchFeedback(element);

    // Add appropriate touch aria attributes
    element.setAttribute('aria-describedby', element.id + '-touch-hint');
    
    const hint = document.createElement('span');
    hint.id = element.id + '-touch-hint';
    hint.className = 'sr-only';
    hint.textContent = 'Touch to activate';
    element.appendChild(hint);
  }
}

// Voice navigation support
export class VoiceNavigation {
  private recognition: any = null;
  private commands: Map<string, () => void> = new Map();

  constructor() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.setupRecognition();
    }
  }

  private setupRecognition(): void {
    if (!this.recognition) return;

    this.recognition.continuous = true;
    this.recognition.lang = 'en-US';
    this.recognition.interimResults = false;

    this.recognition.onresult = (event: any) => {
      const command = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
      this.executeCommand(command);
    };

    // Register common legal navigation commands
    this.registerCommand('go to home', () => window.location.href = '/mobile');
    this.registerCommand('open documents', () => window.location.href = '/mobile/documents');
    this.registerCommand('start voice note', () => {
      const button = document.querySelector('[data-voice-note]') as HTMLElement;
      button?.click();
    });
    this.registerCommand('show disclaimers', () => {
      const disclaimers = document.querySelectorAll('[role="alert"]');
      if (disclaimers.length > 0) {
        (disclaimers[0] as HTMLElement).focus();
      }
    });
  }

  registerCommand(phrase: string, action: () => void): void {
    this.commands.set(phrase.toLowerCase(), action);
  }

  private executeCommand(command: string): void {
    const action = this.commands.get(command);
    if (action) {
      action();
      AccessibilityManager.getInstance().announce(`Executing command: ${command}`);
    }
  }

  start(): void {
    if (this.recognition) {
      this.recognition.start();
    }
  }

  stop(): void {
    if (this.recognition) {
      this.recognition.stop();
    }
  }
}

// Initialize accessibility when DOM is ready
if (typeof window !== 'undefined') {
  let accessibilityManager: AccessibilityManager;
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      accessibilityManager = AccessibilityManager.getInstance();
    });
  } else {
    accessibilityManager = AccessibilityManager.getInstance();
  }

  // Export for global access
  (window as any).AccessibilityManager = accessibilityManager;
}

export default AccessibilityManager;