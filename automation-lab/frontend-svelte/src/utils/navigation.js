export function navigateTo(path) {
  if (typeof window === 'undefined') return;

  const nextPath = path || '/';
  const currentPath = `${window.location.pathname}${window.location.search}`;
  if (nextPath === currentPath) return;

  window.history.pushState({}, '', nextPath);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
