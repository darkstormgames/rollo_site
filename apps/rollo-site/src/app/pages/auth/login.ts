import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { LoginCredentials, ApiError } from '../../models/auth.models';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrls: ['./login.scss']
})
export class Login {
  credentials: LoginCredentials = {
    username: '',
    password: ''
  };

  isLoading = false;
  error: string | null = null;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  onSubmit(): void {
    if (this.isLoading || !this.credentials.username || !this.credentials.password) {
      return;
    }

    this.isLoading = true;
    this.error = null;

    this.authService.login(this.credentials).subscribe({
      next: (response) => {
        console.log('Login successful:', response.message);
        this.router.navigate(['/']);
      },
      error: (apiError: ApiError) => {
        this.error = apiError.error || 'Login failed';
        this.isLoading = false;
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }
}