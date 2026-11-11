import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Send,
  Save,
  Eye,
  ShieldCheck
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, PanelHeader, PanelBody, Button } from '../../components/common/UIComponents';
import type { CoverLetterDraft, Job } from '../../types';

export const CoverLetterPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { jobs, profile, coverLetters, saveCoverLetter, submitCoverLetterForApproval } = useApp();

  const selectedJobIdFromQuery = searchParams.get('jobId') || 'job-104'; // Default to Datadog or Linear
  const [selectedJobId, setSelectedJobId] = useState(selectedJobIdFromQuery);

  const selectedJob = jobs.find(j => j.id === selectedJobId) || jobs[0];

  const createDefaultLetter = (job: Job): CoverLetterDraft => ({
    id: `cov-draft-${job.id}`,
    jobId: job.id,
    jobTitle: job.title,
    company: job.company,
    recipientName: 'University Recruiting Team',
    recipientTitle: 'Campus Talent Partner',
    recipientCompany: `${job.company} India`,
    date: 'November 10, 2026',
    opening: `Dear ${job.company} Recruiting Team,`,
    bodyParagraph1: `I am writing to express my strong enthusiasm for the ${job.title} position at ${job.company}. Having followed your engineering advancements in ${job.domain}, I respect your dedication to high-availability architecture and developer tooling.`,
    bodyParagraph2: `As a final-year Computer Science student at ${profile.college}, my background centers on building resilient distributed systems with ${profile.skills.slice(0, 3).map(s => s.name).join(', ')}. During my internship at InnovateCloud Labs, I optimized telemetry indexing pipelines and designed asynchronous queues handling high concurrency.`,
    closing: `I would welcome the opportunity to contribute my systems curiosity and disciplined execution to ${job.company}. Thank you for your time and consideration.`,
    wordCount: 160,
    approvalStatus: 'draft'
  });

  const draftKey = `cov-draft-${selectedJob.company.toLowerCase()}`;
  const existingLetter = coverLetters[draftKey] || coverLetters['cov-draft-datadog'];

  const [letter, setLetter] = useState<CoverLetterDraft>(() => {
    if (existingLetter && existingLetter.jobId === selectedJob.id) {
      return existingLetter;
    }
    return createDefaultLetter(selectedJob);
  });

  const handleSelectJob = (jobId: string) => {
    setSelectedJobId(jobId);
    const found = Object.values(coverLetters).find(c => c.jobId === jobId);
    if (found) {
      setLetter(found);
    } else {
      const targetJob = jobs.find(j => j.id === jobId);
      if (targetJob) setLetter(createDefaultLetter(targetJob));
    }
  };

  // Recalculate word count
  const wordCount = (
    `${letter.opening} ${letter.bodyParagraph1} ${letter.bodyParagraph2} ${letter.closing}`
  ).trim().split(/\s+/).filter(Boolean).length;

  const handleSave = () => {
    saveCoverLetter({ ...letter, wordCount });
    alert('Cover letter draft saved.');
  };

  const handleSendToApproval = () => {
    submitCoverLetterForApproval({ ...letter, wordCount });
    navigate('/app/approvals');
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Cover Letter Editor</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-800 border border-blue-200">
              Role-Calibrated
            </span>
          </div>
          <p className="text-xs text-charcoal-600 mt-1">
            Target a concise, authentic 150-200 word cover letter tied directly to your verified profile.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={selectedJob.id}
            onChange={(e) => handleSelectJob(e.target.value)}
            className="bg-white border border-charcoal-200 rounded-md py-1.5 px-3 text-xs text-charcoal-900 font-semibold focus:outline-none focus:border-steel-500"
          >
            {jobs.map(j => (
              <option key={j.id} value={j.id}>
                {j.company} — {j.title}
              </option>
            ))}
          </select>

          <Button
            variant="primary"
            size="sm"
            onClick={handleSendToApproval}
            icon={<Send className="w-3.5 h-3.5" />}
          >
            Send to Approvals
          </Button>
        </div>
      </div>

      {/* Editor & Preview Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Structured Editor Form (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <Panel>
            <PanelHeader
              title={`Cover Letter for ${selectedJob.company}`}
              subtitle={`${wordCount} words • Recommended range: 140 - 220 words`}
              action={
                <Button variant="ghost" size="sm" onClick={handleSave} icon={<Save className="w-3.5 h-3.5" />}>
                  Save Draft
                </Button>
              }
            />
            <PanelBody className="space-y-4 text-xs">
              {/* Recipient info */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 bg-canvas-50 border border-charcoal-200 rounded-md">
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">Recipient Name</label>
                  <input
                    type="text"
                    value={letter.recipientName}
                    onChange={(e) => setLetter({ ...letter, recipientName: e.target.value })}
                    className="w-full bg-white border border-charcoal-200 rounded p-1.5 text-xs text-charcoal-900"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-charcoal-700 mb-1">Recipient Title</label>
                  <input
                    type="text"
                    value={letter.recipientTitle}
                    onChange={(e) => setLetter({ ...letter, recipientTitle: e.target.value })}
                    className="w-full bg-white border border-charcoal-200 rounded p-1.5 text-xs text-charcoal-900"
                  />
                </div>
              </div>

              {/* Salutation */}
              <div>
                <label className="block text-xs font-semibold text-charcoal-800 mb-1">Opening Salutation</label>
                <input
                  type="text"
                  value={letter.opening}
                  onChange={(e) => setLetter({ ...letter, opening: e.target.value })}
                  className="w-full bg-white border border-charcoal-200 rounded p-2 text-xs text-charcoal-900 font-medium"
                />
              </div>

              {/* Paragraph 1: Why this role & company */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-charcoal-800">
                    Paragraph 1: Why {selectedJob.company} & Alignment
                  </label>
                  <span className="text-[10px] text-charcoal-600">Contextual hook</span>
                </div>
                <textarea
                  rows={3}
                  value={letter.bodyParagraph1}
                  onChange={(e) => setLetter({ ...letter, bodyParagraph1: e.target.value })}
                  className="w-full bg-white border border-charcoal-200 rounded-md p-2.5 text-xs text-charcoal-900 leading-relaxed focus:outline-none focus:border-steel-500"
                />
              </div>

              {/* Paragraph 2: Proven Project / Experience Evidence */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-charcoal-800">
                    Paragraph 2: Evidence from Your Verified Projects
                  </label>
                  <span className="text-[10px] text-emerald-700 font-medium">Tied to master profile</span>
                </div>
                <textarea
                  rows={4}
                  value={letter.bodyParagraph2}
                  onChange={(e) => setLetter({ ...letter, bodyParagraph2: e.target.value })}
                  className="w-full bg-white border border-charcoal-200 rounded-md p-2.5 text-xs text-charcoal-900 leading-relaxed focus:outline-none focus:border-steel-500"
                />
              </div>

              {/* Closing */}
              <div>
                <label className="block text-xs font-semibold text-charcoal-800 mb-1">Closing & Forward Outlook</label>
                <textarea
                  rows={2}
                  value={letter.closing}
                  onChange={(e) => setLetter({ ...letter, closing: e.target.value })}
                  className="w-full bg-white border border-charcoal-200 rounded-md p-2.5 text-xs text-charcoal-900 leading-relaxed focus:outline-none focus:border-steel-500"
                />
              </div>
            </PanelBody>
          </Panel>

          <div className="p-3 rounded bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>This letter does not claim unverified degrees or false achievements. Approval required before submission.</span>
          </div>
        </div>

        {/* Right: Realistic Letter Paper Preview (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white border border-charcoal-300 rounded-lg shadow-dropdown overflow-hidden">
            <div className="bg-[#263747] px-4 py-2.5 flex items-center justify-between text-xs text-slate-200 border-b border-[#1B2834]">
              <span className="font-semibold flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5 text-steel-400" />
                <span>Rendered Document Preview</span>
              </span>
              <span className="text-[10px] font-mono text-slate-400">1 Page</span>
            </div>

            <div className="p-6 bg-white text-charcoal-900 text-xs leading-relaxed space-y-4 border-b border-charcoal-100 min-h-[460px]">
              <div>
                <p className="font-bold text-sm text-charcoal-900">{profile.fullName}</p>
                <p className="text-[11px] text-charcoal-600">{profile.location} • {profile.email}</p>
                <p className="text-[11px] text-charcoal-600">{letter.date}</p>
              </div>

              <div className="border-t border-charcoal-100 pt-3 text-[11px] text-charcoal-700">
                <p className="font-semibold">{letter.recipientName}</p>
                <p>{letter.recipientTitle}</p>
                <p>{letter.recipientCompany}</p>
              </div>

              <p className="font-semibold text-charcoal-900">{letter.opening}</p>

              <p className="text-charcoal-800 leading-relaxed">
                {letter.bodyParagraph1}
              </p>

              <p className="text-charcoal-800 leading-relaxed">
                {letter.bodyParagraph2}
              </p>

              <p className="text-charcoal-800 leading-relaxed">
                {letter.closing}
              </p>

              <div className="pt-2">
                <p className="text-charcoal-600">Sincerely,</p>
                <p className="font-bold text-charcoal-900 mt-2">{profile.fullName}</p>
                <p className="text-[10px] text-charcoal-600">{profile.degree}, {profile.college}</p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/app/resume-studio?jobId=${selectedJob.id}`)}
            >
              Back to Resume Studio
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={handleSendToApproval}
              icon={<Send className="w-3.5 h-3.5" />}
            >
              Continue to Approval Centre
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
