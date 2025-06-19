import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type Theme = 'light' | 'dark' | 'auto';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly THEME_KEY = 'rollo-theme';
  private currentThemeSubject = new BehaviorSubject<Theme>('auto');
  private activeThemeSubject = new BehaviorSubject<'light' | 'dark'>('light');

  constructor() {
    this.initializeTheme();
    this.setupMediaQueryListener();
  }

  /**
   * Get the current theme setting (light, dark, or auto)
   */
  get currentTheme$(): Observable<Theme> {
    return this.currentThemeSubject.asObservable();
  }

  /**
   * Get the active theme (light or dark, resolving auto)
   */
  get activeTheme$(): Observable<'light' | 'dark'> {
    return this.activeThemeSubject.asObservable();
  }

  /**
   * Get the current theme setting synchronously
   */
  get currentTheme(): Theme {
    return this.currentThemeSubject.value;
  }

  /**
   * Get the active theme synchronously
   */
  get activeTheme(): 'light' | 'dark' {
    return this.activeThemeSubject.value;
  }

  /**
   * Set the theme
   */
  setTheme(theme: Theme): void {
    this.currentThemeSubject.next(theme);
    this.saveTheme(theme);
    this.applyTheme(theme);
  }

  /**
   * Toggle between light and dark themes
   */
  toggleTheme(): void {
    const current = this.currentTheme;
    if (current === 'auto') {
      // If auto, switch to the opposite of current system preference
      const systemPrefersDark = this.getSystemThemePreference();
      this.setTheme(systemPrefersDark ? 'light' : 'dark');
    } else {
      // Toggle between light and dark
      this.setTheme(current === 'light' ? 'dark' : 'light');
    }
  }

  /**
   * Set theme to auto (follow system preference)
   */
  setAutoTheme(): void {
    this.setTheme('auto');
  }

  /**
   * Get system theme preference
   */
  private getSystemThemePreference(): boolean {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  /**
   * Initialize theme on service startup
   */
  private initializeTheme(): void {
    const savedTheme = this.loadTheme();
    this.applyTheme(savedTheme);
  }

  /**
   * Apply the theme to the document
   */
  private applyTheme(theme: Theme): void {
    const body = document.body;
    const root = document.documentElement;
    
    // Remove existing theme classes
    body.classList.remove('theme-light', 'theme-dark', 'theme-auto');
    root.classList.remove('theme-light', 'theme-dark', 'theme-auto');
    
    // Add new theme class
    body.classList.add(`theme-${theme}`);
    root.classList.add(`theme-${theme}`);
    
    // Determine active theme
    let activeTheme: 'light' | 'dark';
    if (theme === 'auto') {
      activeTheme = this.getSystemThemePreference() ? 'dark' : 'light';
    } else {
      activeTheme = theme;
    }
    
    // Apply active theme
    body.classList.add(`active-${activeTheme}`);
    root.classList.add(`active-${activeTheme}`);
    body.classList.remove(`active-${activeTheme === 'light' ? 'dark' : 'light'}`);
    root.classList.remove(`active-${activeTheme === 'light' ? 'dark' : 'light'}`);
    
    // Set data attribute for CSS targeting
    root.setAttribute('data-theme', activeTheme);
    
    // Update active theme subject
    this.activeThemeSubject.next(activeTheme);
    
    // Store the meta tag for theme-color
    this.updateThemeColorMeta(activeTheme);
  }

  /**
   * Update theme-color meta tag
   */
  private updateThemeColorMeta(theme: 'light' | 'dark'): void {
    let metaTag = document.querySelector('meta[name="theme-color"]') as HTMLMetaElement;
    
    if (!metaTag) {
      metaTag = document.createElement('meta');
      metaTag.name = 'theme-color';
      document.head.appendChild(metaTag);
    }
    
    metaTag.content = theme === 'dark' ? '#1a1a1a' : '#ffffff';
  }

  /**
   * Setup listener for system theme changes
   */
  private setupMediaQueryListener(): void {
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      const handleChange = () => {
        if (this.currentTheme === 'auto') {
          this.applyTheme('auto');
        }
      };
      
      // Modern browsers
      if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleChange);
      } else {
        // Legacy browsers
        mediaQuery.addListener(handleChange);
      }
    }
  }

  /**
   * Save theme to localStorage
   */
  private saveTheme(theme: Theme): void {
    try {
      localStorage.setItem(this.THEME_KEY, theme);
    } catch (error) {
      console.warn('Failed to save theme preference:', error);
    }
  }

  /**
   * Load theme from localStorage
   */
  private loadTheme(): Theme {
    try {
      const saved = localStorage.getItem(this.THEME_KEY) as Theme;
      if (saved && ['light', 'dark', 'auto'].includes(saved)) {
        this.currentThemeSubject.next(saved);
        return saved;
      }
    } catch (error) {
      console.warn('Failed to load theme preference:', error);
    }
    
    // Default to auto
    return 'auto';
  }

  /**
   * Get theme display name
   */
  getThemeDisplayName(theme: Theme): string {
    switch (theme) {
      case 'light': return 'Light';
      case 'dark': return 'Dark';
      case 'auto': return 'Auto';
      default: return 'Auto';
    }
  }

  /**
   * Get theme icon
   */
  getThemeIcon(theme: Theme): string {
    switch (theme) {
      case 'light': return '☀️';
      case 'dark': return '🌙';
      case 'auto': return '⚙️';
      default: return '⚙️';
    }
  }

  /**
   * Check if user prefers reduced motion
   */
  prefersReducedMotion(): boolean {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /**
   * Check if user prefers high contrast
   */
  prefersHighContrast(): boolean {
    return window.matchMedia && window.matchMedia('(prefers-contrast: high)').matches;
  }
}