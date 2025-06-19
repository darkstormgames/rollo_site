import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div 
      class="loading-spinner"
      [class]="'spinner-' + size"
      [class.inline]="display === 'inline'"
      [attr.aria-label]="ariaLabel"
      [attr.aria-hidden]="ariaHidden"
      role="status">
      
      <div class="spinner-circle"></div>
      
      <span *ngIf="showText" class="spinner-text">
        {{ text }}
      </span>
    </div>
  `,
  styleUrls: ['./loading-spinner.component.css']
})
export class LoadingSpinnerComponent {
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() display: 'block' | 'inline' = 'block';
  @Input() text?: string;
  @Input() showText = false;
  @Input() ariaLabel = 'Loading';
  @Input() ariaHidden = false;
}