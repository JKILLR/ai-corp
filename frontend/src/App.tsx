import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout';
import { ThemeToggle } from './components/ui';
import { ThemeProvider } from './hooks/useTheme';
import {
  Dashboard,
  Projects,
  Agents,
  Gates,
  Integrations,
  Settings,
} from './pages';
import { COOChannel } from './pages/COOChannel';

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/coo" element={<COOChannel />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/gates" element={<Gates />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Routes>
        <ThemeToggle />
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
