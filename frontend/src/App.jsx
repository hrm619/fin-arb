import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SlateView from './pages/SlateView';
import EventResearch from './pages/EventResearch';
import EdgeDashboard from './pages/EdgeDashboard';
import TrackingDashboard from './pages/TrackingDashboard';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

const navStyle = ({ isActive }) => ({
  color: isActive ? '#3b82f6' : '#aaa',
  textDecoration: 'none',
  fontWeight: isActive ? 'bold' : 'normal',
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <nav style={{ display: 'flex', gap: '1.5rem', padding: '1rem', borderBottom: '1px solid #333', marginBottom: '1rem' }}>
          <NavLink to="/" style={navStyle} end>Slates</NavLink>
          <NavLink to="/edge" style={navStyle}>Edge</NavLink>
          <NavLink to="/tracking" style={navStyle}>Tracking</NavLink>
        </nav>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
          <Routes>
            <Route path="/" element={<SlateView />} />
            <Route path="/events/:id" element={<EventResearch />} />
            <Route path="/edge" element={<EdgeDashboard />} />
            <Route path="/tracking" element={<TrackingDashboard />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
