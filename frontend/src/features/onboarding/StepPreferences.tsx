import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ArrowLeft, Check } from 'lucide-react';
import { Button } from '../../components/common/UIComponents';
import { useApp } from '../../context/appContextDef';

export const StepPreferences: React.FC = () => {
  const navigate = useNavigate();
  const { profile, updateProfile } = useApp();

  const [targetRoles, setTargetRoles] = useState<string[]>(
    profile.preferences?.targetRoles || ['Software Engineer Intern', 'Frontend Engineer', 'Full Stack Developer']
  );
  const [preferredDomains, setPreferredDomains] = useState<string[]>(
    profile.preferences?.preferredDomains || ['Cloud Infrastructure', 'Developer Tools', 'Fintech']
  );
  const [preferredLocations, setPreferredLocations] = useState<string[]>(
    profile.preferences?.preferredLocations || ['Bangalore', 'Remote', 'Chennai']
  );
  const [employmentType, setEmploymentType] = useState<'Internship' | 'Full-time' | 'Both'>(
    profile.preferences?.employmentType || 'Both'
  );
  const [workMode, setWorkMode] = useState<'Remote' | 'Hybrid' | 'On-site' | 'Any'>(
    profile.preferences?.workMode || 'Hybrid'
  );
  const [minStipendSalary] = useState(
    profile.preferences?.minStipendSalary || '₹45,000 / month'
  );

  const availableRoles = [
    'Software Engineer Intern',
    'Frontend Engineer',
    'Full Stack Developer',
    'Backend Systems Engineer',
    'Platform Infrastructure Intern',
    'DevOps & Site Reliability'
  ];

  const availableDomains = [
    'Developer Tools',
    'Cloud Infrastructure',
    'Fintech & Payments',
    'Enterprise SaaS',
    'Consumer Internet',
    'AI/ML Systems'
  ];

  const availableLocations = ['Bangalore', 'Hyderabad', 'Chennai', 'Pune', 'NCR / Delhi', 'Remote'];

  const toggleItem = (list: string[], setList: React.Dispatch<React.SetStateAction<string[]>>, item: string) => {
    if (list.includes(item)) {
      setList(list.filter(i => i !== item));
    } else {
      setList([...list, item]);
    }
  };

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({
      preferences: {
        ...profile.preferences,
        targetRoles,
        preferredDomains,
        preferredLocations,
        employmentType,
        workMode,
        minStipendSalary
      }
    });
    navigate('/onboarding/complete');
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-bold text-charcoal-900">Career Preferences</h2>
        <p className="text-xs text-charcoal-600 mt-1">
          Define what opportunities you are targeting so our matching engine can calculate precise fit scores.
        </p>
      </div>

      <form onSubmit={handleNext} className="space-y-5">
        {/* Target Roles */}
        <div>
          <label className="block text-xs font-semibold text-charcoal-800 mb-1.5">
            Target Roles (Select all that apply)
          </label>
          <div className="flex flex-wrap gap-2">
            {availableRoles.map(role => {
              const selected = targetRoles.includes(role);
              return (
                <button
                  type="button"
                  key={role}
                  onClick={() => toggleItem(targetRoles, setTargetRoles, role)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors flex items-center gap-1.5 ${
                    selected
                      ? 'bg-navy-800 text-white border-navy-900'
                      : 'bg-white text-charcoal-700 border-charcoal-200 hover:bg-canvas-100'
                  }`}
                >
                  {selected && <Check className="w-3.5 h-3.5" />}
                  <span>{role}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Preferred Domains */}
        <div>
          <label className="block text-xs font-semibold text-charcoal-800 mb-1.5">
            Preferred Domains
          </label>
          <div className="flex flex-wrap gap-2">
            {availableDomains.map(domain => {
              const selected = preferredDomains.includes(domain);
              return (
                <button
                  type="button"
                  key={domain}
                  onClick={() => toggleItem(preferredDomains, setPreferredDomains, domain)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors flex items-center gap-1.5 ${
                    selected
                      ? 'bg-steel-600 text-white border-steel-700'
                      : 'bg-white text-charcoal-700 border-charcoal-200 hover:bg-canvas-100'
                  }`}
                >
                  {selected && <Check className="w-3.5 h-3.5" />}
                  <span>{domain}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Opportunity Type & Work Mode */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-charcoal-800 mb-1.5">
              Opportunity Type
            </label>
            <select
              value={employmentType}
              onChange={(e) => setEmploymentType(e.target.value as 'Internship' | 'Full-time' | 'Both')}
              className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
            >
              <option value="Both">Both Internships & Full-time</option>
              <option value="Internship">Internship Only</option>
              <option value="Full-time">Full-time Only</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-charcoal-800 mb-1.5">
              Work Mode Preference
            </label>
            <select
              value={workMode}
              onChange={(e) => setWorkMode(e.target.value as 'Remote' | 'Hybrid' | 'On-site' | 'Any')}
              className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
            >
              <option value="Hybrid">Hybrid</option>
              <option value="Remote">Remote</option>
              <option value="On-site">On-site</option>
              <option value="Any">Any Work Mode</option>
            </select>
          </div>
        </div>

        {/* Preferred Locations */}
        <div>
          <label className="block text-xs font-semibold text-charcoal-800 mb-1.5">
            Preferred Geographic Hubs
          </label>
          <div className="flex flex-wrap gap-2">
            {availableLocations.map(loc => {
              const selected = preferredLocations.includes(loc);
              return (
                <button
                  type="button"
                  key={loc}
                  onClick={() => toggleItem(preferredLocations, setPreferredLocations, loc)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors flex items-center gap-1.5 ${
                    selected
                      ? 'bg-charcoal-800 text-white border-charcoal-900'
                      : 'bg-white text-charcoal-700 border-charcoal-200 hover:bg-canvas-100'
                  }`}
                >
                  {selected && <Check className="w-3.5 h-3.5" />}
                  <span>{loc}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="pt-6 flex items-center justify-between border-t border-charcoal-100">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/onboarding/resume')}
            icon={<ArrowLeft className="w-4 h-4" />}
          >
            Back
          </Button>

          <Button
            type="submit"
            variant="primary"
            icon={<ArrowRight className="w-4 h-4" />}
          >
            Review & Complete
          </Button>
        </div>
      </form>
    </div>
  );
};
