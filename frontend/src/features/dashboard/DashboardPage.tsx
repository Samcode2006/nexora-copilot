import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  ArrowRight,
  ArrowUpRight,
  ChevronRight
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, Button, StageBadge, FitScoreBadge } from '../../components/common/UIComponents';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { profile, jobs, applications, approvals, calendarEvents } = useApp();

  const firstName = profile.fullName.split(' ')[0] || 'Student';
  const activeApplications = applications.filter(a => !['Rejected', 'Withdrawn'].includes(a.stage));
  const pendingApprovals = approvals.filter(a => a.status === 'pending');
  const recommendedJobs = jobs.slice(0, 3);
  const upcomingDeadlines = calendarEvents.filter(e => !e.completed).slice(0, 4);

  return (
    <div className="space-y-7 max-w-6xl mx-auto">
      {/* 1. Warm Editorial Hero Banner (Directly inspired by HALO LAB / Filko Image 2) */}
      <div className="bg-sand-200 border border-charcoal-200/70 rounded-3xl p-6 md:p-8 shadow-card grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Left Side: Greeting & Statement (7 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div>
            <span className="text-xs font-bold text-coral-600 uppercase tracking-wider block mb-1">
              Salut, {firstName}!
            </span>
            <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold text-charcoal-900 tracking-tight leading-tight">
              You have 1 interview &amp; 1 pending approval this week.
            </h1>
          </div>

          <p className="text-xs md:text-sm text-charcoal-600 leading-relaxed max-w-md">
            Your Round 2 Systems session with Stripe is scheduled for Saturday, and your tailored resume for Vercel is ready for review.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link to="/app/interview-prep">
              <Button
                variant="secondary"
                size="md"
                className="rounded-full px-5 shadow-card"
                icon={<ArrowUpRight className="w-4 h-4 text-coral-400" />}
              >
                Start Interview Prep
              </Button>
            </Link>
            {pendingApprovals.length > 0 && (
              <Link to="/app/approvals">
                <Button
                  variant="primary"
                  size="md"
                  className="rounded-full px-5 shadow-card"
                  icon={<AlertCircle className="w-4 h-4" />}
                >
                  Review Approval (1)
                </Button>
              </Link>
            )}
          </div>
        </div>

        {/* Right Side: 3 Colorful Milestone Cards (01, 02, 03 from Image 2!) */}
        <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Card 01 - Coral (Stripe Interview) */}
          <div
            onClick={() => navigate('/app/applications/app-001')}
            className="bg-coral-500 text-white rounded-2xl p-4 shadow-card hover:shadow-float hover:-translate-y-1 transition-all cursor-pointer flex flex-col justify-between min-h-[140px]"
          >
            <span className="text-xs font-black opacity-80 font-mono">01</span>
            <div className="space-y-1 mt-4">
              <h4 className="font-bold text-sm tracking-tight leading-snug">Stripe Systems</h4>
              <p className="text-[11px] text-coral-100 leading-tight">Round 2 • Nov 15</p>
            </div>
            <span className="text-[10px] font-bold text-white/90 pt-2 flex items-center gap-1">
              Prep guide <ArrowRight className="w-3 h-3" />
            </span>
          </div>

          {/* Card 02 - Ochre (Vercel Resume Approval) */}
          <div
            onClick={() => navigate('/app/approvals')}
            className="bg-ochre-400 text-navy-950 rounded-2xl p-4 shadow-card hover:shadow-float hover:-translate-y-1 transition-all cursor-pointer flex flex-col justify-between min-h-[140px]"
          >
            <span className="text-xs font-black opacity-70 font-mono">02</span>
            <div className="space-y-1 mt-4">
              <h4 className="font-bold text-sm tracking-tight leading-snug">Vercel Resume</h4>
              <p className="text-[11px] text-navy-900/80 leading-tight">Awaiting Approval</p>
            </div>
            <span className="text-[10px] font-bold text-navy-950 pt-2 flex items-center gap-1">
              Inspect draft <ArrowRight className="w-3 h-3" />
            </span>
          </div>

          {/* Card 03 - Violet (Atlassian Challenge) */}
          <div
            onClick={() => navigate('/app/applications/app-002')}
            className="bg-violet-500 text-white rounded-2xl p-4 shadow-card hover:shadow-float hover:-translate-y-1 transition-all cursor-pointer flex flex-col justify-between min-h-[140px]"
          >
            <span className="text-xs font-black opacity-80 font-mono">03</span>
            <div className="space-y-1 mt-4">
              <h4 className="font-bold text-sm tracking-tight leading-snug">Atlassian Test</h4>
              <p className="text-[11px] text-violet-100 leading-tight">HackerRank • Nov 14</p>
            </div>
            <span className="text-[10px] font-bold text-white/90 pt-2 flex items-center gap-1">
              View challenge <ArrowRight className="w-3 h-3" />
            </span>
          </div>
        </div>
      </div>

      {/* 2. Structured Two-Column Layout (Pipeline on Left, Scheduled on Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-7">
        {/* Left Column (7 cols): Active Application Pipeline */}
        <div className="lg:col-span-7 space-y-6">
          <Panel>
            <div className="p-5 border-b border-charcoal-100 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-charcoal-900">Active Application Pipeline</h3>
                <p className="text-xs text-charcoal-500 mt-0.5">Tracking {activeApplications.length} active opportunities</p>
              </div>

              <Link to="/app/applications" className="text-xs font-bold text-coral-600 hover:text-coral-700 flex items-center gap-1">
                <span>See All ({applications.length})</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {/* Pipeline Rows (Clean editorial rows like Filko Module items) */}
            <div className="divide-y divide-charcoal-100">
              {activeApplications.slice(0, 4).map((app) => (
                <div
                  key={app.id}
                  onClick={() => navigate(`/app/applications/${app.id}`)}
                  className="p-4 hover:bg-canvas-50 cursor-pointer transition-colors flex items-center justify-between gap-4 text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-sand-100 border border-charcoal-200/80 flex items-center justify-center font-bold text-xs text-charcoal-900 shrink-0 shadow-subtle">
                      {app.company.charAt(0)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-charcoal-900 truncate">{app.company}</h4>
                        <span className="text-charcoal-300">•</span>
                        <span className="text-charcoal-600 truncate">{app.jobTitle}</span>
                      </div>
                      <p className="text-[11px] text-charcoal-500 mt-0.5 truncate">
                        Next: {app.nextAction}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <StageBadge stage={app.stage} size="sm" />
                    <span className="text-charcoal-400 font-mono text-[11px] hidden sm:inline">
                      {app.deadline}
                    </span>
                    <ChevronRight className="w-4 h-4 text-charcoal-400" />
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          {/* Recommended Opportunities Panel */}
          <Panel>
            <div className="p-5 border-b border-charcoal-100 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-charcoal-900">Recommended Opportunities</h3>
                <p className="text-xs text-charcoal-500 mt-0.5">Matched with your confirmed profile skills</p>
              </div>

              <Link to="/app/jobs" className="text-xs font-bold text-coral-600 hover:text-coral-700 flex items-center gap-1">
                <span>Browse All</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="divide-y divide-charcoal-100">
              {recommendedJobs.map((job) => (
                <div
                  key={job.id}
                  onClick={() => navigate(`/app/jobs/${job.id}`)}
                  className="p-4 hover:bg-canvas-50 cursor-pointer transition-colors flex items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 shadow-subtle ${job.logoBg}`}>
                      {job.logoText}
                    </div>
                    <div className="min-w-0">
                      <h4 className="font-bold text-charcoal-900 truncate hover:text-coral-600 transition-colors">
                        {job.title}
                      </h4>
                      <p className="text-[11px] text-charcoal-500 mt-0.5 truncate">
                        {job.company} • {job.location} ({job.workMode}) • <span className="font-semibold text-charcoal-800">{job.stipendSalary}</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <FitScoreBadge score={job.fitScore} showCategory={false} />
                    <span className="text-coral-600 font-bold hidden sm:inline text-xs">
                      View →
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        {/* Right Column (5 cols): Scheduled Items (Filko Style) */}
        <div className="lg:col-span-5 space-y-6">
          <Panel>
            <div className="p-5 border-b border-charcoal-100 flex items-center justify-between">
              <h3 className="font-bold text-sm text-charcoal-900">Scheduled Deadlines</h3>
              <Link to="/app/calendar" className="text-xs font-bold text-coral-600 hover:text-coral-700">
                See all
              </Link>
            </div>

            <div className="p-5 space-y-3.5">
              {upcomingDeadlines.map((evt) => (
                <div
                  key={evt.id}
                  onClick={() => navigate(evt.applicationId ? `/app/applications/${evt.applicationId}` : '/app/calendar')}
                  className="p-3.5 rounded-2xl bg-sand-50 border border-charcoal-200/60 hover:border-charcoal-300 transition-all cursor-pointer flex items-start gap-3.5 text-xs shadow-subtle"
                >
                  <div className="text-center px-2.5 py-1.5 bg-white border border-charcoal-200/80 rounded-xl shrink-0 min-w-[54px] shadow-subtle">
                    <span className="font-extrabold text-charcoal-900 font-mono text-xs block">
                      {new Date(evt.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                    <span className="text-[9px] text-coral-600 uppercase font-black tracking-wide">
                      {evt.type}
                    </span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <h5 className="font-bold text-charcoal-900 text-xs truncate">
                      {evt.title}
                    </h5>
                    <p className="text-[11px] text-charcoal-500 mt-0.5 truncate">
                      {evt.time ? `${evt.time} • ` : ''}{evt.description || 'Action scheduled'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          {/* Quick Readiness Progress Card */}
          <div className="bg-white border border-charcoal-200/80 rounded-2xl p-5 shadow-card space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-charcoal-900">Placement Readiness</span>
              <span className="font-extrabold text-coral-600 text-xs">{profile.completeness}%</span>
            </div>
            <div className="w-full bg-sand-200 h-2 rounded-full overflow-hidden">
              <div className="bg-coral-500 h-full rounded-full transition-all duration-300" style={{ width: `${profile.completeness}%` }} />
            </div>
            <p className="text-[11px] text-charcoal-500 leading-relaxed">
              Master resume and verified skills indexed. 1 interview actively scheduled for this Saturday.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
