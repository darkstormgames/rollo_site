import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should make GET request', () => {
    const mockData = { test: 'data' };
    
    service.get('/test').subscribe(data => {
      expect(data).toEqual(mockData);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/test');
    expect(req.request.method).toBe('GET');
    req.flush(mockData);
  });

  it('should make POST request', () => {
    const mockData = { id: 1 };
    const postData = { name: 'test' };
    
    service.post('/test', postData).subscribe(data => {
      expect(data).toEqual(mockData);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/test');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(postData);
    req.flush(mockData);
  });

  it('should make PUT request', () => {
    const mockData = { id: 1, updated: true };
    const putData = { name: 'updated' };
    
    service.put('/test/1', putData).subscribe(data => {
      expect(data).toEqual(mockData);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/test/1');
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual(putData);
    req.flush(mockData);
  });

  it('should make DELETE request', () => {
    const mockData = { message: 'deleted' };
    
    service.delete('/test/1').subscribe(data => {
      expect(data).toEqual(mockData);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/test/1');
    expect(req.request.method).toBe('DELETE');
    req.flush(mockData);
  });

  it('should handle query parameters', () => {
    const params = { page: 1, per_page: 10, filter: 'test' };
    
    service.get('/test', params).subscribe();

    const req = httpMock.expectOne('http://localhost:8000/api/test?page=1&per_page=10&filter=test');
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('should handle errors', () => {
    const errorResponse = { error: 'Test error', code: 'TEST_ERROR' };
    
    service.get('/test').subscribe({
      next: () => fail('Should have failed'),
      error: (error) => {
        expect(error.error).toBe('Test error');
        expect(error.code).toBe('TEST_ERROR');
      }
    });

    const req = httpMock.expectOne('http://localhost:8000/api/test');
    req.flush(errorResponse, { status: 400, statusText: 'Bad Request' });
  });
});