import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  private loadingSubject = new BehaviorSubject<boolean>(false);
  private loadingStates = new Map<string, boolean>();

  public isLoading$ = this.loadingSubject.asObservable();

  constructor() {}

  /**
   * Set global loading state
   */
  setLoading(loading: boolean): void {
    this.loadingSubject.next(loading);
  }

  /**
   * Set loading state for a specific operation
   */
  setLoadingForOperation(operation: string, loading: boolean): void {
    this.loadingStates.set(operation, loading);
    
    // Update global loading state based on any active operations
    const hasActiveOperations = Array.from(this.loadingStates.values()).some(state => state);
    this.loadingSubject.next(hasActiveOperations);
  }

  /**
   * Get loading state for a specific operation
   */
  getLoadingForOperation(operation: string): boolean {
    return this.loadingStates.get(operation) || false;
  }

  /**
   * Clear loading state for a specific operation
   */
  clearLoadingForOperation(operation: string): void {
    this.loadingStates.delete(operation);
    
    // Update global loading state
    const hasActiveOperations = Array.from(this.loadingStates.values()).some(state => state);
    this.loadingSubject.next(hasActiveOperations);
  }

  /**
   * Clear all loading states
   */
  clearAllLoadingStates(): void {
    this.loadingStates.clear();
    this.loadingSubject.next(false);
  }

  /**
   * Check if currently loading
   */
  isLoading(): boolean {
    return this.loadingSubject.value;
  }

  /**
   * Get observable for a specific operation loading state
   */
  getLoadingForOperation$(operation: string): Observable<boolean> {
    return new Observable<boolean>(observer => {
      const updateLoadingState = () => {
        observer.next(this.getLoadingForOperation(operation));
      };

      // Initial emission
      updateLoadingState();

      // Subscribe to global loading changes and filter for this operation
      const subscription = this.isLoading$.subscribe(() => {
        updateLoadingState();
      });

      return () => subscription.unsubscribe();
    });
  }
}