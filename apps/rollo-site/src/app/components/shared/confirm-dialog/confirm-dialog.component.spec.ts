import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfirmDialogComponent, ConfirmDialogData } from './confirm-dialog.component';

describe('ConfirmDialogComponent', () => {
  let component: ConfirmDialogComponent;
  let fixture: ComponentFixture<ConfirmDialogComponent>;

  const mockDialogData: ConfirmDialogData = {
    title: 'Test Dialog',
    message: 'Are you sure you want to continue?',
    confirmText: 'Yes',
    cancelText: 'No',
    type: 'warning',
    icon: '⚠️'
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConfirmDialogComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(ConfirmDialogComponent);
    component = fixture.componentInstance;
    component.data = mockDialogData;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with correct default values', () => {
    expect(component.visible).toBeFalse();
    expect(component.closeOnOverlayClick).toBeTrue();
    expect(component.closeOnEscape).toBeTrue();
  });

  it('should display dialog content correctly', () => {
    component.visible = true;
    fixture.detectChanges();

    const titleElement = fixture.nativeElement.querySelector('.dialog-title');
    const messageElement = fixture.nativeElement.querySelector('.dialog-message');
    const iconElement = fixture.nativeElement.querySelector('.dialog-icon');

    expect(titleElement.textContent).toContain('Test Dialog');
    expect(messageElement.textContent).toContain('Are you sure you want to continue?');
    expect(iconElement.textContent).toContain('⚠️');
  });

  it('should show dialog when visible is true', () => {
    component.visible = false;
    fixture.detectChanges();
    
    let overlay = fixture.nativeElement.querySelector('.dialog-overlay');
    expect(overlay.classList.contains('visible')).toBeFalse();

    component.visible = true;
    fixture.detectChanges();
    
    overlay = fixture.nativeElement.querySelector('.dialog-overlay');
    expect(overlay.classList.contains('visible')).toBeTrue();
  });

  it('should emit confirm event on confirm button click', () => {
    spyOn(component.confirm, 'emit');
    spyOn(component, 'close').and.callThrough();
    
    component.visible = true;
    fixture.detectChanges();

    const confirmButton = fixture.nativeElement.querySelector('.btn[class*="btn-warning"]');
    confirmButton.click();

    expect(component.confirm.emit).toHaveBeenCalled();
  });

  it('should emit cancel event on cancel button click', () => {
    spyOn(component.cancel, 'emit');
    spyOn(component, 'close').and.callThrough();
    
    component.visible = true;
    fixture.detectChanges();

    const cancelButton = fixture.nativeElement.querySelector('.btn-secondary');
    cancelButton.click();

    expect(component.cancel.emit).toHaveBeenCalled();
  });

  it('should close on overlay click when enabled', () => {
    spyOn(component.cancel, 'emit');
    component.visible = true;
    component.closeOnOverlayClick = true;
    fixture.detectChanges();

    const overlay = fixture.nativeElement.querySelector('.dialog-overlay');
    overlay.click();

    expect(component.cancel.emit).toHaveBeenCalled();
  });

  it('should not close on overlay click when disabled', () => {
    spyOn(component.cancel, 'emit');
    component.visible = true;
    component.closeOnOverlayClick = false;
    fixture.detectChanges();

    const overlay = fixture.nativeElement.querySelector('.dialog-overlay');
    overlay.click();

    expect(component.cancel.emit).not.toHaveBeenCalled();
  });

  it('should close on escape key when enabled', () => {
    spyOn(component, 'onCancel');
    component.visible = true;
    component.closeOnEscape = true;
    
    const keyEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(keyEvent);

    expect(component.onCancel).toHaveBeenCalled();
  });

  it('should not close on escape key when disabled', () => {
    spyOn(component, 'onCancel');
    component.visible = true;
    component.closeOnEscape = false;
    
    const keyEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(keyEvent);

    expect(component.onCancel).not.toHaveBeenCalled();
  });

  it('should close on enter key', () => {
    spyOn(component, 'onConfirm');
    component.visible = true;
    
    const keyEvent = new KeyboardEvent('keydown', { key: 'Enter' });
    document.dispatchEvent(keyEvent);

    expect(component.onConfirm).toHaveBeenCalled();
  });

  it('should handle tab navigation correctly', () => {
    component.visible = true;
    fixture.detectChanges();

    const focusableElements = component['getFocusableElements']();
    expect(focusableElements.length).toBeGreaterThan(0);
  });

  it('should show/hide programmatically', () => {
    spyOn(component.visibilityChange, 'emit');
    
    component.show();
    expect(component.visible).toBeTrue();
    expect(component.visibilityChange.emit).toHaveBeenCalledWith(true);

    component.hide();
    expect(component.visible).toBeFalse();
    expect(component.visibilityChange.emit).toHaveBeenCalledWith(false);
  });

  it('should show with new data', () => {
    const newData: ConfirmDialogData = {
      title: 'New Title',
      message: 'New message'
    };

    component.show(newData);
    
    expect(component.visible).toBeTrue();
    expect(component.data).toEqual(newData);
  });

  it('should get correct default icons', () => {
    component.data = { ...mockDialogData, type: 'info' };
    expect(component.getDefaultIcon()).toBe('ℹ️');

    component.data = { ...mockDialogData, type: 'warning' };
    expect(component.getDefaultIcon()).toBe('⚠️');

    component.data = { ...mockDialogData, type: 'danger' };
    expect(component.getDefaultIcon()).toBe('🚨');

    component.data = { ...mockDialogData, type: 'success' };
    expect(component.getDefaultIcon()).toBe('✅');
  });

  it('should get correct default confirm button classes', () => {
    component.data = { ...mockDialogData, type: 'info' };
    expect(component.getDefaultConfirmClass()).toBe('btn-primary');

    component.data = { ...mockDialogData, type: 'warning' };
    expect(component.getDefaultConfirmClass()).toBe('btn-warning');

    component.data = { ...mockDialogData, type: 'danger' };
    expect(component.getDefaultConfirmClass()).toBe('btn-danger');

    component.data = { ...mockDialogData, type: 'success' };
    expect(component.getDefaultConfirmClass()).toBe('btn-success');
  });

  it('should show default text when no data provided', () => {
    component.data = null;
    component.visible = true;
    fixture.detectChanges();

    const titleElement = fixture.nativeElement.querySelector('.dialog-title');
    const messageElement = fixture.nativeElement.querySelector('.dialog-message');

    expect(titleElement.textContent).toContain('Confirm Action');
    expect(messageElement.textContent).toContain('Are you sure you want to continue?');
  });

  it('should display details section when provided', () => {
    component.data = {
      ...mockDialogData,
      details: 'Additional details about this action'
    };
    component.visible = true;
    fixture.detectChanges();

    const detailsElement = fixture.nativeElement.querySelector('.dialog-details details p');
    expect(detailsElement.textContent).toContain('Additional details about this action');
  });

  it('should handle click on dialog container without closing', () => {
    spyOn(component, 'onCancel');
    component.visible = true;
    fixture.detectChanges();

    const dialogContainer = fixture.nativeElement.querySelector('.dialog-container');
    dialogContainer.click();

    expect(component.onCancel).not.toHaveBeenCalled();
  });

  it('should close dialog on close button click', () => {
    spyOn(component, 'onCancel');
    component.visible = true;
    fixture.detectChanges();

    const closeButton = fixture.nativeElement.querySelector('.dialog-close');
    closeButton.click();

    expect(component.onCancel).toHaveBeenCalled();
  });

  it('should apply correct dialog type class', () => {
    component.data = { ...mockDialogData, type: 'danger' };
    component.visible = true;
    fixture.detectChanges();

    const dialogContainer = fixture.nativeElement.querySelector('.dialog-container');
    expect(dialogContainer.classList.contains('dialog-danger')).toBeTrue();
  });

  it('should cleanup on destroy', () => {
    spyOn(component, 'cleanup').and.callThrough();
    
    component.ngOnDestroy();
    
    expect(component.cleanup).toHaveBeenCalled();
  });

  it('should prevent body scroll when dialog is open', () => {
    spyOn(component, 'handleDialogOpen').and.callThrough();
    
    component.visible = true;
    component.ngOnChanges();
    
    expect(component.handleDialogOpen).toHaveBeenCalled();
  });

  it('should restore body scroll when dialog is closed', () => {
    spyOn(component, 'handleDialogClose').and.callThrough();
    
    component.visible = false;
    component.ngOnChanges();
    
    expect(component.handleDialogClose).toHaveBeenCalled();
  });

  it('should emit visibility change event', () => {
    spyOn(component.visibilityChange, 'emit');
    
    component['close']();
    
    expect(component.visibilityChange.emit).toHaveBeenCalledWith(false);
  });

  it('should generate unique dialog ID', () => {
    expect(component.dialogId).toMatch(/^dialog-[a-z0-9]{7}$/);
  });

  it('should use custom button classes when provided', () => {
    component.data = {
      ...mockDialogData,
      confirmButtonClass: 'custom-confirm',
      cancelButtonClass: 'custom-cancel'
    };
    component.visible = true;
    fixture.detectChanges();

    const confirmButton = fixture.nativeElement.querySelector('.custom-confirm');
    const cancelButton = fixture.nativeElement.querySelector('.custom-cancel');

    expect(confirmButton).toBeTruthy();
    expect(cancelButton).toBeTruthy();
  });
});