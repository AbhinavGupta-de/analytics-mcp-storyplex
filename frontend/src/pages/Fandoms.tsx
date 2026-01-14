import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { api } from '../lib/api';

export default function Fandoms() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['fandoms', page, search],
    queryFn: () => api.getFandoms({ page, pageSize: 50, search: search || undefined }),
  });

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Fandoms</h1>

      {/* Search */}
      <div className="relative max-w-md mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search fandoms..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-purple-500"></div>
        </div>
      ) : data && data.fandoms.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.fandoms.map((fandom) => (
            <div
              key={fandom.id}
              className="bg-gray-800 rounded-xl p-4 border border-gray-700 hover:border-purple-500 transition-colors"
            >
              <h3 className="font-semibold mb-2">{fandom.name}</h3>
              {fandom.category && (
                <span className="inline-block px-2 py-0.5 text-xs bg-purple-600/30 rounded mb-3">
                  {fandom.category}
                </span>
              )}
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>
                  <p className="text-gray-400">Works</p>
                  <p className="font-medium">{fandom.work_count.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-400">Views</p>
                  <p className="font-medium">{fandom.total_views.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-400">Likes</p>
                  <p className="font-medium">{fandom.total_likes.toLocaleString()}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
          <p className="text-gray-400">No fandoms found. Run a fandom scrape job!</p>
        </div>
      )}
    </div>
  );
}
