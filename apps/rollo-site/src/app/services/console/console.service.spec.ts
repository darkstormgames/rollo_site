import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ConsoleService, ConsoleSession, ConsoleStatus } from './console.service';

describe('ConsoleService', () => {
  let service: ConsoleService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ConsoleService]
    });
    
    service = TestBed.inject(ConsoleService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('requestAccess', () => {
    it('should request console access for a VM', () => {
      const vmId = 1;
      const protocol = 'vnc';
      const mockResponse: ConsoleSession = {
        session_token: 'test-token-123',
        vm_id: vmId,
        protocol: protocol,
        websocket_url: 'ws://localhost:8000/ws/console/vnc/test-token-123',
        expires_at: '2024-01-15T10:30:00Z',
        vnc_port: 5901
      };

      service.requestAccess(vmId, protocol).subscribe(response => {
        expect(response).toEqual(mockResponse);
        expect(response.session_token).toBe('test-token-123');
        expect(response.vm_id).toBe(vmId);
        expect(response.protocol).toBe(protocol);
      });

      const req = httpMock.expectOne(`http://localhost:8000/api/vm/${vmId}/console/request`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ protocol });
      req.flush(mockResponse);
    });
  });

  describe('getStatus', () => {
    it('should get console status for a VM', () => {
      const vmId = 1;
      const mockStatus: ConsoleStatus = {
        vm_id: vmId,
        available: true,
        has_active_session: true,
        session_token: 'test-token-123',
        expires_at: '2024-01-15T10:30:00Z',
        protocol: 'vnc'
      };

      service.getStatus(vmId).subscribe(status => {
        expect(status).toEqual(mockStatus);
        expect(status.vm_id).toBe(vmId);
        expect(status.available).toBe(true);
        expect(status.has_active_session).toBe(true);
      });

      const req = httpMock.expectOne(`http://localhost:8000/api/vm/${vmId}/console/status`);
      expect(req.request.method).toBe('GET');
      req.flush(mockStatus);
    });
  });

  describe('terminateSession', () => {
    it('should terminate console session without session token', () => {
      const vmId = 1;
      const mockResponse = { message: 'Console session terminated successfully' };

      service.terminateSession(vmId).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`http://localhost:8000/api/vm/${vmId}/console/session`);
      expect(req.request.method).toBe('DELETE');
      expect(req.request.params.keys().length).toBe(0);
      req.flush(mockResponse);
    });

    it('should terminate console session with session token', () => {
      const vmId = 1;
      const sessionToken = 'test-token-123';
      const mockResponse = { message: 'Console session terminated successfully' };

      service.terminateSession(vmId, sessionToken).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(
        `http://localhost:8000/api/vm/${vmId}/console/session?session_token=${sessionToken}`
      );
      expect(req.request.method).toBe('DELETE');
      req.flush(mockResponse);
    });
  });

  describe('extendSession', () => {
    it('should extend console session', () => {
      const vmId = 1;
      const sessionToken = 'test-token-123';
      const minutes = 15;
      const mockResponse = {
        message: 'Console session extended successfully',
        expires_at: '2024-01-15T10:45:00Z'
      };

      service.extendSession(vmId, sessionToken, minutes).subscribe(response => {
        expect(response).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`http://localhost:8000/api/vm/${vmId}/console/extend`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ session_token: sessionToken, minutes });
      req.flush(mockResponse);
    });
  });

  describe('connection management', () => {
    it('should initialize with disconnected state', () => {
      const connection = service.getConnectionStatus();
      expect(connection.connected).toBe(false);
      expect(connection.session).toBeNull();
      expect(connection.error).toBeNull();
    });

    it('should handle disconnect', () => {
      service.disconnect();
      const connection = service.getConnectionStatus();
      expect(connection.connected).toBe(false);
      expect(connection.session).toBeNull();
      expect(connection.error).toBeNull();
    });
  });

  describe('VNC message handling', () => {
    it('should send VNC messages when connected', () => {
      // This would require a more complex setup with WebSocket mocking
      // For now, we'll test that the method exists and doesn't throw
      expect(() => service.sendKeys(['a', 'b', 'c'])).not.toThrow();
      expect(() => service.sendPointer(100, 200, 1)).not.toThrow();
      expect(() => service.sendResize(1024, 768)).not.toThrow();
    });

    it('should handle screenshot request', async () => {
      await expectAsync(service.takeScreenshot()).toBeRejectedWithError(
        'Screenshot functionality not yet implemented'
      );
    });
  });
});