/** Web demo: show 11-scene switcher while keeping record=1 layout. */
export function isVideoBrowseMode(): boolean {
  if (typeof window === 'undefined') return false;
  const q = new URLSearchParams(window.location.search);
  return q.get('browse') === '1' || q.get('nav') === '1';
}
