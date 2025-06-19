import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ThemeService, Theme } from '../../../services/theme/theme.service';
import { Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="theme-toggle" [class.compact]="compact">
      <!-- Simple toggle button -->
      <button 
        *ngIf="mode === 'toggle'"
        class="theme-btn toggle-btn"
        (click)="toggleTheme()"
        [title]="getToggleTooltip()"
        [attr.aria-label]="getToggleAriaLabel()">
        <span class="theme-icon" [attr.aria-hidden]="true">
          {{ getToggleIcon() }}
        </span>
        <span *ngIf="!compact" class="theme-label">
          {{ getToggleLabel() }}
        </span>
      </button>

      <!-- Dropdown selector -->
      <div *ngIf="mode === 'select'" class="theme-selector">
        <label *ngIf="showLabel" class="theme-selector-label">
          Theme:
        </label>
        <select 
          class="theme-select"
          [value]="currentTheme"
          (change)="onThemeChange($event)"
          [attr.aria-label]="'Select theme'">
          <option value="auto">🌗 Auto</option>
          <option value="light">☀️ Light</option>
          <option value="dark">🌙 Dark</option>
        </select>
      </div>

      <!-- Button group -->
      <div *ngIf="mode === 'buttons'" class="theme-buttons" role="group" [attr.aria-label]="'Theme selection'">
        <button
          *ngFor="let theme of availableThemes"
          class="theme-btn"
          [class.active]="currentTheme === theme"
          (click)="setTheme(theme)"
          [title]="themeService.getThemeDisplayName(theme)"
          [attr.aria-label]="'Set theme to ' + themeService.getThemeDisplayName(theme)"
          [attr.aria-pressed]="currentTheme === theme">
          <span class="theme-icon" [attr.aria-hidden]="true">
            {{ themeService.getThemeIcon(theme) }}
          </span>
          <span *ngIf="!compact" class="theme-label">
            {{ themeService.getThemeDisplayName(theme) }}
          </span>
        </button>
      </div>

      <!-- Status indicator -->
      <div *ngIf="showStatus" class="theme-status" [attr.aria-live]="'polite'">
        <span class="active-theme-indicator">
          {{ themeService.getThemeIcon(activeTheme) }}
          {{ themeService.getThemeDisplayName(activeTheme) }}
          <span *ngIf="currentTheme === 'auto'" class="auto-indicator">
            ({{ activeTheme === 'light' ? 'Light' : 'Dark' }})
          </span>
        </span>
      </div>
    </div>
  `,
  styleUrls: ['./theme-toggle.component.css']
})
export class ThemeToggleComponent implements OnInit, OnDestroy {
  @Input() mode: 'toggle' | 'select' | 'buttons' = 'toggle';
  @Input() compact = false;
  @Input() showLabel = true;
  @Input() showStatus = false;

  currentTheme: Theme = 'auto';
  activeTheme: 'light' | 'dark' = 'light';
  availableThemes: Theme[] = ['auto', 'light', 'dark'];

  private destroy$ = new Subject<void>();

  constructor(public themeService: ThemeService) {}

  ngOnInit() {
    // Subscribe to theme changes
    this.themeService.currentTheme$
      .pipe(takeUntil(this.destroy$))
      .subscribe(theme => {
        this.currentTheme = theme;
      });

    this.themeService.activeTheme$
      .pipe(takeUntil(this.destroy$))
      .subscribe(theme => {
        this.activeTheme = theme;
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  toggleTheme() {
    this.themeService.toggleTheme();
  }

  setTheme(theme: Theme) {
    this.themeService.setTheme(theme);
  }

  onThemeChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const theme = target.value as Theme;
    this.setTheme(theme);
  }

  getToggleIcon(): string {
    switch (this.currentTheme) {
      case 'light': return '🌙';
      case 'dark': return '☀️';
      case 'auto': 
      default: 
        return this.activeTheme === 'light' ? '🌙' : '☀️';
    }
  }

  getToggleLabel(): string {
    switch (this.currentTheme) {
      case 'light': return 'Dark mode';
      case 'dark': return 'Light mode';
      case 'auto':
      default:
        return this.activeTheme === 'light' ? 'Dark mode' : 'Light mode';
    }
  }

  getToggleTooltip(): string {
    switch (this.currentTheme) {
      case 'light': return 'Switch to dark mode';
      case 'dark': return 'Switch to light mode';
      case 'auto':
      default:
        return `Switch to ${this.activeTheme === 'light' ? 'dark' : 'light'} mode`;
    }
  }

  getToggleAriaLabel(): string {
    return `Theme toggle, currently ${this.themeService.getThemeDisplayName(this.currentTheme)}. ${this.getToggleTooltip()}`;
  }
}