import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { RegisterData, ApiError } from '../../models/auth.models';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrls: ['./register.scss']
})
export class Register {
  userData: RegisterData = {
    username: '',
    email: '',
    password: '',
    firstName: '',
    lastName: ''
  };

  confirmPassword = '';
  isLoading = false;
  error: string | null = null;
  success: string | null = null;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  onSubmit(): void {
    if (this.isLoading || !this.isValidForm()) {
      return;
    }

    if (this.userData.password !== this.confirmPassword) {
      this.error = 'Passwords do not match';
      return;
    }

    this.isLoading = true;
    this.error = null;
    this.success = null;

    const registerData = { ...this.userData };
    if (!registerData.firstName) delete registerData.firstName;
    if (!registerData.lastName) delete registerData.lastName;

    this.authService.register(registerData).subscribe({
      next: (response) => {
        this.success = response.message;
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 2000);
      },
      error: (apiError: ApiError) => {
        this.error = apiError.error || 'Registration failed';
        if (apiError.details && Array.isArray(apiError.details)) {
          this.error = apiError.details.map((detail: any) => detail.msg).join(', ');
        }
        this.isLoading = false;
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }

  private isValidForm(): boolean {
    return !!(
      this.userData.username &&
      this.userData.email &&
      this.userData.password &&
      this.confirmPassword
    );
  }
}