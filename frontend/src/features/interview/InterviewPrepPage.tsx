import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Play,
  Award
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, PanelHeader, PanelBody, Button } from '../../components/common/UIComponents';

export const InterviewPrepPage: React.FC = () => {
  const navigate = useNavigate();
  const { jobs, interviewSessions, feedbackReport, startNewSession } = useApp();

  const [targetCompany, setTargetCompany] = useState('Stripe');
  const [targetRole, setTargetRole] = useState('Junior Software Engineer (Backend Systems)');
  const [interviewType, setInterviewType] = useState<'Technical' | 'Behavioural' | 'HR' | 'Role-specific'>('Technical');
  const [difficulty, setDifficulty] = useState<'Junior' | 'Mid' | 'Challenging'>('Mid');

  const handleStartPractice = () => {
    const newSessionId = startNewSession(targetRole, targetCompany, interviewType, difficulty);
    navigate(`/app/interview-prep/${newSessionId}`);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Interview Preparation</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
              Structured Simulation
            </span>
          </div>
          <p className="text-xs text-charcoal-600 mt-1 max-w-2xl leading-relaxed">
            Practice realistic technical architecture and behavioral questions tailored to company expectations. Receive scored feedback that feeds your Skill Roadmap.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/app/feedback">
            <Button variant="outline" size="sm" icon={<Award className="w-3.5 h-3.5" />}>
              View Latest Feedback ({feedbackReport.overallScore}%)
            </Button>
          </Link>
        </div>
      </div>

      {/* Grid: Start Practice Config & Upcoming Interviews */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Practice Setup (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          <Panel>
            <PanelHeader
              title="Configure Mock Interview Practice"
              subtitle="Calibrate role, difficulty, and question depth"
            />
            <PanelBody className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-charcoal-800 mb-1.5">Target Company</label>
                <select
                  value={targetCompany}
                  onChange={(e) => {
                    setTargetCompany(e.target.value);
                    const matchingJob = jobs.find(j => j.company === e.target.value);
                    if (matchingJob) setTargetRole(matchingJob.title);
                  }}
                  className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900 focus:outline-none focus:border-steel-500"
                >
                  {jobs.map(j => (
                    <option key={j.id} value={j.company}>{j.company}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-charcoal-800 mb-1.5">Target Engineering Role</label>
                <input
                  type="text"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-charcoal-800 mb-1.5">Interview Round Type</label>
                  <select
                    value={interviewType}
                    onChange={(e) => setInterviewType(e.target.value as 'Technical' | 'Behavioural' | 'HR' | 'Role-specific')}
                    className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
                  >
                    <option value="Technical">Technical Systems & Coding</option>
                    <option value="Behavioural">Behavioural & Leadership STAR</option>
                    <option value="Role-specific">Role-Specific Architecture</option>
                    <option value="HR">HR & Cultural Alignment</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-charcoal-800 mb-1.5">Difficulty Calibration</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value as 'Junior' | 'Mid' | 'Challenging')}
                    className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
                  >
                    <option value="Junior">Junior / New Grad</option>
                    <option value="Mid">Mid-Level / Challenging</option>
                    <option value="Challenging">Senior / Staff Deep Dive</option>
                  </select>
                </div>
              </div>

              <div className="p-3 bg-canvas-50 border border-charcoal-200 rounded text-[11px] text-charcoal-700">
                <span className="font-semibold text-charcoal-900">Format:</span> 3 structured questions with problem-solving frameworks, real-time answer input, and actionable rubric feedback.
              </div>

              <div className="pt-2">
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full"
                  onClick={handleStartPractice}
                  icon={<Play className="w-4 h-4 fill-current" />}
                >
                  Start Practice Session Now
                </Button>
              </div>
            </PanelBody>
          </Panel>
        </div>

        {/* Right: Readiness Overview & Past Sessions (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Readiness Score Panel */}
          <Panel className="border-emerald-300 bg-emerald-50/30">
            <PanelHeader title="Interview Readiness Overview" />
            <PanelBody className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-2xl font-bold text-charcoal-900">{feedbackReport.overallScore}%</span>
                  <span className="text-[11px] text-emerald-800 font-semibold block">Demonstrated Performance</span>
                </div>
                <span className="px-2.5 py-1 bg-white border border-emerald-300 rounded text-xs font-bold text-emerald-800">
                  Ready for Round 2
                </span>
              </div>

              <div className="space-y-1.5 pt-2 border-t border-emerald-200/60 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-charcoal-600">Communication & Clarity:</span>
                  <span className="font-bold text-charcoal-900">{feedbackReport.scores.communication}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-charcoal-600">Technical Depth:</span>
                  <span className="font-bold text-charcoal-900">{feedbackReport.scores.technical}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-charcoal-600">Relevance to Job Description:</span>
                  <span className="font-bold text-charcoal-900">{feedbackReport.scores.relevance}%</span>
                </div>
              </div>

              <div className="pt-1">
                <Link to="/app/feedback" className="text-steel-600 hover:underline font-semibold block text-right">
                  Inspect full feedback breakdown →
                </Link>
              </div>
            </PanelBody>
          </Panel>

          {/* Past Sessions List */}
          <Panel>
            <PanelHeader title="Completed Practice Sessions" />
            <div className="divide-y divide-charcoal-100 text-xs">
              {interviewSessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => navigate('/app/feedback')}
                  className="p-3.5 hover:bg-canvas-50 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between font-semibold text-charcoal-900">
                    <span>{session.company} — {session.role}</span>
                    <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[10px]">
                      {session.status === 'completed' ? 'Score: 84%' : 'In progress'}
                    </span>
                  </div>
                  <p className="text-[11px] text-charcoal-600 mt-0.5">
                    {session.type} ({session.difficulty}) • 3 questions answered
                  </p>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
};
