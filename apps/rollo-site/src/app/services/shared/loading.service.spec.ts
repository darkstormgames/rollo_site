import { TestBed } from '@angular/core/testing';
import { LoadingService } from './loading.service';

describe('LoadingService', () => {
  let service: LoadingService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [LoadingService]
    });
    service = TestBed.inject(LoadingService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should initialize with not loading', (done) => {
    service.isLoading$.subscribe(loading => {
      expect(loading).toBeFalse();
      done();
    });
  });

  it('should set global loading state', (done) => {
    service.setLoading(true);
    
    service.isLoading$.subscribe(loading => {
      expect(loading).toBeTrue();
      expect(service.isLoading()).toBeTrue();
      done();
    });
  });

  it('should set loading for specific operation', (done) => {
    service.setLoadingForOperation('test-operation', true);
    
    service.isLoading$.subscribe(loading => {
      expect(loading).toBeTrue();
      expect(service.getLoadingForOperation('test-operation')).toBeTrue();
      done();
    });
  });

  it('should clear loading for specific operation', () => {
    service.setLoadingForOperation('test-operation', true);
    expect(service.getLoadingForOperation('test-operation')).toBeTrue();
    
    service.clearLoadingForOperation('test-operation');
    expect(service.getLoadingForOperation('test-operation')).toBeFalse();
  });

  it('should handle multiple operations', () => {
    service.setLoadingForOperation('operation1', true);
    service.setLoadingForOperation('operation2', true);
    
    expect(service.getLoadingForOperation('operation1')).toBeTrue();
    expect(service.getLoadingForOperation('operation2')).toBeTrue();
    expect(service.isLoading()).toBeTrue();
    
    // Clear one operation
    service.clearLoadingForOperation('operation1');
    expect(service.getLoadingForOperation('operation1')).toBeFalse();
    expect(service.getLoadingForOperation('operation2')).toBeTrue();
    expect(service.isLoading()).toBeTrue(); // Should still be loading because operation2 is active
    
    // Clear the second operation
    service.clearLoadingForOperation('operation2');
    expect(service.getLoadingForOperation('operation2')).toBeFalse();
    expect(service.isLoading()).toBeFalse();
  });

  it('should clear all loading states', () => {
    service.setLoadingForOperation('operation1', true);
    service.setLoadingForOperation('operation2', true);
    
    expect(service.isLoading()).toBeTrue();
    
    service.clearAllLoadingStates();
    
    expect(service.isLoading()).toBeFalse();
    expect(service.getLoadingForOperation('operation1')).toBeFalse();
    expect(service.getLoadingForOperation('operation2')).toBeFalse();
  });

  it('should provide observable for specific operation', (done) => {
    const operation = 'test-operation';
    
    service.getLoadingForOperation$(operation).subscribe(loading => {
      if (loading) {
        expect(loading).toBeTrue();
        done();
      }
    });
    
    service.setLoadingForOperation(operation, true);
  });
});