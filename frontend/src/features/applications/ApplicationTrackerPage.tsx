import React, { useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Search,
  Plus,
  ArrowRight,
  Kanban,
  List
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, Button, StageBadge } from '../../components/common/UIComponents';
import type { ApplicationStage } from '../../types';

export const ApplicationTrackerPage: React.FC = () => {
  const navigate = useNavigate();
  const { applications } = useApp();

  const [viewMode, setViewMode] = useState<'table' | 'kanban'>('table');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStage, setSelectedStage] = useState<string>('all');

  const allStages: ApplicationStage[] = [
    'Interested',
    'Preparing',
    'Awaiting approval',
    'Ready to apply',
    'Applied',
    'Assessment',
    'Interview',
    'Offer',
    'Rejected',
    'Withdrawn'
  ];

  // Filtering
  const filteredApps = useMemo(() => {
    return applications.filter(app => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        if (!app.company.toLowerCase().includes(q) && !app.jobTitle.toLowerCase().includes(q)) {
          return false;
        }
      }
      if (selectedStage !== 'all' && app.stage !== selectedStage) {
        return false;
      }
      return true;
    });
  }, [applications, searchQuery, selectedStage]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Application Tracker</h2>
          <p className="text-xs text-charcoal-600 mt-1">
            Maintain complete end-to-end continuity across every company deadline, technical assessment, and interview round.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* View mode toggle */}
          <div className="flex items-center bg-canvas-100 border border-charcoal-200 rounded p-1">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded transition-colors ${
                viewMode === 'table' ? 'bg-white shadow-xs text-charcoal-900 font-semibold' : 'text-charcoal-600 hover:text-charcoal-900'
              }`}
              title="Table View"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('kanban')}
              className={`p-1.5 rounded transition-colors ${
                viewMode === 'kanban' ? 'bg-white shadow-xs text-charcoal-900 font-semibold' : 'text-charcoal-600 hover:text-charcoal-900'
              }`}
              title="Kanban Board View"
            >
              <Kanban className="w-4 h-4" />
            </button>
          </div>

          <Link to="/app/jobs">
            <Button variant="primary" size="sm" icon={<Plus className="w-3.5 h-3.5" />}>
              Add Application
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Panel className="p-3 bg-white">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 text-xs">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by company or role..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-canvas-50 border border-charcoal-200 rounded py-1.5 pl-8 pr-3 text-charcoal-900 focus:outline-none focus:border-steel-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedStage}
              onChange={(e) => setSelectedStage(e.target.value)}
              className="bg-white border border-charcoal-200 rounded py-1.5 px-3 text-charcoal-800 focus:outline-none focus:border-steel-500"
            >
              <option value="all">All Stages ({applications.length})</option>
              {allStages.map(st => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>
          </div>
        </div>
      </Panel>

      {/* Table View */}
      {viewMode === 'table' && (
        <Panel className="overflow-hidden bg-white">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-canvas-50 border-b border-charcoal-200 text-charcoal-700 font-semibold uppercase text-[10px] tracking-wider">
                  <th className="py-3 px-4">Company & Role</th>
                  <th className="py-3 px-4">Stage</th>
                  <th className="py-3 px-4">Next Action</th>
                  <th className="py-3 px-4">Deadline</th>
                  <th className="py-3 px-4">Last Updated</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-charcoal-100">
                {filteredApps.map((app) => (
                  <tr
                    key={app.id}
                    onClick={() => navigate(`/app/applications/${app.id}`)}
                    className="hover:bg-canvas-50 cursor-pointer transition-colors"
                  >
                    <td className="py-3.5 px-4">
                      <div>
                        <span className="font-bold text-charcoal-900 text-xs block">{app.company}</span>
                        <span className="text-charcoal-600 text-[11px]">{app.jobTitle} • {app.jobType}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <StageBadge stage={app.stage} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 max-w-xs">
                      <p className="truncate text-charcoal-800 font-medium" title={app.nextAction}>
                        {app.nextAction}
                      </p>
                      <span className="text-[10px] text-charcoal-600">Due: {app.nextActionDueDate}</span>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-charcoal-700 font-mono text-[11px]">
                      {app.deadline}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-charcoal-600 text-[11px]">
                      {app.lastUpdated}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <span className="text-steel-600 hover:text-steel-800 font-semibold inline-flex items-center gap-1">
                        View <ArrowRight className="w-3 h-3" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* Kanban Board View */}
      {viewMode === 'kanban' && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 overflow-x-auto pb-4">
          {[
            { title: 'In Preparation', stages: ['Interested', 'Preparing', 'Awaiting approval'] as ApplicationStage[] },
            { title: 'Ready / Applied', stages: ['Ready to apply', 'Applied'] as ApplicationStage[] },
            { title: 'In Assessment & Interview', stages: ['Assessment', 'Interview'] as ApplicationStage[] },
            { title: 'Decisions / Complete', stages: ['Offer', 'Rejected', 'Withdrawn'] as ApplicationStage[] }
          ].map((column) => {
            const columnApps = applications.filter(a => column.stages.includes(a.stage));

            return (
              <div key={column.title} className="bg-canvas-50 border border-charcoal-200 rounded-lg p-3 min-w-[260px]">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-charcoal-200">
                  <h4 className="text-xs font-bold text-charcoal-800">{column.title}</h4>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-white text-charcoal-600 border border-charcoal-200">
                    {columnApps.length}
                  </span>
                </div>

                <div className="space-y-2.5">
                  {columnApps.map((app) => (
                    <div
                      key={app.id}
                      onClick={() => navigate(`/app/applications/${app.id}`)}
                      className="p-3 bg-white border border-charcoal-200 rounded shadow-xs hover:border-steel-400 cursor-pointer transition-colors text-xs"
                    >
                      <div className="flex items-start justify-between gap-1 mb-1">
                        <span className="font-bold text-charcoal-900">{app.company}</span>
                        <StageBadge stage={app.stage} size="sm" />
                      </div>
                      <p className="text-[11px] text-charcoal-600 truncate">{app.jobTitle}</p>

                      <div className="mt-2 pt-2 border-t border-charcoal-100 text-[10px] text-charcoal-600 flex items-center justify-between">
                        <span>Deadline: {app.deadline}</span>
                        <span className="text-steel-600 font-medium">Inspect →</span>
                      </div>
                    </div>
                  ))}

                  {columnApps.length === 0 && (
                    <div className="text-center py-6 text-[11px] text-charcoal-600">
                      No applications in this phase
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
