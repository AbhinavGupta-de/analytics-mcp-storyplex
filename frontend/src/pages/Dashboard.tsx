import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { BookOpen, Users, Folder, Tag, Eye, Heart } from 'lucide-react';
import { api } from '../lib/api';

const COLORS = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold mt-1">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['summary'],
    queryFn: api.getSummary,
  });

  const { data: topFandoms } = useQuery({
    queryKey: ['topFandoms'],
    queryFn: () => api.getTopFandoms(10, 'works'),
  });

  const { data: wordDistribution } = useQuery({
    queryKey: ['wordDistribution'],
    queryFn: api.getWordCountDistribution,
  });

  const { data: topTags } = useQuery({
    queryKey: ['topTags'],
    queryFn: () => api.getTopTags(10),
  });

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        <StatCard
          title="Total Works"
          value={summary?.total_works || 0}
          icon={BookOpen}
          color="bg-purple-600"
        />
        <StatCard
          title="Total Authors"
          value={summary?.total_authors || 0}
          icon={Users}
          color="bg-cyan-600"
        />
        <StatCard
          title="Fandoms"
          value={summary?.total_fandoms || 0}
          icon={Folder}
          color="bg-emerald-600"
        />
        <StatCard
          title="Tags"
          value={summary?.total_tags || 0}
          icon={Tag}
          color="bg-amber-600"
        />
        <StatCard
          title="Total Views"
          value={summary?.total_views || 0}
          icon={Eye}
          color="bg-rose-600"
        />
        <StatCard
          title="Total Likes"
          value={summary?.total_likes || 0}
          icon={Heart}
          color="bg-pink-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Top Fandoms Chart */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Top Fandoms</h2>
          {topFandoms && topFandoms.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topFandoms} layout="vertical">
                <XAxis type="number" stroke="#9ca3af" />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={150}
                  stroke="#9ca3af"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) =>
                    value.length > 20 ? value.slice(0, 20) + '...' : value
                  }
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="work_count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-12">No data yet. Run a scrape job!</p>
          )}
        </div>

        {/* Word Count Distribution */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Word Count Distribution</h2>
          {wordDistribution && wordDistribution.some((d) => d.count > 0) ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={wordDistribution.filter((d) => d.count > 0)}
                  dataKey="count"
                  nameKey="range"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ range, percent }) =>
                    `${range} (${(percent * 100).toFixed(0)}%)`
                  }
                >
                  {wordDistribution.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-center py-12">No data yet. Run a scrape job!</p>
          )}
        </div>
      </div>

      {/* Top Tags */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Top Tags</h2>
        {topTags && topTags.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {topTags.map((tag, index) => (
              <span
                key={tag.name}
                className="px-3 py-1 rounded-full text-sm"
                style={{ backgroundColor: COLORS[index % COLORS.length] + '33' }}
              >
                {tag.name} ({tag.work_count})
              </span>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-8">No tags yet. Run a scrape job!</p>
        )}
      </div>
    </div>
  );
}
