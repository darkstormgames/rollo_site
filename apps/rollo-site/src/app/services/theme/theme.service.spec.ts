import { TestBed } from '@angular/core/testing';
import { ThemeService, Theme } from './theme.service';

describe('ThemeService', () => {
  let service: ThemeService;
  let mockLocalStorage: { [key: string]: string };
  let mockMatchMedia: jasmine.Spy;

  beforeEach(() => {
    mockLocalStorage = {};
    
    spyOn(localStorage, 'getItem').and.callFake((key: string) => mockLocalStorage[key] || null);
    spyOn(localStorage, 'setItem').and.callFake((key: string, value: string) => {
      mockLocalStorage[key] = value;
    });

    mockMatchMedia = jasmine.createSpy('matchMedia').and.returnValue({
      matches: false,
      addEventListener: jasmine.createSpy('addEventListener'),
      addListener: jasmine.createSpy('addListener')
    });
    Object.defineProperty(window, 'matchMedia', { value: mockMatchMedia });

    TestBed.configureTestingModule({});
    service = TestBed.inject(ThemeService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should initialize with auto theme by default', () => {
    expect(service.currentTheme).toBe('auto');
  });

  it('should load theme from localStorage', () => {
    mockLocalStorage['rollo-theme'] = 'dark';
    
    const newService = TestBed.inject(ThemeService);
    expect(newService.currentTheme).toBe('dark');
  });

  it('should save theme to localStorage', () => {
    service.setTheme('dark');
    expect(mockLocalStorage['rollo-theme']).toBe('dark');
  });

  it('should set theme and update observables', (done) => {
    service.currentTheme$.subscribe(theme => {
      if (theme === 'light') {
        expect(theme).toBe('light');
        done();
      }
    });
    
    service.setTheme('light');
  });

  it('should toggle theme correctly', () => {
    service.setTheme('light');
    service.toggleTheme();
    expect(service.currentTheme).toBe('dark');
    
    service.toggleTheme();
    expect(service.currentTheme).toBe('light');
  });

  it('should toggle from auto to opposite of system preference', () => {
    mockMatchMedia.and.returnValue({
      matches: true, // System prefers dark
      addEventListener: jasmine.createSpy(),
      addListener: jasmine.createSpy()
    });
    
    service.setTheme('auto');
    service.toggleTheme();
    expect(service.currentTheme).toBe('light'); // Opposite of system dark
  });

  it('should set auto theme', () => {
    service.setAutoTheme();
    expect(service.currentTheme).toBe('auto');
  });

  it('should apply theme classes to body and root', () => {
    const body = document.body;
    const root = document.documentElement;
    
    service.setTheme('dark');
    
    expect(body.classList.contains('theme-dark')).toBeTrue();
    expect(body.classList.contains('active-dark')).toBeTrue();
    expect(root.classList.contains('theme-dark')).toBeTrue();
    expect(root.classList.contains('active-dark')).toBeTrue();
    expect(root.getAttribute('data-theme')).toBe('dark');
  });

  it('should resolve auto theme based on system preference', () => {
    mockMatchMedia.and.returnValue({
      matches: true, // System prefers dark
      addEventListener: jasmine.createSpy(),
      addListener: jasmine.createSpy()
    });
    
    service.setTheme('auto');
    expect(service.activeTheme).toBe('dark');
  });

  it('should update theme-color meta tag', () => {
    service.setTheme('dark');
    
    const metaTag = document.querySelector('meta[name="theme-color"]') as HTMLMetaElement;
    expect(metaTag.content).toBe('#1a1a1a');
    
    service.setTheme('light');
    expect(metaTag.content).toBe('#ffffff');
  });

  it('should get theme display names correctly', () => {
    expect(service.getThemeDisplayName('light')).toBe('Light');
    expect(service.getThemeDisplayName('dark')).toBe('Dark');
    expect(service.getThemeDisplayName('auto')).toBe('Auto');
  });

  it('should get theme icons correctly', () => {
    expect(service.getThemeIcon('light')).toBe('☀️');
    expect(service.getThemeIcon('dark')).toBe('🌙');
    expect(service.getThemeIcon('auto')).toBe('⚙️');
  });

  it('should detect system preferences correctly', () => {
    mockMatchMedia.and.returnValue({ matches: true });
    expect(service['getSystemThemePreference']()).toBeTrue();
    
    mockMatchMedia.and.returnValue({ matches: false });
    expect(service['getSystemThemePreference']()).toBeFalse();
  });

  it('should check for reduced motion preference', () => {
    mockMatchMedia.and.returnValue({ matches: true });
    expect(service.prefersReducedMotion()).toBeTrue();
  });

  it('should check for high contrast preference', () => {
    mockMatchMedia.and.returnValue({ matches: true });
    expect(service.prefersHighContrast()).toBeTrue();
  });

  it('should handle localStorage errors gracefully', () => {
    spyOn(localStorage, 'setItem').and.throwError('Storage error');
    spyOn(console, 'warn');
    
    service.setTheme('dark');
    expect(console.warn).toHaveBeenCalledWith('Failed to save theme preference:', jasmine.any(Error));
  });

  it('should handle invalid saved theme gracefully', () => {
    mockLocalStorage['rollo-theme'] = 'invalid-theme';
    
    const newService = TestBed.inject(ThemeService);
    expect(newService.currentTheme).toBe('auto');
  });

  it('should setup media query listener for auto theme updates', () => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: jasmine.createSpy('addEventListener'),
      addListener: jasmine.createSpy('addListener')
    };
    
    mockMatchMedia.and.returnValue(mockMediaQuery);
    
    service['setupMediaQueryListener']();
    
    expect(mockMatchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)');
    expect(mockMediaQuery.addEventListener).toHaveBeenCalled();
  });

  it('should update theme when system preference changes and theme is auto', () => {
    service.setTheme('auto');
    spyOn(service, 'applyTheme').and.callThrough();
    
    const mockMediaQuery = {
      matches: false,
      addEventListener: jasmine.createSpy('addEventListener'),
      addListener: jasmine.createSpy('addListener')
    };
    
    mockMatchMedia.and.returnValue(mockMediaQuery);
    service['setupMediaQueryListener']();
    
    // Simulate media query change
    const changeHandler = mockMediaQuery.addEventListener.calls.argsFor(0)[1];
    changeHandler();
    
    expect(service.applyTheme).toHaveBeenCalledWith('auto');
  });

  it('should not update theme when system preference changes and theme is not auto', () => {
    service.setTheme('light');
    spyOn(service, 'applyTheme').and.callThrough();
    
    const mockMediaQuery = {
      matches: false,
      addEventListener: jasmine.createSpy('addEventListener'),
      addListener: jasmine.createSpy('addListener')
    };
    
    mockMatchMedia.and.returnValue(mockMediaQuery);
    service['setupMediaQueryListener']();
    
    // Reset the spy after initial setup
    (service.applyTheme as jasmine.Spy).calls.reset();
    
    // Simulate media query change
    const changeHandler = mockMediaQuery.addEventListener.calls.argsFor(0)[1];
    changeHandler();
    
    expect(service.applyTheme).not.toHaveBeenCalled();
  });

  it('should fallback to addListener for legacy browsers', () => {
    const mockMediaQuery = {
      matches: false,
      addEventListener: undefined,
      addListener: jasmine.createSpy('addListener')
    };
    
    mockMatchMedia.and.returnValue(mockMediaQuery);
    
    service['setupMediaQueryListener']();
    
    expect(mockMediaQuery.addListener).toHaveBeenCalled();
  });

  it('should handle missing matchMedia gracefully', () => {
    Object.defineProperty(window, 'matchMedia', { value: undefined });
    
    expect(() => service['getSystemThemePreference']()).not.toThrow();
    expect(() => service['setupMediaQueryListener']()).not.toThrow();
  });

  it('should remove existing theme classes before applying new ones', () => {
    const body = document.body;
    const root = document.documentElement;
    
    // Add existing classes
    body.classList.add('theme-light', 'active-light');
    root.classList.add('theme-light', 'active-light');
    
    service.setTheme('dark');
    
    expect(body.classList.contains('theme-light')).toBeFalse();
    expect(body.classList.contains('active-light')).toBeFalse();
    expect(body.classList.contains('theme-dark')).toBeTrue();
    expect(body.classList.contains('active-dark')).toBeTrue();
  });

  it('should emit activeTheme changes when auto resolves differently', (done) => {
    let emissionCount = 0;
    service.activeTheme$.subscribe(theme => {
      emissionCount++;
      if (emissionCount === 2) {
        expect(theme).toBe('dark');
        done();
      }
    });
    
    // Start with light preference
    mockMatchMedia.and.returnValue({ matches: false });
    service.setTheme('auto');
    
    // Change to dark preference
    mockMatchMedia.and.returnValue({ matches: true });
    service.setTheme('auto');
  });
});