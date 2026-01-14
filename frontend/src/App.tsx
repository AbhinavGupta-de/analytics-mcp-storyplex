import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { BookOpen, BarChart3, Folder, Play, Settings } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Works from './pages/Works';
import Fandoms from './pages/Fandoms';
import Jobs from './pages/Jobs';
import clsx from 'clsx';

const navItems = [
  { path: '/', label: 'Dashboard', icon: BarChart3 },
  { path: '/works', label: 'Works', icon: BookOpen },
  { path: '/fandoms', label: 'Fandoms', icon: Folder },
  { path: '/jobs', label: 'Scrape Jobs', icon: Play },
];

function App() {
  const location = useLocation();

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <h1 className="text-xl font-bold text-purple-400 flex items-center gap-2">
            <BookOpen className="w-6 h-6" />
            Storyplex
          </h1>
          <p className="text-sm text-gray-400 mt-1">Analytics Dashboard</p>
        </div>

        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={clsx(
                      'flex items-center gap-3 px-4 py-2 rounded-lg transition-colors',
                      isActive
                        ? 'bg-purple-600 text-white'
                        : 'text-gray-300 hover:bg-gray-700'
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="p-4 border-t border-gray-700">
          <p className="text-xs text-gray-500">v0.1.0</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/works" element={<Works />} />
          <Route path="/fandoms" element={<Fandoms />} />
          <Route path="/jobs" element={<Jobs />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
