import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, FileText, Briefcase, GraduationCap, ArrowRight, ShieldCheck } from 'lucide-react';
import { Button } from '../../components/common/UIComponents';
import { useApp } from '../../context/appContextDef';

export const StepComplete: React.FC = () => {
  const navigate = useNavigate();
  const { profile, resumeDoc } = useApp();

  return (
    <div>
      <div className="text-center pb-6 border-b border-charcoal-100">
        <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center mb-3">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-charcoal-900">Your Placement Setup is Ready</h2>
        <p className="text-xs text-charcoal-600 mt-1 max-w-md mx-auto">
          We have indexed your verified skills and configured role matches for your target domains.
        </p>
      </div>

      <div className="py-6 space-y-4">
        {/* Profile Card */}
        <div className="p-4 rounded-md border border-charcoal-200 bg-canvas-50">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded bg-[#263747] text-white flex items-center justify-center shrink-0">
              <GraduationCap className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-charcoal-900">{profile.fullName}</h4>
              <p className="text-[11px] text-charcoal-600 mt-0.5">
                {profile.degree} in {profile.branch}
              </p>
              <p className="text-[11px] text-charcoal-600">
                {profile.college} • Class of {profile.graduationYear}
              </p>
            </div>
          </div>
        </div>

        {/* Resume Card */}
        <div className="p-4 rounded-md border border-charcoal-200 bg-white">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded bg-steel-100 text-steel-700 flex items-center justify-center shrink-0">
              <FileText className="w-4 h-4" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-charcoal-900">Resume Document</h4>
                <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-medium">
                  Parsed & Verified
                </span>
              </div>
              <p className="text-[11px] text-charcoal-600 mt-0.5">
                {resumeDoc.fileName} ({resumeDoc.fileSize})
              </p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {resumeDoc.extractedSkills.slice(0, 6).map(s => (
                  <span key={s.name} className="px-2 py-0.5 bg-canvas-100 border border-charcoal-200 rounded text-[10px] text-charcoal-700">
                    {s.name}
                  </span>
                ))}
                {resumeDoc.extractedSkills.length > 6 && (
                  <span className="px-1.5 py-0.5 text-[10px] text-charcoal-600">
                    +{resumeDoc.extractedSkills.length - 6} more
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Preferences Card */}
        <div className="p-4 rounded-md border border-charcoal-200 bg-white">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded bg-navy-800 text-white flex items-center justify-center shrink-0">
              <Briefcase className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-charcoal-900">Target Roles & Modes</h4>
              <p className="text-[11px] text-charcoal-600 mt-0.5">
                {profile.preferences.targetRoles.join(' • ')}
              </p>
              <p className="text-[11px] text-charcoal-600 mt-1">
                Preference: <span className="font-semibold text-charcoal-800">{profile.preferences.workMode}</span> • Hubs: {profile.preferences.preferredLocations.join(', ')}
              </p>
            </div>
          </div>
        </div>

        {/* Integrity note */}
        <div className="flex items-center gap-2 p-3 bg-steel-50 border border-steel-200 rounded text-[11px] text-steel-700">
          <ShieldCheck className="w-4 h-4 text-steel-600 shrink-0" />
          <span>All documents and applications will require your explicit confirmation before submission.</span>
        </div>
      </div>

      <div className="pt-4 border-t border-charcoal-100 flex justify-end">
        <Button
          type="button"
          variant="primary"
          size="lg"
          onClick={() => navigate('/app/dashboard')}
          icon={<ArrowRight className="w-4 h-4" />}
        >
          Go to My Dashboard
        </Button>
      </div>
    </div>
  );
};
