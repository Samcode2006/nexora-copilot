import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  MapPin,
  Calendar,
  DollarSign,
  Bookmark,
  BookmarkCheck,
  FileEdit,
  Mail,
  Send,
  CheckCircle2
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, PanelHeader, PanelBody, Button, FitScoreBadge, StageBadge } from '../../components/common/UIComponents';

export const JobDetailPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { getJobById, toggleSaveJob, createApplication, applications } = useApp();

  const job = jobId ? getJobById(jobId) : undefined;
  const existingApp = applications.find(a => a.jobId === jobId);

  if (!job) {
    return (
      <div className="text-center py-12">
        <h3 className="font-bold text-charcoal-900 text-sm">Opportunity Not Found</h3>
        <p className="text-xs text-charcoal-600 mt-1 mb-4">The requested job posting is not available or has expired.</p>
        <Button variant="outline" size="sm" onClick={() => navigate('/app/jobs')}>
          Back to Jobs List
        </Button>
      </div>
    );
  }

  const handleStartApplication = () => {
    const app = createApplication(job.id);
    navigate(`/app/applications/${app.id}`);
  };

  return (
    <div className="space-y-6">
      {/* Back button & Breadcrumb */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/app/jobs')}
          className="inline-flex items-center gap-1.5 text-xs text-charcoal-600 hover:text-charcoal-900 font-medium"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Opportunities</span>
        </button>

        <div className="flex items-center gap-2">
          {existingApp && (
            <div className="flex items-center gap-2 mr-2">
              <span className="text-xs text-charcoal-600 font-medium">Application Status:</span>
              <StageBadge stage={existingApp.stage} size="sm" />
            </div>
          )}
          <button
            onClick={() => toggleSaveJob(job.id)}
            className={`p-2 rounded border text-xs font-medium transition-colors flex items-center gap-1.5 ${
              job.saved
                ? 'bg-steel-50 text-steel-700 border-steel-300'
                : 'bg-white text-charcoal-700 border-charcoal-200 hover:bg-canvas-100'
            }`}
          >
            {job.saved ? <BookmarkCheck className="w-3.5 h-3.5 text-steel-600" /> : <Bookmark className="w-3.5 h-3.5" />}
            <span>{job.saved ? 'Saved' : 'Save'}</span>
          </button>
        </div>
      </div>

      {/* Header Overview Banner */}
      <Panel className="p-6 bg-white">
        <div className="flex flex-col md:flex-row items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className={`w-14 h-14 rounded-lg flex items-center justify-center font-bold text-xl shrink-0 shadow-xs ${job.logoBg}`}>
              {job.logoText}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg md:text-xl font-bold text-charcoal-900">{job.title}</h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-canvas-100 text-charcoal-700 border border-charcoal-200">
                  {job.type}
                </span>
              </div>
              <p className="text-xs text-charcoal-600 mt-1">
                <span className="font-semibold text-charcoal-800">{job.company}</span> • {job.department}
              </p>

              <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-charcoal-600">
                <span className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-charcoal-600" />
                  {job.location} ({job.workMode})
                </span>
                <span className="flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5 text-charcoal-600" />
                  {job.stipendSalary}
                </span>
                <span className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-charcoal-600" />
                  Deadline: {job.deadline}
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-start md:items-end gap-2 w-full md:w-auto">
            <FitScoreBadge score={job.fitScore} category={job.matchCategory} />
            <div className="flex items-center gap-2 mt-2 w-full md:w-auto">
              <Button
                variant="primary"
                size="md"
                onClick={handleStartApplication}
                icon={<Send className="w-3.5 h-3.5" />}
              >
                {existingApp ? 'View Application Pipeline' : 'Start Application Workflow'}
              </Button>
            </div>
          </div>
        </div>
      </Panel>

      {/* Grid: Why this matches you & Job Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Job Description, Responsibilities, Requirements */}
        <div className="lg:col-span-2 space-y-6">
          <Panel>
            <PanelHeader title="Role Overview" />
            <PanelBody className="space-y-4 text-xs text-charcoal-700 leading-relaxed">
              <p>{job.description}</p>

              <div>
                <h4 className="font-bold text-charcoal-900 mb-2">Core Responsibilities</h4>
                <ul className="space-y-1.5 pl-4 list-disc text-charcoal-700">
                  {job.responsibilities.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>

              <div className="pt-2">
                <h4 className="font-bold text-charcoal-900 mb-2">Requirements & Qualifications</h4>
                <ul className="space-y-1.5 pl-4 list-disc text-charcoal-700">
                  {job.requirements.map((req, i) => (
                    <li key={i}>{req}</li>
                  ))}
                </ul>
              </div>

              <div className="pt-2">
                <h4 className="font-bold text-charcoal-900 mb-2">Required Technical Stack</h4>
                <div className="flex flex-wrap gap-1.5">
                  {job.requiredSkills.map(s => (
                    <span key={s} className="px-2.5 py-1 bg-canvas-100 border border-charcoal-200 rounded text-xs text-charcoal-800 font-medium">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </PanelBody>
          </Panel>
        </div>

        {/* Right Col: Dedicated "Why This Matches You" Section & Document Actions */}
        <div className="space-y-6">
          {/* Why This Matches You */}
          <Panel className="border-steel-300 bg-white">
            <PanelHeader
              title="Why This Matches You"
              subtitle="Calibrated against your confirmed student profile"
            />
            <PanelBody className="space-y-4 text-xs">
              <div className="p-3 bg-canvas-50 border border-charcoal-200 rounded text-charcoal-700 leading-relaxed">
                "{job.matchExplanation}"
              </div>

              <div>
                <span className="font-bold text-charcoal-900 block mb-1.5">Matching Verified Skills</span>
                <div className="space-y-1">
                  {job.matchingSkills.map(s => (
                    <div key={s} className="flex items-center justify-between p-1.5 bg-emerald-50/60 border border-emerald-200 rounded text-[11px] text-emerald-900">
                      <span className="font-medium">{s}</span>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    </div>
                  ))}
                </div>
              </div>

              {job.missingSkills.length > 0 && (
                <div>
                  <span className="font-bold text-charcoal-900 block mb-1.5">Identified Skill Gaps</span>
                  <div className="space-y-1">
                    {job.missingSkills.map(s => (
                      <div key={s} className="flex items-center justify-between p-1.5 bg-amber-50/60 border border-amber-200 rounded text-[11px] text-amber-900">
                        <span>{s}</span>
                        <Link to="/app/skill-roadmap" className="text-[10px] text-steel-600 underline">Add to roadmap</Link>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="p-2.5 bg-canvas-100 rounded text-[11px] text-charcoal-600">
                <span className="font-semibold text-charcoal-800">Fit Disclaimer:</span> Match scores reflect skill overlap and do not guarantee an interview.
              </div>
            </PanelBody>
          </Panel>

          {/* Action Hub for this Opportunity */}
          <Panel>
            <PanelHeader title="Application Preparation" subtitle="Prepare materials for this role" />
            <PanelBody className="space-y-2.5">
              <Link to={`/app/resume-studio?jobId=${job.id}`} className="block">
                <Button variant="secondary" size="md" className="w-full justify-start" icon={<FileEdit className="w-4 h-4 text-steel-600" />}>
                  Tailor Resume for {job.company}
                </Button>
              </Link>

              <Link to={`/app/cover-letter?jobId=${job.id}`} className="block">
                <Button variant="secondary" size="md" className="w-full justify-start" icon={<Mail className="w-4 h-4 text-steel-600" />}>
                  Draft Cover Letter for {job.company}
                </Button>
              </Link>

              <Link to={`/app/interview-prep`} className="block">
                <Button variant="outline" size="md" className="w-full justify-start" icon={<CheckCircle2 className="w-4 h-4 text-charcoal-600" />}>
                  Practice Mock Interview for {job.company}
                </Button>
              </Link>
            </PanelBody>
          </Panel>
        </div>
      </div>
    </div>
  );
};
