import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout';
import {
  Dashboard,
  Projects,
  Agents,
  Discovery,
  Gates,
  Integrations,
  Settings,
} from './pages';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/discovery" element={<Discovery />} />
          <Route path="/gates" element={<Gates />} />
          <Route path="/integrations" element={<Integrations />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
