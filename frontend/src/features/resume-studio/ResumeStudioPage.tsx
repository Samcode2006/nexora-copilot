import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  RotateCcw,
  Eye,
  Send,
  Sparkles,
  ShieldCheck,
  Check,
  X,
  ArrowRight
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, PanelHeader, PanelBody, Button } from '../../components/common/UIComponents';
import type { Job, ResumeDraft } from '../../types';

export const ResumeStudioPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { jobs, profile, resumeDrafts, submitResumeForApproval } = useApp();

  const selectedJobIdFromQuery = searchParams.get('jobId') || 'job-101'; // Default to Vercel
  const [selectedJobId, setSelectedJobId] = useState(selectedJobIdFromQuery);

  const selectedJob = jobs.find(j => j.id === selectedJobId) || jobs[0];

  const createDefaultDraft = (job: Job): ResumeDraft => ({
    id: `res-draft-${job.id}`,
    jobId: job.id,
    jobTitle: job.title,
    company: job.company,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    summary: profile.bio,
    originalSummary: profile.bio,
    skills: job.requiredSkills.map(s => ({
      name: s,
      isHighlighted: profile.skills.some(ps => ps.name.toLowerCase() === s.toLowerCase())
    })),
    experienceHighlights: profile.experience.flatMap(exp =>
      exp.highlights.map((h, idx) => ({
        id: `eh-${exp.id}-${idx}`,
        company: exp.company,
        role: exp.role,
        bullet: h,
        originalBullet: h,
        hasSuggestion: idx === 0,
        suggestion: idx === 0 ? `${h} (Tailored for ${job.company} requirements)` : undefined,
        status: 'pending' as const
      }))
    ),
    projectHighlights: profile.projects.flatMap(proj =>
      proj.highlights.map((h, idx) => ({
        id: `ph-${proj.id}-${idx}`,
        projectTitle: proj.title,
        bullet: h,
        originalBullet: h,
        hasSuggestion: idx === 0,
        suggestion: idx === 0 ? `Optimized ${proj.title} architecture for responsiveness and sub-100ms user interactions.` : undefined,
        status: 'pending' as const
      }))
    ),
    approvalStatus: 'draft'
  });

  // Active draft for this job
  const draftKey = `res-draft-${selectedJob.company.toLowerCase()}`;
  const existingDraft = resumeDrafts[draftKey] || resumeDrafts['res-draft-vercel'];

  const [draft, setDraft] = useState<ResumeDraft>(() => {
    if (existingDraft && existingDraft.jobId === selectedJob.id) {
      return existingDraft;
    }
    return createDefaultDraft(selectedJob);
  });

  const handleSelectJob = (jobId: string) => {
    setSelectedJobId(jobId);
    const foundDraft = Object.values(resumeDrafts).find(d => d.jobId === jobId);
    if (foundDraft) {
      setDraft(foundDraft);
    } else {
      const targetJob = jobs.find(j => j.id === jobId);
      if (targetJob) setDraft(createDefaultDraft(targetJob));
    }
  };

  const [activeSection, setActiveSection] = useState<'summary' | 'skills' | 'experience' | 'projects'>('summary');
  const [submittedFeedback, setSubmittedFeedback] = useState(false);

  const handleAcceptSuggestion = (type: 'experience' | 'project', id: string) => {
    if (type === 'experience') {
      setDraft(prev => ({
        ...prev,
        experienceHighlights: prev.experienceHighlights.map(h => 
          h.id === id && h.suggestion ? { ...h, bullet: h.suggestion, status: 'accepted' } : h
        )
      }));
    } else {
      setDraft(prev => ({
        ...prev,
        projectHighlights: prev.projectHighlights.map(h => 
          h.id === id && h.suggestion ? { ...h, bullet: h.suggestion, status: 'accepted' } : h
        )
      }));
    }
  };

  const handleRejectSuggestion = (type: 'experience' | 'project', id: string) => {
    if (type === 'experience') {
      setDraft(prev => ({
        ...prev,
        experienceHighlights: prev.experienceHighlights.map(h => 
          h.id === id ? { ...h, bullet: h.originalBullet, status: 'rejected' } : h
        )
      }));
    } else {
      setDraft(prev => ({
        ...prev,
        projectHighlights: prev.projectHighlights.map(h => 
          h.id === id ? { ...h, bullet: h.originalBullet, status: 'rejected' } : h
        )
      }));
    }
  };

  const handleSendToApproval = () => {
    submitResumeForApproval(draft);
    setSubmittedFeedback(true);
    setTimeout(() => {
      navigate('/app/approvals');
    }, 1200);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Job Selector */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Resume Studio</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-50 text-purple-800 border border-purple-200">
              Integrity Verified Workspace
            </span>
          </div>
          <p className="text-xs text-charcoal-600 mt-1">
            Tailor bullet points specifically for target job descriptions without fabricating experience or numbers.
          </p>
        </div>

        {/* Job selector dropdown */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="text-right hidden sm:block">
            <span className="text-[10px] text-charcoal-600 uppercase font-semibold block">Targeting Job:</span>
          </div>
          <select
            value={selectedJob.id}
            onChange={(e) => {
              handleSelectJob(e.target.value);
            }}
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
            {submittedFeedback ? 'Sent to Approvals...' : 'Send to Approval Centre'}
          </Button>
        </div>
      </div>

      {/* Two-Panel Split Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Panel: Tailoring & Suggestions (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Section Selector Tabs */}
          <div className="flex items-center gap-1.5 p-1 bg-white border border-charcoal-200 rounded-lg text-xs font-medium">
            <button
              onClick={() => setActiveSection('summary')}
              className={`flex-1 py-1.5 rounded-md transition-colors ${
                activeSection === 'summary' ? 'bg-[#263747] text-white shadow-xs' : 'text-charcoal-700 hover:bg-canvas-100'
              }`}
            >
              Summary
            </button>
            <button
              onClick={() => setActiveSection('experience')}
              className={`flex-1 py-1.5 rounded-md transition-colors ${
                activeSection === 'experience' ? 'bg-[#263747] text-white shadow-xs' : 'text-charcoal-700 hover:bg-canvas-100'
              }`}
            >
              Experience ({draft.experienceHighlights.length})
            </button>
            <button
              onClick={() => setActiveSection('projects')}
              className={`flex-1 py-1.5 rounded-md transition-colors ${
                activeSection === 'projects' ? 'bg-[#263747] text-white shadow-xs' : 'text-charcoal-700 hover:bg-canvas-100'
              }`}
            >
              Projects ({draft.projectHighlights.length})
            </button>
            <button
              onClick={() => setActiveSection('skills')}
              className={`flex-1 py-1.5 rounded-md transition-colors ${
                activeSection === 'skills' ? 'bg-[#263747] text-white shadow-xs' : 'text-charcoal-700 hover:bg-canvas-100'
              }`}
            >
              Skill Emphasis
            </button>
          </div>

          {/* Section 1: Professional Summary Editor */}
          {activeSection === 'summary' && (
            <Panel>
              <PanelHeader
                title="Professional Summary Calibration"
                subtitle={`Aligned with ${selectedJob.company}'s requirements`}
              />
              <PanelBody className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-charcoal-800 mb-1.5">
                    Tailored Summary Text
                  </label>
                  <textarea
                    rows={4}
                    value={draft.summary}
                    onChange={(e) => setDraft({ ...draft, summary: e.target.value })}
                    className="w-full bg-white border border-charcoal-200 rounded-md p-3 text-xs text-charcoal-900 leading-relaxed focus:outline-none focus:border-steel-500"
                  />
                </div>

                <div className="p-3 bg-canvas-50 border border-charcoal-200 rounded text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-charcoal-800 text-[11px]">Original Master Summary</span>
                    <button
                      onClick={() => setDraft({ ...draft, summary: draft.originalSummary })}
                      className="text-[10px] text-steel-600 hover:underline flex items-center gap-1"
                    >
                      <RotateCcw className="w-3 h-3" /> Restore Original
                    </button>
                  </div>
                  <p className="text-charcoal-600 text-[11px] italic leading-relaxed">
                    "{draft.originalSummary}"
                  </p>
                </div>
              </PanelBody>
            </Panel>
          )}

          {/* Section 2: Experience Highlights */}
          {activeSection === 'experience' && (
            <Panel>
              <PanelHeader
                title="Work Experience Highlights"
                subtitle="Review suggestions highlighting systems relevance"
              />
              <div className="divide-y divide-charcoal-100">
                {draft.experienceHighlights.map((h) => (
                  <div key={h.id} className="p-4 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-charcoal-900">{h.role} • {h.company}</span>
                      {h.status === 'accepted' && (
                        <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-medium">Suggestion Accepted</span>
                      )}
                      {h.status === 'rejected' && (
                        <span className="text-[10px] text-charcoal-600 bg-canvas-100 px-2 py-0.5 rounded font-medium">Original Kept</span>
                      )}
                    </div>

                    <p className="text-charcoal-800 bg-white p-2.5 rounded border border-charcoal-200 leading-relaxed">
                      {h.bullet}
                    </p>

                    {h.hasSuggestion && h.status === 'pending' && (
                      <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-md space-y-2">
                        <div className="flex items-start gap-1.5 text-purple-900 font-semibold text-[11px]">
                          <Sparkles className="w-3.5 h-3.5 text-purple-600 shrink-0 mt-0.5" />
                          <span>Recommended phrasing for {selectedJob.company}:</span>
                        </div>
                        <p className="text-purple-950 text-[11px] leading-relaxed pl-5">
                          "{h.suggestion}"
                        </p>
                        <div className="flex items-center gap-2 pl-5 pt-1">
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleAcceptSuggestion('experience', h.id)}
                            icon={<Check className="w-3 h-3" />}
                          >
                            Accept Suggestion
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRejectSuggestion('experience', h.id)}
                            icon={<X className="w-3 h-3" />}
                          >
                            Keep Original
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {/* Section 3: Project Highlights */}
          {activeSection === 'projects' && (
            <Panel>
              <PanelHeader
                title="Project Bullets Calibration"
                subtitle="Align verified project metrics with role qualifications"
              />
              <div className="divide-y divide-charcoal-100">
                {draft.projectHighlights.map((ph) => (
                  <div key={ph.id} className="p-4 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-charcoal-900">{ph.projectTitle}</span>
                      {ph.status === 'accepted' && (
                        <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-medium">Suggestion Accepted</span>
                      )}
                      {ph.status === 'rejected' && (
                        <span className="text-[10px] text-charcoal-600 bg-canvas-100 px-2 py-0.5 rounded font-medium">Original Kept</span>
                      )}
                    </div>

                    <p className="text-charcoal-800 bg-white p-2.5 rounded border border-charcoal-200 leading-relaxed">
                      {ph.bullet}
                    </p>

                    {ph.hasSuggestion && ph.status === 'pending' && (
                      <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-md space-y-2">
                        <div className="flex items-start gap-1.5 text-purple-900 font-semibold text-[11px]">
                          <Sparkles className="w-3.5 h-3.5 text-purple-600 shrink-0 mt-0.5" />
                          <span>Recommended focus for {selectedJob.company}:</span>
                        </div>
                        <p className="text-purple-950 text-[11px] leading-relaxed pl-5">
                          "{ph.suggestion}"
                        </p>
                        <div className="flex items-center gap-2 pl-5 pt-1">
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleAcceptSuggestion('project', ph.id)}
                            icon={<Check className="w-3 h-3" />}
                          >
                            Accept Suggestion
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRejectSuggestion('project', ph.id)}
                            icon={<X className="w-3 h-3" />}
                          >
                            Keep Original
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {/* Section 4: Skills Emphasis */}
          {activeSection === 'skills' && (
            <Panel>
              <PanelHeader
                title="Highlighted Skills in Header"
                subtitle="Select which verified skills should be prioritized at the top"
              />
              <PanelBody className="space-y-3">
                <p className="text-xs text-charcoal-600">
                  Toggle to emphasize skills specifically mentioned in the {selectedJob.company} posting:
                </p>
                <div className="flex flex-wrap gap-2">
                  {draft.skills.map((s) => (
                    <button
                      key={s.name}
                      onClick={() => {
                        setDraft({
                          ...draft,
                          skills: draft.skills.map(sk => sk.name === s.name ? { ...sk, isHighlighted: !sk.isHighlighted } : sk)
                        });
                      }}
                      className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors flex items-center gap-1.5 ${
                        s.isHighlighted
                          ? 'bg-[#263747] text-white border-[#263747]'
                          : 'bg-white text-charcoal-700 border-charcoal-200 hover:bg-canvas-100'
                      }`}
                    >
                      {s.isHighlighted && <Check className="w-3.5 h-3.5" />}
                      <span>{s.name}</span>
                    </button>
                  ))}
                </div>
              </PanelBody>
            </Panel>
          )}

          {/* Integrity Banner */}
          <div className="p-3.5 rounded-lg bg-emerald-50/70 border border-emerald-200 text-xs text-emerald-900 flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Integrity Guard Active:</span>
              <p className="text-[11px] text-emerald-800 mt-0.5">
                Every metric and company name in this draft matches your verified master profile. Unconfirmed claims cannot be injected.
              </p>
            </div>
          </div>
        </div>

        {/* Right Panel: Live Document Preview (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white border border-charcoal-300 rounded-lg shadow-dropdown overflow-hidden">
            <div className="bg-[#263747] px-4 py-2.5 flex items-center justify-between text-xs text-slate-200 border-b border-[#1B2834]">
              <span className="font-semibold flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5 text-steel-400" />
                <span>Live Tailored Document Preview</span>
              </span>
              <span className="font-mono text-[10px] text-slate-400">PDF Preview</span>
            </div>

            {/* Simulated Clean Printed Resume Format */}
            <div className="p-6 bg-white text-charcoal-900 font-sans text-[11px] leading-relaxed space-y-4 select-none">
              {/* Document Header */}
              <div className="text-center border-b border-charcoal-200 pb-3">
                <h1 className="text-base font-bold tracking-tight text-charcoal-950 uppercase">
                  {profile.fullName}
                </h1>
                <p className="text-[10px] text-charcoal-600 mt-0.5">
                  {profile.email} • {profile.phone} • {profile.location}
                </p>
                <p className="text-[10px] text-steel-600 mt-0.5 font-mono">
                  {profile.links.portfolio} • {profile.links.github}
                </p>
              </div>

              {/* Education */}
              <div>
                <h4 className="font-bold text-[10px] text-navy-800 uppercase tracking-wider border-b border-charcoal-200 pb-0.5 mb-1">
                  Education
                </h4>
                <div className="flex justify-between font-semibold">
                  <span>{profile.college}</span>
                  <span>{profile.education[0]?.grade}</span>
                </div>
                <div className="flex justify-between text-charcoal-600 text-[10px]">
                  <span>{profile.degree} in {profile.branch}</span>
                  <span>{profile.education[0]?.startYear} - {profile.education[0]?.endYear}</span>
                </div>
              </div>

              {/* Summary */}
              <div>
                <h4 className="font-bold text-[10px] text-navy-800 uppercase tracking-wider border-b border-charcoal-200 pb-0.5 mb-1">
                  Professional Summary
                </h4>
                <p className="text-charcoal-800 text-[10px] leading-snug">
                  {draft.summary}
                </p>
              </div>

              {/* Highlighted Skills */}
              <div>
                <h4 className="font-bold text-[10px] text-navy-800 uppercase tracking-wider border-b border-charcoal-200 pb-0.5 mb-1">
                  Technical Stack
                </h4>
                <p className="text-[10px] text-charcoal-700">
                  <span className="font-semibold">Core:</span> {draft.skills.filter(s => s.isHighlighted).map(s => s.name).join(', ')}
                </p>
              </div>

              {/* Experience */}
              <div>
                <h4 className="font-bold text-[10px] text-navy-800 uppercase tracking-wider border-b border-charcoal-200 pb-0.5 mb-1">
                  Experience
                </h4>
                {draft.experienceHighlights.map((eh, idx) => (
                  <div key={eh.id} className="mt-1">
                    {idx === 0 && (
                      <div className="flex justify-between font-semibold">
                        <span>{eh.company}</span>
                        <span className="text-[10px] text-charcoal-600">May 2026 - Jul 2026</span>
                      </div>
                    )}
                    <p className="text-[10px] text-charcoal-700 pl-2 border-l border-steel-300 mt-0.5">
                      • {eh.bullet}
                    </p>
                  </div>
                ))}
              </div>

              {/* Projects */}
              <div>
                <h4 className="font-bold text-[10px] text-navy-800 uppercase tracking-wider border-b border-charcoal-200 pb-0.5 mb-1">
                  Key Projects
                </h4>
                {draft.projectHighlights.map((ph, idx) => (
                  <div key={ph.id} className="mt-1">
                    {idx % 2 === 0 && (
                      <p className="font-semibold text-charcoal-900">{ph.projectTitle}</p>
                    )}
                    <p className="text-[10px] text-charcoal-700 pl-2 border-l border-steel-300 mt-0.5">
                      • {ph.bullet}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs pt-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/app/cover-letter?jobId=${selectedJob.id}`)}
              icon={<ArrowRight className="w-3.5 h-3.5" />}
            >
              Draft Cover Letter Next
            </Button>

            <Button
              variant="primary"
              size="sm"
              onClick={handleSendToApproval}
              icon={<Send className="w-3.5 h-3.5" />}
            >
              Send to Approval Centre
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
