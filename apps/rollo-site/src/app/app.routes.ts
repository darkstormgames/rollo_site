import { Routes } from '@angular/router';
import { Home } from './pages/home/home';
import { About } from './pages/about/about';
import { Portfolio } from './pages/portfolio/portfolio';
import { Contact } from './pages/contact/contact';
import { Login } from './pages/auth/login';
import { Register } from './pages/auth/register';
import { AuthGuard, GuestGuard } from './guards/auth.guard';
import { DashboardLayout } from './components/layout/dashboard-layout/dashboard-layout';
import { DashboardOverview } from './pages/dashboard-overview/dashboard-overview';
import { VmList } from './components/vm/vm-list/vm-list';

export const routes: Routes = [
  { path: '', component: Home },
  { path: 'about', component: About },
  { path: 'portfolio', component: Portfolio, canActivate: [AuthGuard] },
  { path: 'contact', component: Contact },
  { path: 'login', component: Login, canActivate: [GuestGuard] },
  { path: 'register', component: Register, canActivate: [GuestGuard] },
  {
    path: 'dashboard',
    component: DashboardLayout,
    canActivate: [AuthGuard],
    children: [
      { path: '', component: DashboardOverview },
      { path: 'vms', component: VmList },
      // TODO: Add more dashboard routes as components are created
      { path: 'servers', redirectTo: '' },
      { path: 'monitoring', redirectTo: '' },
      { path: 'users', redirectTo: '' },
      { path: 'settings', redirectTo: '' }
    ]
  },
  { path: '**', redirectTo: '' } // Wildcard route for 404 handling
];
