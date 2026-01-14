import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ExternalLink, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { api } from '../lib/api';

export default function Works() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('views');

  const { data, isLoading } = useQuery({
    queryKey: ['works', page, search, sortBy],
    queryFn: () =>
      api.getWorks({
        page,
        pageSize: 20,
        sortBy,
        sortOrder: 'desc',
        search: search || undefined,
      }),
  });

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Works</h1>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search works..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="views">Sort by Views</option>
          <option value="likes">Sort by Likes</option>
          <option value="words">Sort by Words</option>
          <option value="updated">Sort by Updated</option>
        </select>
      </div>

      {/* Works Table */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-purple-500"></div>
        </div>
      ) : data && data.works.length > 0 ? (
        <>
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Title</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Author</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Fandoms</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Words</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Views</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">Likes</th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-400">Link</th>
                </tr>
              </thead>
              <tbody>
                {data.works.map((work) => (
                  <tr key={work.id} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="px-4 py-3">
                      <span className="font-medium">{work.title.slice(0, 50)}</span>
                      {work.title.length > 50 && '...'}
                    </td>
                    <td className="px-4 py-3 text-gray-400">{work.author_name || 'Unknown'}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {work.fandoms.slice(0, 2).map((f) => (
                          <span
                            key={f}
                            className="px-2 py-0.5 text-xs bg-purple-600/30 rounded"
                          >
                            {f.slice(0, 20)}
                          </span>
                        ))}
                        {work.fandoms.length > 2 && (
                          <span className="text-xs text-gray-500">
                            +{work.fandoms.length - 2}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">{work.word_count.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">{work.views.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">{work.likes.toLocaleString()}</td>
                    <td className="px-4 py-3 text-center">
                      <a
                        href={work.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-purple-400 hover:text-purple-300"
                      >
                        <ExternalLink className="w-4 h-4 inline" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4">
            <p className="text-sm text-gray-400">
              Showing {(page - 1) * data.page_size + 1} - {Math.min(page * data.page_size, data.total)} of {data.total}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 bg-gray-800 border border-gray-700 rounded-lg disabled:opacity-50 hover:bg-gray-700"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page >= data.total_pages}
                className="p-2 bg-gray-800 border border-gray-700 rounded-lg disabled:opacity-50 hover:bg-gray-700"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
          <p className="text-gray-400">No works found. Run a scrape job to get started!</p>
        </div>
      )}
    </div>
  );
}
