import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ThemeToggleComponent } from './theme-toggle.component';
import { ThemeService, Theme } from '../../../services/theme/theme.service';
import { BehaviorSubject } from 'rxjs';

describe('ThemeToggleComponent', () => {
  let component: ThemeToggleComponent;
  let fixture: ComponentFixture<ThemeToggleComponent>;
  let themeService: jasmine.SpyObj<ThemeService>;
  let currentThemeSubject: BehaviorSubject<Theme>;
  let activeThemeSubject: BehaviorSubject<'light' | 'dark'>;

  beforeEach(async () => {
    currentThemeSubject = new BehaviorSubject<Theme>('auto');
    activeThemeSubject = new BehaviorSubject<'light' | 'dark'>('light');
    
    const themeServiceSpy = jasmine.createSpyObj('ThemeService', [
      'toggleTheme',
      'setTheme',
      'getThemeDisplayName',
      'getThemeIcon'
    ], {
      currentTheme$: currentThemeSubject.asObservable(),
      activeTheme$: activeThemeSubject.asObservable(),
      currentTheme: 'auto',
      activeTheme: 'light'
    });

    await TestBed.configureTestingModule({
      imports: [ThemeToggleComponent],
      providers: [
        { provide: ThemeService, useValue: themeServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ThemeToggleComponent);
    component = fixture.componentInstance;
    themeService = TestBed.inject(ThemeService) as jasmine.SpyObj<ThemeService>;
    
    // Setup spy return values
    themeService.getThemeDisplayName.and.callFake((theme: Theme) => {
      const names = { light: 'Light', dark: 'Dark', auto: 'Auto' };
      return names[theme];
    });
    
    themeService.getThemeIcon.and.callFake((theme: Theme) => {
      const icons = { light: '☀️', dark: '🌙', auto: '⚙️' };
      return icons[theme];
    });
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default values', () => {
    expect(component.mode).toBe('toggle');
    expect(component.compact).toBeFalse();
    expect(component.showLabel).toBeTrue();
    expect(component.showStatus).toBeFalse();
  });

  it('should subscribe to theme changes on init', () => {
    component.ngOnInit();
    
    currentThemeSubject.next('dark');
    expect(component.currentTheme).toBe('dark');
    
    activeThemeSubject.next('dark');
    expect(component.activeTheme).toBe('dark');
  });

  it('should call theme service toggle method', () => {
    component.toggleTheme();
    expect(themeService.toggleTheme).toHaveBeenCalled();
  });

  it('should call theme service setTheme method', () => {
    component.setTheme('dark');
    expect(themeService.setTheme).toHaveBeenCalledWith('dark');
  });

  it('should handle theme change from select dropdown', () => {
    const mockEvent = {
      target: { value: 'light' } as HTMLSelectElement
    } as Event;
    
    spyOn(component, 'setTheme');
    component.onThemeChange(mockEvent);
    
    expect(component.setTheme).toHaveBeenCalledWith('light');
  });

  it('should display toggle button in toggle mode', () => {
    component.mode = 'toggle';
    fixture.detectChanges();
    
    const toggleButton = fixture.nativeElement.querySelector('.toggle-btn');
    expect(toggleButton).toBeTruthy();
  });

  it('should display select dropdown in select mode', () => {
    component.mode = 'select';
    fixture.detectChanges();
    
    const selectElement = fixture.nativeElement.querySelector('.theme-select');
    expect(selectElement).toBeTruthy();
  });

  it('should display button group in buttons mode', () => {
    component.mode = 'buttons';
    fixture.detectChanges();
    
    const buttonGroup = fixture.nativeElement.querySelector('.theme-buttons');
    expect(buttonGroup).toBeTruthy();
    
    const buttons = fixture.nativeElement.querySelectorAll('.theme-buttons .theme-btn');
    expect(buttons.length).toBe(3); // auto, light, dark
  });

  it('should hide labels in compact mode', () => {
    component.compact = true;
    component.mode = 'toggle';
    fixture.detectChanges();
    
    const label = fixture.nativeElement.querySelector('.theme-label');
    expect(label).toBeFalsy();
  });

  it('should show/hide label based on showLabel property', () => {
    component.mode = 'select';
    component.showLabel = true;
    fixture.detectChanges();
    
    let label = fixture.nativeElement.querySelector('.theme-selector-label');
    expect(label).toBeTruthy();
    
    component.showLabel = false;
    fixture.detectChanges();
    
    label = fixture.nativeElement.querySelector('.theme-selector-label');
    expect(label).toBeFalsy();
  });

  it('should show/hide status based on showStatus property', () => {
    component.showStatus = true;
    fixture.detectChanges();
    
    let status = fixture.nativeElement.querySelector('.theme-status');
    expect(status).toBeTruthy();
    
    component.showStatus = false;
    fixture.detectChanges();
    
    status = fixture.nativeElement.querySelector('.theme-status');
    expect(status).toBeFalsy();
  });

  it('should get correct toggle icon for different themes', () => {
    component.currentTheme = 'light';
    expect(component.getToggleIcon()).toBe('🌙');
    
    component.currentTheme = 'dark';
    expect(component.getToggleIcon()).toBe('☀️');
    
    component.currentTheme = 'auto';
    component.activeTheme = 'light';
    expect(component.getToggleIcon()).toBe('🌙');
    
    component.currentTheme = 'auto';
    component.activeTheme = 'dark';
    expect(component.getToggleIcon()).toBe('☀️');
  });

  it('should get correct toggle label for different themes', () => {
    component.currentTheme = 'light';
    expect(component.getToggleLabel()).toBe('Dark mode');
    
    component.currentTheme = 'dark';
    expect(component.getToggleLabel()).toBe('Light mode');
    
    component.currentTheme = 'auto';
    component.activeTheme = 'light';
    expect(component.getToggleLabel()).toBe('Dark mode');
    
    component.currentTheme = 'auto';
    component.activeTheme = 'dark';
    expect(component.getToggleLabel()).toBe('Light mode');
  });

  it('should get correct toggle tooltip for different themes', () => {
    component.currentTheme = 'light';
    expect(component.getToggleTooltip()).toBe('Switch to dark mode');
    
    component.currentTheme = 'dark';
    expect(component.getToggleTooltip()).toBe('Switch to light mode');
    
    component.currentTheme = 'auto';
    component.activeTheme = 'light';
    expect(component.getToggleTooltip()).toBe('Switch to dark mode');
    
    component.currentTheme = 'auto';
    component.activeTheme = 'dark';
    expect(component.getToggleTooltip()).toBe('Switch to light mode');
  });

  it('should get correct aria label for toggle button', () => {
    component.currentTheme = 'light';
    const ariaLabel = component.getToggleAriaLabel();
    expect(ariaLabel).toContain('currently Light');
    expect(ariaLabel).toContain('Switch to dark mode');
  });

  it('should mark active button in button group mode', () => {
    component.mode = 'buttons';
    component.currentTheme = 'dark';
    fixture.detectChanges();
    
    const buttons = fixture.nativeElement.querySelectorAll('.theme-buttons .theme-btn');
    const darkButton = Array.from(buttons).find((btn: Element) => 
      btn.textContent?.includes('Dark')
    ) as HTMLElement;
    
    expect(darkButton.classList.contains('active')).toBeTrue();
  });

  it('should set correct select value', () => {
    component.mode = 'select';
    component.currentTheme = 'dark';
    fixture.detectChanges();
    
    const selectElement = fixture.nativeElement.querySelector('.theme-select') as HTMLSelectElement;
    expect(selectElement.value).toBe('dark');
  });

  it('should clean up subscriptions on destroy', () => {
    component.ngOnInit();
    spyOn(component['destroy$'], 'next');
    spyOn(component['destroy$'], 'complete');
    
    component.ngOnDestroy();
    
    expect(component['destroy$'].next).toHaveBeenCalled();
    expect(component['destroy$'].complete).toHaveBeenCalled();
  });

  it('should handle button clicks in button group', () => {
    component.mode = 'buttons';
    spyOn(component, 'setTheme');
    fixture.detectChanges();
    
    const buttons = fixture.nativeElement.querySelectorAll('.theme-buttons .theme-btn');
    const lightButton = Array.from(buttons).find((btn: Element) => 
      btn.textContent?.includes('Light')
    ) as HTMLElement;
    
    lightButton.click();
    expect(component.setTheme).toHaveBeenCalledWith('light');
  });

  it('should display icons correctly', () => {
    component.mode = 'buttons';
    fixture.detectChanges();
    
    const icons = fixture.nativeElement.querySelectorAll('.theme-icon');
    expect(icons.length).toBeGreaterThan(0);
    
    // Check that theme service getThemeIcon is called
    expect(themeService.getThemeIcon).toHaveBeenCalled();
  });

  it('should show auto indicator in status when theme is auto', () => {
    component.showStatus = true;
    component.currentTheme = 'auto';
    component.activeTheme = 'dark';
    fixture.detectChanges();
    
    const autoIndicator = fixture.nativeElement.querySelector('.auto-indicator');
    expect(autoIndicator).toBeTruthy();
    expect(autoIndicator.textContent).toContain('Dark');
  });

  it('should not show auto indicator when theme is not auto', () => {
    component.showStatus = true;
    component.currentTheme = 'light';
    fixture.detectChanges();
    
    const autoIndicator = fixture.nativeElement.querySelector('.auto-indicator');
    expect(autoIndicator).toBeFalsy();
  });

  it('should handle theme changes from service', () => {
    component.ngOnInit();
    
    currentThemeSubject.next('dark');
    expect(component.currentTheme).toBe('dark');
    
    activeThemeSubject.next('dark');
    expect(component.activeTheme).toBe('dark');
  });

  it('should call theme service methods with correct parameters', () => {
    component.setTheme('light');
    expect(themeService.setTheme).toHaveBeenCalledWith('light');
    
    component.setTheme('dark');
    expect(themeService.setTheme).toHaveBeenCalledWith('dark');
    
    component.setTheme('auto');
    expect(themeService.setTheme).toHaveBeenCalledWith('auto');
  });

  it('should have correct accessibility attributes', () => {
    component.mode = 'buttons';
    fixture.detectChanges();
    
    const buttonGroup = fixture.nativeElement.querySelector('.theme-buttons');
    expect(buttonGroup.getAttribute('role')).toBe('group');
    expect(buttonGroup.getAttribute('aria-label')).toBe('Theme selection');
    
    const buttons = fixture.nativeElement.querySelectorAll('.theme-buttons .theme-btn');
    buttons.forEach((button: HTMLElement) => {
      expect(button.hasAttribute('aria-label')).toBeTrue();
      expect(button.hasAttribute('aria-pressed')).toBeTrue();
    });
  });

  it('should handle select accessibility', () => {
    component.mode = 'select';
    fixture.detectChanges();
    
    const selectElement = fixture.nativeElement.querySelector('.theme-select');
    expect(selectElement.getAttribute('aria-label')).toBe('Select theme');
  });
});