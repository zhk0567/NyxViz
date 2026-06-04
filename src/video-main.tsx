import { createRoot } from 'react-dom/client';
import { VideoApp } from '@/dashboard/VideoApp';
import '@/dashboard/video-dashboard.css';

createRoot(document.getElementById('root')!).render(<VideoApp />);
