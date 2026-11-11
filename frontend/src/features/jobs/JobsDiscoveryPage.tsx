import React, { useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search,
  Bookmark,
  BookmarkCheck,
  MapPin,
  ArrowRight,
  X
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, Button, FitScoreBadge } from '../../components/common/UIComponents';

export const JobsDiscoveryPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { jobs, toggleSaveJob } = useApp();

  const initialQuery = searchParams.get('q') || '';
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [selectedWorkMode, setSelectedWorkMode] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [onlySaved, setOnlySaved] = useState(false);
  const [sortBy, setSortBy] = useState<'fit' | 'deadline' | 'recent'>('fit');

  // Filter & sort logic
  const filteredJobs = useMemo(() => {
    return jobs.filter(job => {
      // Query filter
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = job.title.toLowerCase().includes(q);
        const matchesCompany = job.company.toLowerCase().includes(q);
        const matchesSkills = job.requiredSkills.some(s => s.toLowerCase().includes(q));
        if (!matchesTitle && !matchesCompany && !matchesSkills) return false;
      }

      // Work mode
      if (selectedWorkMode !== 'all' && job.workMode !== selectedWorkMode) {
        return false;
      }

      // Type
      if (selectedType !== 'all' && job.type !== selectedType) {
        return false;
      }

      // Only saved
      if (onlySaved && !job.saved) {
        return false;
      }

      return true;
    }).sort((a, b) => {
      if (sortBy === 'fit') return b.fitScore - a.fitScore;
      if (sortBy === 'deadline') return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
      return new Date(b.postedDate).getTime() - new Date(a.postedDate).getTime();
    });
  }, [jobs, searchQuery, selectedWorkMode, selectedType, onlySaved, sortBy]);

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedWorkMode('all');
    setSelectedType('all');
    setOnlySaved(false);
    setSortBy('fit');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Find Opportunities</h2>
        <p className="text-xs text-charcoal-600 mt-0.5">
          Nexora analyzes verified profile skills against each opening to calculate genuine match explanations.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <Panel className="p-4 bg-white">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by role title, company, or required skill (e.g. React, Kafka)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-canvas-50 border border-charcoal-200 rounded-md py-2 pl-9 pr-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500 focus:bg-white transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-charcoal-600 hover:text-charcoal-700"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Controls: Work mode, Type, Sort */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <select
              value={selectedWorkMode}
              onChange={(e) => setSelectedWorkMode(e.target.value)}
              className="bg-white border border-charcoal-200 rounded py-2 px-2.5 text-charcoal-800 focus:outline-none focus:border-steel-500"
            >
              <option value="all">All Work Modes</option>
              <option value="Hybrid">Hybrid</option>
              <option value="Remote">Remote</option>
              <option value="On-site">On-site</option>
            </select>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-white border border-charcoal-200 rounded py-2 px-2.5 text-charcoal-800 focus:outline-none focus:border-steel-500"
            >
              <option value="all">All Types</option>
              <option value="Internship">Internship</option>
              <option value="Full-time">Full-time</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'fit' | 'deadline' | 'recent')}
              className="bg-white border border-charcoal-200 rounded py-2 px-2.5 text-charcoal-800 focus:outline-none focus:border-steel-500"
            >
              <option value="fit">Sort by Fit Score</option>
              <option value="deadline">Sort by Deadline</option>
              <option value="recent">Sort by Recently Posted</option>
            </select>

            <button
              onClick={() => setOnlySaved(!onlySaved)}
              className={`px-3 py-2 border rounded font-medium transition-colors flex items-center gap-1.5 ${
                onlySaved
                  ? 'bg-steel-50 text-steel-700 border-steel-300'
                  : 'bg-white text-charcoal-700 border-charcoal-200 hover:bg-canvas-100'
              }`}
            >
              <Bookmark className="w-3.5 h-3.5" />
              <span>Saved</span>
            </button>
          </div>
        </div>
      </Panel>

      {/* Results Count & Clear */}
      <div className="flex items-center justify-between text-xs text-charcoal-600 px-1">
        <span>Showing {filteredJobs.length} opportunities matching your criteria</span>
        {(searchQuery || selectedWorkMode !== 'all' || selectedType !== 'all' || onlySaved) && (
          <button
            onClick={clearFilters}
            className="text-steel-600 hover:underline font-medium"
          >
            Clear active filters
          </button>
        )}
      </div>

      {/* Job Cards List */}
      <div className="space-y-4">
        {filteredJobs.map((job) => (
          <Panel
            key={job.id}
            className="p-5 hover:border-steel-400 transition-all cursor-pointer bg-white"
            onClick={() => navigate(`/app/jobs/${job.id}`)}
          >
            <div className="flex flex-col md:flex-row items-start justify-between gap-4">
              {/* Left Details */}
              <div className="flex items-start gap-4">
                <div className={`w-11 h-11 rounded-lg flex items-center justify-center font-bold text-sm shrink-0 shadow-xs ${job.logoBg}`}>
                  {job.logoText}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-bold text-sm text-charcoal-900 hover:text-steel-600 transition-colors">
                      {job.title}
                    </h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-canvas-100 text-charcoal-700 border border-charcoal-200">
                      {job.type}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-charcoal-600">
                    <span className="font-medium text-charcoal-800">{job.company}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {job.location} ({job.workMode})
                    </span>
                    <span>•</span>
                    <span className="font-medium text-charcoal-800">{job.stipendSalary}</span>
                  </div>

                  {/* Match Explanation Banner */}
                  <div className="mt-3 p-2.5 rounded bg-canvas-50 border border-charcoal-200 text-xs">
                    <div className="flex items-start gap-2">
                      <span className="font-semibold text-charcoal-800 text-[11px] shrink-0">Why it matches:</span>
                      <p className="text-charcoal-700 text-[11px] leading-relaxed">
                        {job.matchExplanation}
                      </p>
                    </div>
                  </div>

                  {/* Matching vs Missing Skills */}
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] text-charcoal-600">Matching:</span>
                      {job.matchingSkills.slice(0, 4).map(s => (
                        <span key={s} className="px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded text-[10px] font-medium">
                          ✓ {s}
                        </span>
                      ))}
                    </div>

                    {job.missingSkills.length > 0 && (
                      <div className="flex items-center gap-1.5 ml-2">
                        <span className="text-[11px] text-charcoal-600">Missing:</span>
                        {job.missingSkills.slice(0, 2).map(s => (
                          <span key={s} className="px-2 py-0.5 bg-amber-50 text-amber-800 border border-amber-200 rounded text-[10px] font-medium">
                            • {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right: Fit Score & Actions */}
              <div className="flex md:flex-col items-center md:items-end justify-between w-full md:w-auto shrink-0 gap-3">
                <FitScoreBadge score={job.fitScore} category={job.matchCategory} />

                <div className="flex items-center gap-2 mt-auto">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSaveJob(job.id);
                    }}
                    className={`p-2 rounded border transition-colors ${
                      job.saved
                        ? 'bg-steel-50 text-steel-700 border-steel-300'
                        : 'bg-white text-charcoal-600 border-charcoal-200 hover:bg-canvas-100'
                    }`}
                    title={job.saved ? "Saved" : "Save job"}
                  >
                    {job.saved ? <BookmarkCheck className="w-4 h-4 text-steel-600" /> : <Bookmark className="w-4 h-4" />}
                  </button>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/app/jobs/${job.id}`);
                    }}
                    icon={<ArrowRight className="w-3.5 h-3.5" />}
                  >
                    View Details
                  </Button>
                </div>
              </div>
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
};
