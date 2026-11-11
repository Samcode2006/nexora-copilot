import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Clock,
  ArrowRight,
  ArrowLeft,
  HelpCircle,
  StopCircle
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, Button } from '../../components/common/UIComponents';

export const InterviewSessionPage: React.FC = () => {
  const navigate = useNavigate();
  const { activeSession, interviewSessions, submitAnswer, completeSession } = useApp();

  const session = activeSession || interviewSessions[0];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState(() => session?.questions[0]?.studentAnswer || '');
  const [showFramework, setShowFramework] = useState(false);
  const [secondsElapsed, setSecondsElapsed] = useState(0);

  // Timer counter
  useEffect(() => {
    const interval = setInterval(() => {
      setSecondsElapsed(prev => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const currentQuestion = session?.questions[currentIndex];

  if (!session || !currentQuestion) {
    return (
      <div className="text-center py-12">
        <h3 className="font-bold text-charcoal-900 text-sm">Session Not Found</h3>
        <p className="text-xs text-charcoal-600 mt-1 mb-4">Please launch a new session from Interview Prep.</p>
        <Button variant="outline" size="sm" onClick={() => navigate('/app/interview-prep')}>
          Back to Interview Prep
        </Button>
      </div>
    );
  }

  const formatTimer = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleNext = () => {
    submitAnswer(session.id, currentIndex, currentAnswer);
    if (currentIndex < session.questions.length - 1) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      setCurrentAnswer(session.questions[nextIndex]?.studentAnswer || '');
      setShowFramework(false);
    } else {
      // Complete session
      completeSession(session.id);
      navigate('/app/feedback');
    }
  };

  const handlePrev = () => {
    submitAnswer(session.id, currentIndex, currentAnswer);
    if (currentIndex > 0) {
      const prevIndex = currentIndex - 1;
      setCurrentIndex(prevIndex);
      setCurrentAnswer(session.questions[prevIndex]?.studentAnswer || '');
      setShowFramework(false);
    }
  };

  const handleFinishEarly = () => {
    submitAnswer(session.id, currentIndex, currentAnswer);
    completeSession(session.id);
    navigate('/app/feedback');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Session Top Bar */}
      <div className="bg-[#263747] text-white rounded-lg p-4 px-6 flex items-center justify-between shadow-card">
        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
            Practice Simulation • {session.company} ({session.type})
          </span>
          <h2 className="text-sm md:text-base font-bold tracking-tight text-white mt-0.5">
            Question {currentIndex + 1} of {session.questions.length}
          </h2>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 px-3 py-1 bg-[#1B2834] rounded font-mono text-xs text-slate-300 border border-[#32475B]">
            <Clock className="w-3.5 h-3.5 text-steel-400" />
            <span>{formatTimer(secondsElapsed)}</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleFinishEarly}
            className="text-slate-300 hover:text-white hover:bg-[#32475B]"
            icon={<StopCircle className="w-4 h-4 text-red-400" />}
          >
            End & Evaluate
          </Button>
        </div>
      </div>

      {/* Progress Pill Bar */}
      <div className="flex gap-2">
        {session.questions.map((q, idx) => (
          <div
            key={q.id}
            className={`h-1.5 flex-1 rounded-full transition-colors ${
              idx === currentIndex
                ? 'bg-steel-600'
                : idx < currentIndex
                ? 'bg-emerald-600'
                : 'bg-charcoal-200'
            }`}
          />
        ))}
      </div>

      {/* Question Card */}
      <Panel className="p-6 bg-white space-y-5">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-steel-100 text-steel-800 border border-steel-200">
              {currentQuestion.category}
            </span>
            <span className="text-xs text-charcoal-600">
              {session.difficulty} Level
            </span>
          </div>

          <h3 className="text-base md:text-lg font-bold text-charcoal-900 leading-snug">
            {currentQuestion.question}
          </h3>

          <div className="p-3 bg-canvas-50 border border-charcoal-200 rounded text-xs text-charcoal-700">
            <span className="font-semibold text-charcoal-900">Why interviewers ask this:</span>{' '}
            {currentQuestion.contextWhyAsked}
          </div>
        </div>

        {/* Framework & Hint Toggle */}
        <div>
          <button
            onClick={() => setShowFramework(!showFramework)}
            className="text-xs font-semibold text-steel-600 hover:text-steel-700 flex items-center gap-1.5"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>{showFramework ? 'Hide Recommended Framework' : 'Show Recommended Answer Framework / Hint'}</span>
          </button>

          {showFramework && (
            <div className="mt-2.5 p-3.5 bg-blue-50/70 border border-blue-200 rounded text-xs text-blue-950 space-y-1.5 animate-in fade-in duration-150">
              <span className="font-bold block">Structuring Strategy:</span>
              <p className="leading-relaxed">{currentQuestion.sampleFramework}</p>
              <p className="text-[11px] text-blue-800 font-medium pt-1">
                Hint: {currentQuestion.hint}
              </p>
            </div>
          )}
        </div>

        {/* Answer Editor */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <label className="font-semibold text-charcoal-800">Your Structured Answer</label>
            <span className="text-charcoal-600">
              {currentAnswer.trim().split(/\s+/).filter(Boolean).length} words
            </span>
          </div>

          <textarea
            rows={8}
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            placeholder="Type your structured explanation here (or talk through the problem and capture key bullet points)..."
            className="w-full bg-white border border-charcoal-200 rounded-md p-3 text-xs text-charcoal-900 leading-relaxed font-sans focus:outline-none focus:border-steel-500 focus:ring-1 focus:ring-steel-500"
          />
        </div>

        {/* Navigation Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-charcoal-100">
          <Button
            variant="outline"
            size="md"
            disabled={currentIndex === 0}
            onClick={handlePrev}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            Previous Question
          </Button>

          <Button
            variant="primary"
            size="md"
            onClick={handleNext}
            icon={<ArrowRight className="w-4 h-4" />}
          >
            {currentIndex === session.questions.length - 1 ? 'Complete Session & View Feedback' : 'Next Question'}
          </Button>
        </div>
      </Panel>
    </div>
  );
};
