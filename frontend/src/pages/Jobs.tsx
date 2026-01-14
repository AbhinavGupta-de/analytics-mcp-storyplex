import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Play, RefreshCw, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';
import { api, CreateJobRequest, Job } from '../lib/api';

function JobStatusBadge({ status }: { status: Job['status'] }) {
  const config = {
    pending: { icon: Clock, color: 'text-yellow-400 bg-yellow-400/20' },
    running: { icon: Loader2, color: 'text-blue-400 bg-blue-400/20', animate: true },
    completed: { icon: CheckCircle, color: 'text-green-400 bg-green-400/20' },
    failed: { icon: XCircle, color: 'text-red-400 bg-red-400/20' },
    cancelled: { icon: XCircle, color: 'text-gray-400 bg-gray-400/20' },
  }[status];

  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm ${config.color}`}>
      <Icon className={`w-4 h-4 ${config.animate ? 'animate-spin' : ''}`} />
      {status}
    </span>
  );
}

export default function Jobs() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<CreateJobRequest>({
    platform: 'ao3',
    job_type: 'scrape_works',
    limit: 50,
    sort_by: 'kudos',
  });

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: api.getJobs,
    refetchInterval: 3000, // Poll every 3 seconds
  });

  const { data: platforms } = useQuery({
    queryKey: ['platforms'],
    queryFn: api.getAvailablePlatforms,
  });

  const createJob = useMutation({
    mutationFn: api.createJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setShowForm(false);
      setFormData({
        platform: 'ao3',
        job_type: 'scrape_works',
        limit: 50,
        sort_by: 'kudos',
      });
    },
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Scrape Jobs</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
        >
          <Play className="w-5 h-5" />
          New Job
        </button>
      </div>

      {/* New Job Form */}
      {showForm && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 mb-8">
          <h2 className="text-xl font-semibold mb-4">Create New Scrape Job</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Platform</label>
              <select
                value={formData.platform}
                onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg"
              >
                {platforms?.filter((p) => !p.status).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Job Type</label>
              <select
                value={formData.job_type}
                onChange={(e) =>
                  setFormData({ ...formData, job_type: e.target.value as CreateJobRequest['job_type'] })
                }
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg"
              >
                <option value="scrape_works">Scrape Works</option>
                <option value="scrape_fandoms">Scrape Fandoms</option>
                <option value="scrape_single_work">Scrape Single Work</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Limit</label>
              <input
                type="number"
                value={formData.limit}
                onChange={(e) => setFormData({ ...formData, limit: parseInt(e.target.value) })}
                min={1}
                max={500}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg"
              />
            </div>

            {formData.job_type === 'scrape_works' && (
              <>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Fandom (optional)</label>
                  <input
                    type="text"
                    value={formData.fandom || ''}
                    onChange={(e) => setFormData({ ...formData, fandom: e.target.value })}
                    placeholder="e.g. Harry Potter"
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">Sort By</label>
                  <select
                    value={formData.sort_by}
                    onChange={(e) => setFormData({ ...formData, sort_by: e.target.value })}
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                  >
                    <option value="kudos">Kudos</option>
                    <option value="hits">Hits</option>
                    <option value="bookmarks">Bookmarks</option>
                    <option value="date">Date</option>
                  </select>
                </div>
              </>
            )}

            {formData.job_type === 'scrape_single_work' && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">Work ID</label>
                <input
                  type="text"
                  value={formData.work_id || ''}
                  onChange={(e) => setFormData({ ...formData, work_id: e.target.value })}
                  placeholder="e.g. 12345678"
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg"
                />
              </div>
            )}
          </div>

          <div className="flex gap-4 mt-6">
            <button
              onClick={() => createJob.mutate(formData)}
              disabled={createJob.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors disabled:opacity-50"
            >
              {createJob.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Play className="w-5 h-5" />
              )}
              Start Job
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Jobs List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-purple-500"></div>
        </div>
      ) : jobs && jobs.length > 0 ? (
        <div className="space-y-4">
          {jobs.map((job) => (
            <div
              key={job.id}
              className="bg-gray-800 rounded-xl p-4 border border-gray-700"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-4">
                  <JobStatusBadge status={job.status} />
                  <span className="text-sm text-gray-400">{job.job_type}</span>
                  <span className="text-sm text-gray-400">{job.platform.toUpperCase()}</span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(job.created_at).toLocaleString()}
                </span>
              </div>

              {job.status === 'running' && (
                <div className="mb-3">
                  <div className="flex justify-between text-sm text-gray-400 mb-1">
                    <span>Progress</span>
                    <span>{job.progress} / {job.total}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-600 transition-all"
                      style={{ width: `${(job.progress / job.total) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {job.error && (
                <p className="text-red-400 text-sm">Error: {job.error}</p>
              )}

              {job.result && (
                <p className="text-green-400 text-sm">
                  Result: {JSON.stringify(job.result)}
                </p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
          <p className="text-gray-400 mb-4">No jobs yet. Create a new scrape job to get started!</p>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            <Play className="w-5 h-5" />
            Create First Job
          </button>
        </div>
      )}
    </div>
  );
}
