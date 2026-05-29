import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { InteractiveShowcase } from './InteractiveShowcase';

const root = document.getElementById('showcase-root');
if (root) {
  createRoot(root).render(
    <StrictMode>
      <InteractiveShowcase />
    </StrictMode>,
  );
}
