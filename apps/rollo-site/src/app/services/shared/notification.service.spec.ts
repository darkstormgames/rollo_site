import { TestBed } from '@angular/core/testing';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';
import { NotificationService } from './notification.service';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

describe('NotificationService', () => {
  let service: NotificationService;
  let snackBar: jasmine.SpyObj<MatSnackBar>;
  let dialog: jasmine.SpyObj<MatDialog>;

  beforeEach(() => {
    const snackBarSpy = jasmine.createSpyObj('MatSnackBar', ['openFromComponent', 'open', 'dismiss']);
    const dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);

    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [
        NotificationService,
        { provide: MatSnackBar, useValue: snackBarSpy },
        { provide: MatDialog, useValue: dialogSpy }
      ]
    });

    service = TestBed.inject(NotificationService);
    snackBar = TestBed.inject(MatSnackBar) as jasmine.SpyObj<MatSnackBar>;
    dialog = TestBed.inject(MatDialog) as jasmine.SpyObj<MatDialog>;
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should show success notification', () => {
    const message = 'Operation successful';
    service.showSuccess(message);
    
    expect(snackBar.openFromComponent).toHaveBeenCalled();
  });

  it('should show error notification without auto-dismiss', () => {
    const message = 'Operation failed';
    service.showError(message);
    
    expect(snackBar.openFromComponent).toHaveBeenCalled();
    const config = snackBar.openFromComponent.calls.mostRecent().args[1];
    expect(config.duration).toBe(0); // Should not auto-dismiss
  });

  it('should parse backend error correctly', () => {
    const backendError = {
      error: {
        code: 'VM_CREATE_FAILED',
        message: 'Failed to create virtual machine',
        details: { reason: 'Insufficient resources' },
        category: 'virtualization',
        timestamp: '2024-01-20T10:30:00Z',
        request_id: 'req_123'
      }
    };

    const appError = (service as any).parseApiError(backendError);
    
    expect(appError.code).toBe('VM_CREATE_FAILED');
    expect(appError.message).toBe('Failed to create virtual machine');
    expect(appError.category).toBe('virtualization');
    expect(appError.severity).toBe('high');
    expect(appError.retryable).toBe(false);
  });

  it('should handle API error appropriately', () => {
    const criticalError = {
      error: {
        code: 'INTERNAL_SERVER_ERROR',
        message: 'System error occurred',
        category: 'system'
      }
    };

    spyOn(service, 'showErrorDialog').and.returnValue(Promise.resolve({} as any));
    
    service.handleApiError(criticalError);
    
    expect(service.showErrorDialog).toHaveBeenCalled();
  });

  it('should maintain notification history', () => {
    service.showSuccess('Test message 1');
    service.showError('Test message 2');
    
    const history = service.getNotificationHistory();
    expect(history.length).toBe(2);
    expect(history[0].type).toBe('error'); // Most recent first
    expect(history[1].type).toBe('success');
  });

  it('should clear notification history', () => {
    service.showSuccess('Test message');
    expect(service.getNotificationHistory().length).toBe(1);
    
    service.clearNotificationHistory();
    expect(service.getNotificationHistory().length).toBe(0);
  });
});