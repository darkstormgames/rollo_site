import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ConsoleSession {
  session_token: string;
  vm_id: number;
  protocol: string;
  websocket_url: string;
  expires_at: string;
  vnc_port?: number;
  spice_port?: number;
}

export interface ConsoleStatus {
  vm_id: number;
  available: boolean;
  has_active_session: boolean;
  session_token?: string;
  expires_at?: string;
  protocol?: string;
}

export interface ConsoleConnection {
  connected: boolean;
  session: ConsoleSession | null;
  error: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class ConsoleService {
  private baseUrl = environment.apiUrl || 'http://localhost:8000';
  private connectionSubject = new BehaviorSubject<ConsoleConnection>({
    connected: false,
    session: null,
    error: null
  });

  public connection$ = this.connectionSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Request console access for a VM
   */
  requestAccess(vmId: number, protocol: string = 'vnc'): Observable<ConsoleSession> {
    const url = `${this.baseUrl}/api/vm/${vmId}/console/request`;
    const body = { protocol };
    
    return this.http.post<ConsoleSession>(url, body);
  }

  /**
   * Check console status for a VM
   */
  getStatus(vmId: number): Observable<ConsoleStatus> {
    const url = `${this.baseUrl}/api/vm/${vmId}/console/status`;
    return this.http.get<ConsoleStatus>(url);
  }

  /**
   * Terminate console session
   */
  terminateSession(vmId: number, sessionToken?: string): Observable<any> {
    const url = `${this.baseUrl}/api/vm/${vmId}/console/session`;
    const params = sessionToken ? { session_token: sessionToken } : {};
    
    return this.http.delete(url, { params });
  }

  /**
   * Extend console session
   */
  extendSession(vmId: number, sessionToken: string, minutes: number = 15): Observable<any> {
    const url = `${this.baseUrl}/api/vm/${vmId}/console/extend`;
    const body = { session_token: sessionToken, minutes };
    
    return this.http.post(url, body);
  }

  /**
   * Connect to VNC console using WebSocket
   */
  connect(session: ConsoleSession): Observable<ConsoleConnection> {
    return new Observable(observer => {
      try {
        // Update connection status
        this.connectionSubject.next({
          connected: false,
          session,
          error: null
        });

        // Create WebSocket URL for VNC
        const wsUrl = session.websocket_url.replace('ws/console/', 'ws/console/vnc/');
        const websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
          console.log('VNC WebSocket connected');
          const connection = {
            connected: true,
            session,
            error: null
          };
          this.connectionSubject.next(connection);
          observer.next(connection);
        };

        websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('VNC message received:', data);
            
            // Handle different VNC message types
            this.handleVncMessage(data);
          } catch (error) {
            console.error('Failed to parse VNC message:', error);
          }
        };

        websocket.onerror = (error) => {
          console.error('VNC WebSocket error:', error);
          const connection = {
            connected: false,
            session,
            error: 'WebSocket connection failed'
          };
          this.connectionSubject.next(connection);
          observer.next(connection);
        };

        websocket.onclose = (event) => {
          console.log('VNC WebSocket closed:', event);
          const connection = {
            connected: false,
            session: null,
            error: event.reason || 'Connection closed'
          };
          this.connectionSubject.next(connection);
          observer.next(connection);
        };

        // Store websocket reference for cleanup
        (session as any).websocket = websocket;

      } catch (error) {
        const connection = {
          connected: false,
          session,
          error: `Connection failed: ${error}`
        };
        this.connectionSubject.next(connection);
        observer.next(connection);
      }
    });
  }

  /**
   * Disconnect from console
   */
  disconnect(): void {
    const currentConnection = this.connectionSubject.value;
    if (currentConnection.session && (currentConnection.session as any).websocket) {
      try {
        (currentConnection.session as any).websocket.close();
      } catch (error) {
        console.error('Error closing WebSocket:', error);
      }
    }

    this.connectionSubject.next({
      connected: false,
      session: null,
      error: null
    });
  }

  /**
   * Send VNC message
   */
  sendMessage(message: any): void {
    const currentConnection = this.connectionSubject.value;
    if (currentConnection.connected && currentConnection.session && (currentConnection.session as any).websocket) {
      try {
        const websocket = (currentConnection.session as any).websocket;
        websocket.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send VNC message:', error);
      }
    }
  }

  /**
   * Send key event to VNC
   */
  sendKeys(keys: string[]): void {
    keys.forEach(key => {
      this.sendMessage({
        type: 'vnc_key',
        data: {
          key: key.charCodeAt(0),
          down: true
        }
      });
      
      // Send key up event
      setTimeout(() => {
        this.sendMessage({
          type: 'vnc_key',
          data: {
            key: key.charCodeAt(0),
            down: false
          }
        });
      }, 50);
    });
  }

  /**
   * Send mouse event to VNC
   */
  sendPointer(x: number, y: number, buttonMask: number = 0): void {
    this.sendMessage({
      type: 'vnc_pointer',
      data: {
        x,
        y,
        buttonMask
      }
    });
  }

  /**
   * Send resize event to VNC
   */
  sendResize(width: number, height: number): void {
    this.sendMessage({
      type: 'vnc_resize',
      data: {
        width,
        height
      }
    });
  }

  /**
   * Take screenshot (future implementation)
   */
  async takeScreenshot(): Promise<Blob> {
    // This would be implemented to capture the VNC display
    throw new Error('Screenshot functionality not yet implemented');
  }

  /**
   * Handle incoming VNC messages
   */
  private handleVncMessage(data: any): void {
    switch (data.type) {
      case 'console_connected':
        console.log('Console connected:', data.data);
        break;
      case 'vnc_init':
        console.log('VNC initialized:', data.data);
        // Handle VNC initialization
        break;
      case 'vnc_frame':
        console.log('VNC frame received:', data.data);
        // Handle frame updates
        break;
      case 'vnc_resize_response':
        console.log('VNC resize response:', data.data);
        break;
      default:
        console.log('Unknown VNC message type:', data.type);
    }
  }

  /**
   * Get current connection status
   */
  getConnectionStatus(): ConsoleConnection {
    return this.connectionSubject.value;
  }
}