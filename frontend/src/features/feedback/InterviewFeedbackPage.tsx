import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  AlertTriangle,
  Compass,
  RotateCcw
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, PanelHeader, Button } from '../../components/common/UIComponents';

export const InterviewFeedbackPage: React.FC = () => {
  const navigate = useNavigate();
  const { feedbackReport, addRoadmapTask } = useApp();

  const handleAddToRoadmap = (skillName: string, reason: string) => {
    addRoadmapTask({
      skillName,
      category: 'Backend',
      priority: 'High',
      estimatedHours: 6,
      reason,
      targetRoles: ['Backend Systems Engineer', 'Software Engineer'],
      resources: [
        { title: `${skillName} Practical Deep Dive`, type: 'Doc', link: 'https://docs.nexora.dev' }
      ]
    });
    alert(`Added "${skillName}" to your Skill Roadmap.`);
    navigate('/app/skill-roadmap');
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Structured Interview Feedback</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
              Rubric Assessment
            </span>
          </div>
          <p className="text-xs text-charcoal-600 mt-1">
            Session for <span className="font-semibold text-charcoal-800">{feedbackReport.company}</span> — {feedbackReport.role} ({feedbackReport.interviewType}) completed on {feedbackReport.completedDate}.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/app/interview-prep">
            <Button variant="outline" size="sm" icon={<RotateCcw className="w-3.5 h-3.5" />}>
              Start Another Practice
            </Button>
          </Link>

          <Link to="/app/skill-roadmap">
            <Button variant="primary" size="sm" icon={<Compass className="w-3.5 h-3.5" />}>
              Open Skill Roadmap
            </Button>
          </Link>
        </div>
      </div>

      {/* Score Summary Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
        <Panel className="p-4 bg-emerald-50/40 border-emerald-200">
          <span className="text-[11px] text-emerald-900 font-semibold block mb-1">Overall Assessment</span>
          <span className="text-3xl font-bold text-emerald-800">{feedbackReport.overallScore}%</span>
          <p className="text-[10px] text-emerald-900 mt-1">Ready for Round 2</p>
        </Panel>

        <Panel className="p-4">
          <span className="text-charcoal-600 text-[11px] block mb-1">Communication</span>
          <span className="text-2xl font-bold text-charcoal-900">{feedbackReport.scores.communication}%</span>
          <div className="w-full bg-charcoal-100 h-1.5 rounded-full mt-2 overflow-hidden">
            <div className="bg-steel-600 h-full rounded-full" style={{ width: `${feedbackReport.scores.communication}%` }}></div>
          </div>
        </Panel>

        <Panel className="p-4">
          <span className="text-charcoal-600 text-[11px] block mb-1">Technical Correctness</span>
          <span className="text-2xl font-bold text-charcoal-900">{feedbackReport.scores.technical}%</span>
          <div className="w-full bg-charcoal-100 h-1.5 rounded-full mt-2 overflow-hidden">
            <div className="bg-steel-600 h-full rounded-full" style={{ width: `${feedbackReport.scores.technical}%` }}></div>
          </div>
        </Panel>

        <Panel className="p-4">
          <span className="text-charcoal-600 text-[11px] block mb-1">Relevance</span>
          <span className="text-2xl font-bold text-charcoal-900">{feedbackReport.scores.relevance}%</span>
          <div className="w-full bg-charcoal-100 h-1.5 rounded-full mt-2 overflow-hidden">
            <div className="bg-steel-600 h-full rounded-full" style={{ width: `${feedbackReport.scores.relevance}%` }}></div>
          </div>
        </Panel>

        <Panel className="p-4">
          <span className="text-charcoal-600 text-[11px] block mb-1">Clarity & Cadence</span>
          <span className="text-2xl font-bold text-charcoal-900">{feedbackReport.scores.clarity}%</span>
          <div className="w-full bg-charcoal-100 h-1.5 rounded-full mt-2 overflow-hidden">
            <div className="bg-steel-600 h-full rounded-full" style={{ width: `${feedbackReport.scores.clarity}%` }}></div>
          </div>
        </Panel>
      </div>

      {/* Synthesis: Strengths & Growth Areas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Panel className="p-5 bg-white space-y-3">
          <div className="flex items-center gap-2 text-emerald-800 font-bold text-xs uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Demonstrated Strong Points</span>
          </div>
          <ul className="space-y-2 text-xs text-charcoal-700">
            {feedbackReport.strongPoints.map((pt, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span className="leading-relaxed">{pt}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel className="p-5 bg-white space-y-3">
          <div className="flex items-center gap-2 text-amber-900 font-bold text-xs uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>High-Impact Improvement Opportunities</span>
          </div>
          <ul className="space-y-2 text-xs text-charcoal-700">
            {feedbackReport.areasToImprove.map((pt, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-amber-600 font-bold">•</span>
                <span className="leading-relaxed">{pt}</span>
              </li>
            ))}
          </ul>

          <div className="pt-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleAddToRoadmap('Distributed Locks & Cache Stampede', 'Identified gap from Stripe practice feedback')}
              icon={<Compass className="w-3.5 h-3.5" />}
            >
              Add Identified Gaps to Skill Roadmap
            </Button>
          </div>
        </Panel>
      </div>

      {/* Question by Question Detailed Breakdown */}
      <Panel>
        <PanelHeader
          title="Question-by-Question Rubric Evaluation"
          subtitle="Specific critiques and optimal answer refinements"
        />
        <div className="divide-y divide-charcoal-100">
          {feedbackReport.questionFeedback.map((q, idx) => (
            <div key={q.questionId} className="p-5 space-y-3 text-xs">
              <div className="flex items-start justify-between gap-3">
                <h4 className="font-bold text-charcoal-900 text-sm">
                  {idx + 1}. {q.questionText}
                </h4>
                <span className="px-2 py-0.5 rounded font-bold text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 shrink-0">
                  {q.score} / 100
                </span>
              </div>

              {/* Student answer snippet */}
              <div className="p-3 bg-canvas-50 border border-charcoal-200 rounded text-charcoal-800">
                <span className="font-semibold text-charcoal-600 text-[11px] block mb-1">Your Answer:</span>
                <p className="leading-relaxed font-sans">{q.studentAnswer}</p>
              </div>

              {/* Critique & Recommendation */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div className="p-2.5 bg-white border border-charcoal-200 rounded">
                  <span className="font-semibold text-emerald-800 text-[11px] block mb-0.5">Evaluator Critique:</span>
                  <p className="text-charcoal-700 text-[11px] leading-relaxed">{q.critique}</p>
                </div>

                <div className="p-2.5 bg-blue-50/60 border border-blue-200 rounded">
                  <span className="font-semibold text-blue-900 text-[11px] block mb-0.5">Recommended Refinement:</span>
                  <p className="text-blue-950 text-[11px] leading-relaxed">{q.improvedApproach}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
};
