import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, fromEvent, merge } from 'rxjs';
import { map, startWith, distinctUntilChanged } from 'rxjs/operators';
import { NotificationService } from './notification.service';

@Injectable({
  providedIn: 'root'
})
export class OfflineDetectionService {
  private onlineSubject = new BehaviorSubject<boolean>(navigator.onLine);
  public isOnline$ = this.onlineSubject.asObservable();
  
  private offlineNotificationShown = false;

  constructor(private notificationService: NotificationService) {
    this.setupOnlineDetection();
  }

  private setupOnlineDetection(): void {
    // Listen to online/offline events
    const online$ = fromEvent(window, 'online').pipe(map(() => true));
    const offline$ = fromEvent(window, 'offline').pipe(map(() => false));
    
    merge(online$, offline$)
      .pipe(
        startWith(navigator.onLine),
        distinctUntilChanged()
      )
      .subscribe(isOnline => {
        this.onlineSubject.next(isOnline);
        this.handleConnectionChange(isOnline);
      });
  }

  private handleConnectionChange(isOnline: boolean): void {
    if (isOnline) {
      if (this.offlineNotificationShown) {
        this.notificationService.showSuccess('Connection restored');
        this.offlineNotificationShown = false;
      }
    } else {
      this.notificationService.showWarning(
        'You are currently offline. Some features may not be available.',
        { duration: 0 } // Don't auto-dismiss
      );
      this.offlineNotificationShown = true;
    }
  }

  isOnline(): boolean {
    return this.onlineSubject.value;
  }

  isOffline(): boolean {
    return !this.isOnline();
  }

  /**
   * Check if the user is online and show error if not
   */
  requireOnline(action: string = 'perform this action'): boolean {
    if (this.isOffline()) {
      this.notificationService.showError(
        `You need to be online to ${action}. Please check your internet connection.`
      );
      return false;
    }
    return true;
  }
}