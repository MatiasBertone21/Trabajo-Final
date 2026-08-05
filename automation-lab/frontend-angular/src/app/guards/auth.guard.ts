import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { authService } from '../core/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  if (authService.isAuthenticated()) return true;
  router.navigate(['/login'], { queryParams: { redirect: state?.url } });
  return false;
};
