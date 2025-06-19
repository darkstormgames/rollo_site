import { Component, Input, Output, EventEmitter, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface ConfirmDialogData {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'info' | 'warning' | 'danger' | 'success';
  icon?: string;
  details?: string;
  confirmButtonClass?: string;
  cancelButtonClass?: string;
}

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dialog-overlay" 
         [class.visible]="visible"
         (click)="onOverlayClick($event)"
         role="dialog"
         [attr.aria-modal]="visible"
         [attr.aria-labelledby]="dialogId + '-title'"
         [attr.aria-describedby]="dialogId + '-message'">
      
      <div #dialogElement 
           class="dialog-container"
           [class]="'dialog-' + (data?.type || 'info')"
           (click)="$event.stopPropagation()"
           tabindex="-1">
        
        <!-- Dialog Header -->
        <div class="dialog-header">
          <div class="dialog-title-container">
            <span *ngIf="data?.icon || getDefaultIcon()" 
                  class="dialog-icon" 
                  [attr.aria-hidden]="true">
              {{ data?.icon || getDefaultIcon() }}
            </span>
            <h2 [id]="dialogId + '-title'" class="dialog-title">
              {{ data?.title || 'Confirm Action' }}
            </h2>
          </div>
          
          <button class="dialog-close"
                  (click)="onCancel()"
                  [attr.aria-label]="'Close dialog'"
                  title="Close">
            <span aria-hidden="true">×</span>
          </button>
        </div>

        <!-- Dialog Body -->
        <div class="dialog-body">
          <p [id]="dialogId + '-message'" class="dialog-message">
            {{ data?.message || 'Are you sure you want to continue?' }}
          </p>
          
          <div *ngIf="data?.details" class="dialog-details">
            <details>
              <summary>More details</summary>
              <p>{{ data!.details }}</p>
            </details>
          </div>
        </div>

        <!-- Dialog Footer -->
        <div class="dialog-footer">
          <button #cancelButton
                  class="btn"
                  [class]="data?.cancelButtonClass || 'btn-secondary'"
                  (click)="onCancel()"
                  [attr.aria-label]="data?.cancelText || 'Cancel'">
            {{ data?.cancelText || 'Cancel' }}
          </button>
          
          <button #confirmButton
                  class="btn"
                  [class]="data?.confirmButtonClass || getDefaultConfirmClass()"
                  (click)="onConfirm()"
                  [attr.aria-label]="data?.confirmText || 'Confirm'">
            {{ data?.confirmText || 'Confirm' }}
          </button>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./confirm-dialog.component.css']
})
export class ConfirmDialogComponent implements OnInit, AfterViewInit {
  @Input() visible = false;
  @Input() data: ConfirmDialogData | null = null;
  @Input() closeOnOverlayClick = true;
  @Input() closeOnEscape = true;
  
  @Output() confirm = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();
  @Output() visibilityChange = new EventEmitter<boolean>();

  @ViewChild('dialogElement') dialogElement!: ElementRef;
  @ViewChild('confirmButton') confirmButton!: ElementRef;
  @ViewChild('cancelButton') cancelButton!: ElementRef;

  dialogId = `dialog-${Math.random().toString(36).substring(2, 9)}`;
  private previousActiveElement: Element | null = null;
  private keydownListener?: (event: KeyboardEvent) => void;

  ngOnInit() {
    this.setupKeyboardListeners();
  }

  ngAfterViewInit() {
    if (this.visible) {
      this.handleDialogOpen();
    }
  }

  ngOnChanges() {
    if (this.visible) {
      this.handleDialogOpen();
    } else {
      this.handleDialogClose();
    }
  }

  ngOnDestroy() {
    this.cleanup();
  }

  private setupKeyboardListeners() {
    this.keydownListener = (event: KeyboardEvent) => {
      if (!this.visible) return;

      switch (event.key) {
        case 'Escape':
          if (this.closeOnEscape) {
            event.preventDefault();
            this.onCancel();
          }
          break;
        
        case 'Enter':
          // Only trigger confirm if focus is on confirm button or no focusable element
          const activeElement = document.activeElement;
          if (activeElement === this.confirmButton?.nativeElement || 
              !this.isInDialog(activeElement)) {
            event.preventDefault();
            this.onConfirm();
          }
          break;
        
        case 'Tab':
          this.handleTabNavigation(event);
          break;
      }
    };

    document.addEventListener('keydown', this.keydownListener);
  }

  private handleTabNavigation(event: KeyboardEvent) {
    if (!this.dialogElement?.nativeElement) return;

    const focusableElements = this.getFocusableElements();
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (event.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        event.preventDefault();
        lastElement?.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        event.preventDefault();
        firstElement?.focus();
      }
    }
  }

  private getFocusableElements(): HTMLElement[] {
    if (!this.dialogElement?.nativeElement) return [];

    const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const elements = this.dialogElement.nativeElement.querySelectorAll(selector);
    
    return Array.from(elements).filter((element): element is HTMLElement => {
      const htmlElement = element as HTMLElement;
      const isDisabled = (htmlElement as any).disabled;
      return !isDisabled && 
             htmlElement.offsetWidth > 0 && 
             htmlElement.offsetHeight > 0 &&
             getComputedStyle(htmlElement).visibility !== 'hidden';
    });
  }

  private isInDialog(element: Element | null): boolean {
    if (!element || !this.dialogElement?.nativeElement) return false;
    return this.dialogElement.nativeElement.contains(element);
  }

  private handleDialogOpen() {
    // Store currently focused element
    this.previousActiveElement = document.activeElement;
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Focus the dialog
    setTimeout(() => {
      const focusableElements = this.getFocusableElements();
      const elementToFocus = focusableElements.find(el => 
        el.classList.contains('btn-primary') || 
        el === this.confirmButton?.nativeElement
      ) || focusableElements[0] || this.dialogElement?.nativeElement;
      
      elementToFocus?.focus();
    }, 100);
  }

  private handleDialogClose() {
    // Restore body scroll
    document.body.style.overflow = '';
    
    // Restore focus to previously active element
    if (this.previousActiveElement instanceof HTMLElement) {
      this.previousActiveElement.focus();
    }
    
    this.previousActiveElement = null;
  }

  private cleanup() {
    if (this.keydownListener) {
      document.removeEventListener('keydown', this.keydownListener);
    }
    
    // Restore body scroll in case component is destroyed while dialog is open
    document.body.style.overflow = '';
  }

  onOverlayClick(event: MouseEvent) {
    if (this.closeOnOverlayClick && event.target === event.currentTarget) {
      this.onCancel();
    }
  }

  onConfirm() {
    this.confirm.emit();
    this.close();
  }

  onCancel() {
    this.cancel.emit();
    this.close();
  }

  private close() {
    this.visible = false;
    this.visibilityChange.emit(false);
    this.handleDialogClose();
  }

  show(data?: ConfirmDialogData) {
    if (data) {
      this.data = data;
    }
    this.visible = true;
    this.visibilityChange.emit(true);
  }

  hide() {
    this.close();
  }

  getDefaultIcon(): string {
    switch (this.data?.type) {
      case 'warning': return '⚠️';
      case 'danger': return '🚨';
      case 'success': return '✅';
      case 'info': 
      default: return 'ℹ️';
    }
  }

  getDefaultConfirmClass(): string {
    switch (this.data?.type) {
      case 'danger': return 'btn-danger';
      case 'warning': return 'btn-warning';
      case 'success': return 'btn-success';
      case 'info':
      default: return 'btn-primary';
    }
  }
}