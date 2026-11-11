import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Clock,
  FileText,
  Mail,
  Send
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, PanelHeader, PanelBody, Button, StageBadge } from '../../components/common/UIComponents';
import type { ApplicationStage } from '../../types';

export const ApplicationDetailPage: React.FC = () => {
  const { applicationId } = useParams<{ applicationId: string }>();
  const navigate = useNavigate();
  const { getApplicationById, updateApplicationStage } = useApp();

  const application = applicationId ? getApplicationById(applicationId) : undefined;

  const [newNote, setNewNote] = useState('');
  const [showStageSuccess, setShowStageSuccess] = useState(false);

  if (!application) {
    return (
      <div className="text-center py-12">
        <h3 className="font-bold text-charcoal-900 text-sm">Application Not Found</h3>
        <p className="text-xs text-charcoal-600 mt-1 mb-4">The requested application record could not be found.</p>
        <Button variant="outline" size="sm" onClick={() => navigate('/app/applications')}>
          Back to Pipeline
        </Button>
      </div>
    );
  }

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

  const handleStageChange = (newStage: ApplicationStage) => {
    updateApplicationStage(application.id, newStage, `Stage updated to ${newStage}`);
    setShowStageSuccess(true);
    setTimeout(() => setShowStageSuccess(false), 2000);
  };

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    updateApplicationStage(application.id, application.stage, newNote.trim());
    setNewNote('');
  };

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/app/applications')}
        className="inline-flex items-center gap-1.5 text-xs text-charcoal-600 hover:text-charcoal-900 font-medium"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Application Tracker</span>
      </button>

      {/* Main Banner */}
      <Panel className="p-6 bg-white">
        <div className="flex flex-col md:flex-row items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg md:text-xl font-bold text-charcoal-900">{application.company}</h2>
              <span className="text-charcoal-300">•</span>
              <span className="text-sm font-semibold text-charcoal-700">{application.jobTitle}</span>
              <StageBadge stage={application.stage} />
            </div>

            <p className="text-xs text-charcoal-600 mt-1">
              Application ID: <span className="font-mono text-charcoal-800">{application.id}</span> • Type: {application.jobType} • Location: {application.location}
            </p>

            <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-charcoal-600">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" /> Added: {application.dateAdded}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 font-semibold text-charcoal-800">
                <Clock className="w-3.5 h-3.5" /> Deadline: {application.deadline}
              </span>
            </div>
          </div>

          {/* Stage Switcher Tool (Interactive demo feature) */}
          <div className="flex flex-col items-start md:items-end gap-1.5 p-3 bg-canvas-50 border border-charcoal-200 rounded-md text-xs w-full md:w-auto">
            <span className="font-semibold text-charcoal-800 text-[11px]">Update Pipeline Stage:</span>
            <div className="flex items-center gap-2">
              <select
                value={application.stage}
                onChange={(e) => handleStageChange(e.target.value as ApplicationStage)}
                className="bg-white border border-charcoal-300 rounded px-2.5 py-1 text-xs font-semibold text-charcoal-900 focus:outline-none focus:border-steel-500"
              >
                {allStages.map(st => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
            </div>
            {showStageSuccess && (
              <span className="text-[10px] text-emerald-700 font-semibold animate-in fade-in">
                ✓ Updated across dashboard
              </span>
            )}
          </div>
        </div>
      </Panel>

      {/* Grid: Details, Timeline, Interview Prep */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Timeline & Application Notes */}
        <div className="lg:col-span-2 space-y-6">
          {/* Scheduled Interview Details (if scheduled) */}
          {application.interviewDetails && (
            <Panel className="border-emerald-300 bg-emerald-50/30">
              <PanelHeader
                title="Upcoming Interview Details"
                subtitle="Confirmed with campus recruiting"
                action={
                  <Link to="/app/interview-prep">
                    <Button variant="primary" size="sm">
                      Open Interview Prep →
                    </Button>
                  </Link>
                }
              />
              <PanelBody className="space-y-3 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <span className="text-[11px] text-charcoal-600 block">Round & Topic:</span>
                    <span className="font-bold text-charcoal-900">{application.interviewDetails.round}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-charcoal-600 block">Date & Time:</span>
                    <span className="font-bold text-charcoal-900">{application.interviewDetails.date} ({application.interviewDetails.time})</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-charcoal-600 block">Interviewers:</span>
                    <span className="text-charcoal-800">{application.interviewDetails.interviewers.join(', ')}</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-charcoal-600 block">Meeting Platform:</span>
                    <span className="text-charcoal-800">{application.interviewDetails.platform}</span>
                  </div>
                </div>

                <div className="p-2.5 bg-white border border-emerald-200 rounded text-emerald-950 text-[11px]">
                  <span className="font-bold">Preparation Note:</span> {application.interviewDetails.notes}
                </div>
              </PanelBody>
            </Panel>
          )}

          {/* Chronological Timeline */}
          <Panel>
            <PanelHeader title="Application Event History & Audit Log" />
            <div className="p-5">
              <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-charcoal-200">
                {application.timeline.map((event) => (
                  <div key={event.id} className="relative">
                    <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-steel-600 ring-4 ring-white" />
                    <div className="text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-charcoal-900">{event.stage}</span>
                        <span className="text-charcoal-600 text-[11px]">• {event.date}</span>
                        <span className="text-[10px] text-steel-700 bg-steel-50 px-1.5 py-0.2 rounded font-medium">
                          {event.author}
                        </span>
                      </div>
                      <p className="text-charcoal-700 mt-1 leading-relaxed">
                        {event.note}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Add manual note */}
              <form onSubmit={handleAddNote} className="mt-6 pt-4 border-t border-charcoal-100 flex gap-2">
                <input
                  type="text"
                  placeholder="Add a log entry or note (e.g. Sent follow-up email to recruiter)..."
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  className="flex-1 bg-canvas-50 border border-charcoal-200 rounded px-3 py-1.5 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
                />
                <Button type="submit" variant="secondary" size="sm">
                  Add Entry
                </Button>
              </form>
            </div>
          </Panel>
        </div>

        {/* Right Col: Associated Application Packet & Actions */}
        <div className="space-y-6">
          <Panel>
            <PanelHeader title="Associated Application Packet" />
            <PanelBody className="space-y-3 text-xs">
              {/* Tailored Resume */}
              <div className="p-3 border border-charcoal-200 rounded bg-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-purple-600" />
                  <div>
                    <span className="font-semibold text-charcoal-900 block">Tailored Resume</span>
                    <span className="text-[10px] text-charcoal-600">Configured in Resume Studio</span>
                  </div>
                </div>
                <Link to={`/app/resume-studio?jobId=${application.jobId}`}>
                  <span className="text-steel-600 hover:underline text-[11px] font-semibold">Open →</span>
                </Link>
              </div>

              {/* Cover Letter */}
              <div className="p-3 border border-charcoal-200 rounded bg-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-blue-600" />
                  <div>
                    <span className="font-semibold text-charcoal-900 block">Cover Letter Draft</span>
                    <span className="text-[10px] text-charcoal-600">Customized for {application.company}</span>
                  </div>
                </div>
                <Link to={`/app/cover-letter?jobId=${application.jobId}`}>
                  <span className="text-steel-600 hover:underline text-[11px] font-semibold">Open →</span>
                </Link>
              </div>

              {/* Follow-up assistant shortcut */}
              <div className="p-3 border border-charcoal-200 rounded bg-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Send className="w-4 h-4 text-steel-600" />
                  <div>
                    <span className="font-semibold text-charcoal-900 block">Follow-up Assistant</span>
                    <span className="text-[10px] text-charcoal-600">Draft polite status inquiry</span>
                  </div>
                </div>
                <Link to={`/app/follow-ups`}>
                  <span className="text-steel-600 hover:underline text-[11px] font-semibold">Draft →</span>
                </Link>
              </div>
            </PanelBody>
          </Panel>

          {/* Next Recommended Action */}
          <Panel className="border-steel-300 bg-steel-50/40">
            <PanelHeader title="Next Action on File" />
            <PanelBody className="space-y-2 text-xs">
              <p className="font-semibold text-charcoal-900">{application.nextAction}</p>
              <p className="text-[11px] text-charcoal-600">Target Completion: {application.nextActionDueDate}</p>
            </PanelBody>
          </Panel>
        </div>
      </div>
    </div>
  );
};
