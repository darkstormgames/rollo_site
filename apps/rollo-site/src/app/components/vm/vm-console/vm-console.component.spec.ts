import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { VmConsoleComponent } from './vm-console.component';
import { LoadingSpinnerComponent } from '../../shared/loading-spinner/loading-spinner.component';
import { VM } from '../../../models/vm/vm.model';

describe('VmConsoleComponent', () => {
  let component: VmConsoleComponent;
  let fixture: ComponentFixture<VmConsoleComponent>;

  const mockVM: VM = {
    id: 1,
    name: 'test-vm',
    uuid: 'test-uuid',
    status: 'running' as any,
    os_type: 'linux' as any,
    os_version: 'Ubuntu 20.04',
    vnc_port: 5900,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    server: {
      id: 1,
      hostname: 'test-server',
      ip_address: '192.168.1.1',
      status: 'running'
    },
    resources: {
      cpu_cores: 2,
      memory_mb: 4096,
      disk_gb: 50
    },
    network: {
      interface: 'eth0',
      ip_address: '192.168.1.100',
      mac_address: '00:1B:44:11:3A:B7',
      network_type: 'bridge'
    }
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VmConsoleComponent, FormsModule, LoadingSpinnerComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(VmConsoleComponent);
    component = fixture.componentInstance;
    component.vm = mockVM;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with disconnected state', () => {
    expect(component.isConnected).toBeFalse();
    expect(component.isConnecting).toBeFalse();
    expect(component.error).toBeNull();
  });

  it('should start connecting when VM is provided', () => {
    spyOn(component, 'connect');
    component.ngOnInit();
    expect(component.connect).toHaveBeenCalled();
  });

  it('should display VM name in header', () => {
    fixture.detectChanges();
    const headerElement = fixture.nativeElement.querySelector('.console-header h3');
    expect(headerElement.textContent).toContain('test-vm');
  });

  it('should show loading state when connecting', () => {
    component.isConnecting = true;
    fixture.detectChanges();
    
    const loadingElement = fixture.nativeElement.querySelector('.console-loading');
    expect(loadingElement).toBeTruthy();
    expect(loadingElement.textContent).toContain('Connecting to console...');
  });

  it('should show error state when error occurs', () => {
    component.error = 'Connection failed';
    fixture.detectChanges();
    
    const errorElement = fixture.nativeElement.querySelector('.console-error');
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('Connection failed');
  });

  it('should handle command input', () => {
    component.isConnected = true;
    component.currentCommand = 'ls';
    spyOn(component, 'sendCommand');
    
    fixture.detectChanges();
    
    const inputElement = fixture.nativeElement.querySelector('.console-command-input');
    const event = new KeyboardEvent('keydown', { key: 'Enter' });
    inputElement.dispatchEvent(event);
    
    expect(component.sendCommand).toHaveBeenCalled();
  });

  it('should navigate command history with arrow keys', () => {
    component.isConnected = true;
    component['commandHistory'] = ['command1', 'command2'];
    
    const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
    component.onKeyDown(event);
    
    expect(component.currentCommand).toBe('command1');
  });

  it('should toggle fullscreen mode', () => {
    expect(component.isFullscreen).toBeFalse();
    
    component.toggleFullscreen();
    expect(component.isFullscreen).toBeTrue();
    
    component.toggleFullscreen();
    expect(component.isFullscreen).toBeFalse();
  });

  it('should disconnect on destroy', () => {
    spyOn(component, 'disconnect');
    component.ngOnDestroy();
    expect(component.disconnect).toHaveBeenCalled();
  });

  it('should add console lines correctly', () => {
    const initialCount = component.consoleLines.length;
    (component as any).addConsoleLine('test line');
    expect(component.consoleLines.length).toBe(initialCount + 1);
    expect(component.consoleLines[component.consoleLines.length - 1]).toBe('test line');
  });

  it('should limit console history', () => {
    // Fill console with many lines
    for (let i = 0; i < 1100; i++) {
      (component as any).addConsoleLine(`line ${i}`);
    }
    
    expect(component.consoleLines.length).toBeLessThanOrEqual(800);
  });

  it('should get correct status text', () => {
    component.isConnecting = true;
    expect(component.getStatusText()).toBe('Connecting...');
    
    component.isConnecting = false;
    component.isConnected = true;
    expect(component.getStatusText()).toBe('Connected');
    
    component.isConnected = false;
    component.error = 'Error message';
    expect(component.getStatusText()).toBe('Error');
    
    component.error = null;
    expect(component.getStatusText()).toBe('Disconnected');
  });

  it('should simulate command responses correctly', () => {
    spyOn(component as any, 'addConsoleLine');
    
    (component as any).simulateCommandResponse('ls');
    
    setTimeout(() => {
      expect((component as any).addConsoleLine).toHaveBeenCalledWith(jasmine.stringMatching(/bin.*boot.*dev/));
    }, 600);
  });

  it('should handle reconnection attempts', () => {
    (component as any).reconnectAttempts = 0;
    (component as any).maxReconnectAttempts = 3;
    
    spyOn(component, 'disconnect');
    spyOn(component, 'connect');
    
    component.reconnect();
    
    expect((component as any).reconnectAttempts).toBe(1);
    expect(component.disconnect).toHaveBeenCalled();
  });

  it('should set error when max reconnection attempts exceeded', () => {
    (component as any).reconnectAttempts = 3;
    (component as any).maxReconnectAttempts = 3;
    
    component.reconnect();
    
    expect(component.error).toBe('Maximum reconnection attempts exceeded. Please try again later.');
  });

  it('should focus input after view init', (done) => {
    const inputElement = fixture.nativeElement.querySelector('.console-command-input');
    spyOn(inputElement, 'focus');
    
    component.ngAfterViewInit();
    
    setTimeout(() => {
      expect(inputElement.focus).toHaveBeenCalled();
      done();
    }, 150);
  });
});