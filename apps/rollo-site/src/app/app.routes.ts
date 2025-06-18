import { Routes } from '@angular/router';
import { Home } from './pages/home/home';
import { About } from './pages/about/about';
import { Portfolio } from './pages/portfolio/portfolio';
import { Contact } from './pages/contact/contact';
import { Login } from './pages/auth/login';
import { Register } from './pages/auth/register';
import { AuthGuard, GuestGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', component: Home },
  { path: 'about', component: About },
  { path: 'portfolio', component: Portfolio, canActivate: [AuthGuard] },
  { path: 'contact', component: Contact },
  { path: 'login', component: Login, canActivate: [GuestGuard] },
  { path: 'register', component: Register, canActivate: [GuestGuard] },
  { path: '**', redirectTo: '' } // Wildcard route for 404 handling
];
