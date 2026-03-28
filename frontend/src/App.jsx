import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SlateView from './pages/SlateView';
import EventResearch from './pages/EventResearch';
import EdgeDashboard from './pages/EdgeDashboard';
import TrackingDashboard from './pages/TrackingDashboard';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

function NavItem({ to, children, end }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `text-sm font-medium transition-colors hover:text-foreground ${isActive ? 'text-foreground' : 'text-muted-foreground'}`
      }
    >
      {children}
    </NavLink>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <nav className="flex items-center gap-6 px-6 py-4 border-b border-border">
          <span className="text-sm font-bold tracking-tight text-primary mr-2">fin-arb</span>
          <NavItem to="/" end>Slates</NavItem>
          <NavItem to="/edge">Edge</NavItem>
          <NavItem to="/tracking">Tracking</NavItem>
        </nav>
        <main className="max-w-6xl mx-auto px-6 py-6">
          <Routes>
            <Route path="/" element={<SlateView />} />
            <Route path="/events/:id" element={<EventResearch />} />
            <Route path="/edge" element={<EdgeDashboard />} />
            <Route path="/tracking" element={<TrackingDashboard />} />
          </Routes>
        </main>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
