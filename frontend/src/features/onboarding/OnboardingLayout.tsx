import React from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { GraduationCap, Check } from 'lucide-react';
import { cn } from '../../lib/utils';

export const OnboardingLayout: React.FC = () => {
  const location = useLocation();

  const steps = [
    { id: 'profile', name: 'Academic Profile', path: '/onboarding/profile', number: 1 },
    { id: 'resume', name: 'Resume Upload', path: '/onboarding/resume', number: 2 },
    { id: 'preferences', name: 'Career Preferences', path: '/onboarding/preferences', number: 3 },
    { id: 'complete', name: 'Review & Finish', path: '/onboarding/complete', number: 4 },
  ];

  const getCurrentStepIndex = () => {
    const current = steps.findIndex(s => location.pathname.includes(s.id));
    return current >= 0 ? current : 0;
  };

  const currentIndex = getCurrentStepIndex();

  return (
    <div className="min-h-screen bg-[#F5F6F4] flex flex-col antialiased">
      {/* Top minimal header */}
      <header className="h-14 border-b border-charcoal-200 bg-white px-6 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-[#263747] text-white flex items-center justify-center font-bold text-xs">
            <GraduationCap className="w-4 h-4" />
          </div>
          <span className="font-bold text-sm tracking-tight text-[#263747]">NEXORA</span>
          <span className="text-xs text-charcoal-600 hidden sm:inline ml-2 pl-2 border-l border-charcoal-200">
            Student Setup Guide
          </span>
        </Link>

        <span className="text-xs text-charcoal-600 font-medium">
          Step {currentIndex + 1} of {steps.length}
        </span>
      </header>

      {/* Stepper indicator bar */}
      <div className="bg-white border-b border-charcoal-200 py-4 px-4 overflow-x-auto">
        <div className="max-w-2xl mx-auto flex items-center justify-between gap-2 min-w-[320px]">
          {steps.map((step, idx) => {
            const isCompleted = idx < currentIndex;
            const isCurrent = idx === currentIndex;

            return (
              <React.Fragment key={step.id}>
                <div className="flex items-center gap-2">
                  <div
                    className={cn(
                      "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-colors",
                      isCompleted
                        ? "bg-emerald-600 text-white"
                        : isCurrent
                        ? "bg-[#263747] text-white"
                        : "bg-charcoal-100 text-charcoal-600 border border-charcoal-300"
                    )}
                  >
                    {isCompleted ? <Check className="w-3.5 h-3.5" /> : step.number}
                  </div>
                  <span
                    className={cn(
                      "text-xs hidden md:inline font-medium whitespace-nowrap",
                      isCurrent ? "text-charcoal-900 font-semibold" : "text-charcoal-600"
                    )}
                  >
                    {step.name}
                  </span>
                </div>
                {idx < steps.length - 1 && (
                  <div
                    className={cn(
                      "flex-1 h-0.5 mx-2 rounded",
                      idx < currentIndex ? "bg-emerald-500" : "bg-charcoal-200"
                    )}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Onboarding form card content */}
      <main className="flex-1 max-w-2xl w-full mx-auto p-4 md:p-6 lg:p-8 flex flex-col justify-center">
        <div className="bg-white border border-charcoal-200 rounded-lg shadow-card p-6 md:p-8 animate-in fade-in duration-200">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
