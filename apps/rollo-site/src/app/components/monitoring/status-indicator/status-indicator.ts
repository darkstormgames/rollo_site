import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export type StatusType = 'running' | 'stopped' | 'paused' | 'error' | 'transitioning' | 'online' | 'offline' | 'maintenance';

@Component({
  selector: 'app-status-indicator',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './status-indicator.html',
  styleUrls: ['./status-indicator.scss']
})
export class StatusIndicator {
  @Input() status!: string;
  @Input() type: StatusType = 'stopped';
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() showDot: boolean = true;
  @Input() showText: boolean = true;

  getStatusType(): StatusType {
    // Auto-detect status type based on status string
    const statusLower = this.status?.toLowerCase();
    
    if (statusLower === 'running') return 'running';
    if (statusLower === 'stopped') return 'stopped';
    if (statusLower === 'paused') return 'paused';
    if (statusLower === 'error') return 'error';
    if (statusLower === 'starting' || statusLower === 'stopping') return 'transitioning';
    if (statusLower === 'online') return 'online';
    if (statusLower === 'offline') return 'offline';
    if (statusLower === 'maintenance') return 'maintenance';
    
    return this.type;
  }
}