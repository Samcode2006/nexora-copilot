import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Download,
  RefreshCw
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, PanelHeader, PanelBody, Button } from '../../components/common/UIComponents';

export const ResumeManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const { resumeDoc, uploadResume, verifySkill, profile } = useApp();

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    uploadResume({
      name: file.name,
      size: `${(file.size / 1024).toFixed(0)} KB`
    });
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Resume Management</h2>
          <p className="text-xs text-charcoal-600 mt-0.5">
            Manage your verified primary master resume, inspect parsed entities, and launch job-specific tailoring.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/app/resume-studio">
            <Button variant="primary" size="sm" icon={<ArrowRight className="w-4 h-4" />}>
              Open Resume Studio
            </Button>
          </Link>
        </div>
      </div>

      {/* Primary Resume Metadata Card */}
      <Panel>
        <div className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-charcoal-100">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-steel-100 text-steel-700 flex items-center justify-center shrink-0">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-sm text-charcoal-900">{resumeDoc.fileName}</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                  Primary Master Resume
                </span>
              </div>
              <p className="text-xs text-charcoal-600 mt-1">
                Size: {resumeDoc.fileSize} • Uploaded on {new Date(resumeDoc.uploadedAt).toLocaleDateString()} • Last parsed {new Date(resumeDoc.lastParsedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <input
              type="file"
              accept=".pdf,.docx"
              id="replace-resume-input"
              className="hidden"
              onChange={handleFileUpload}
            />
            <label
              htmlFor="replace-resume-input"
              className="px-3 py-1.5 bg-white border border-charcoal-200 hover:bg-canvas-100 text-xs font-medium text-charcoal-800 rounded cursor-pointer transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Replace Resume</span>
            </label>

            <button
              onClick={() => alert(`Simulated downloading ${resumeDoc.fileName}`)}
              className="px-3 py-1.5 bg-canvas-100 border border-charcoal-200 hover:bg-canvas-200 text-xs font-medium text-charcoal-800 rounded transition-colors flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download</span>
            </button>
          </div>
        </div>

        {/* Areas needing attention */}
        {resumeDoc.attentionItems && resumeDoc.attentionItems.length > 0 && (
          <div className="p-4 bg-amber-50/60 border-b border-amber-200 text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-amber-900 mb-1">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Items needing student verification</span>
            </div>
            <ul className="space-y-1 pl-6 list-disc text-[11px] text-amber-800">
              {resumeDoc.attentionItems.map(item => (
                <li key={item.id}>{item.message}</li>
              ))}
            </ul>
          </div>
        )}
      </Panel>

      {/* Grid: Extracted Entities & Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Extracted Skills with status breakdown */}
        <div className="lg:col-span-2 space-y-6">
          <Panel>
            <PanelHeader
              title="Parsed Skills & Verification Status"
              subtitle="Skills marked confirmed are used in automated job matching calculations"
            />
            <PanelBody className="space-y-4">
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-emerald-800 font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-600"></span> Confirmed ({resumeDoc.extractedSkills.filter(s => s.confirmed).length})
                </span>
                <span className="flex items-center gap-1.5 text-amber-800 font-medium">
                  <span className="w-2 h-2 rounded-full bg-amber-500"></span> Needs confirmation ({resumeDoc.extractedSkills.filter(s => !s.confirmed).length})
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {resumeDoc.extractedSkills.map(skill => (
                  <div
                    key={skill.name}
                    className="p-2.5 border border-charcoal-200 rounded flex items-center justify-between bg-white text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-charcoal-900">{skill.name}</span>
                      {skill.confirmed ? (
                        <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded font-medium">Confirmed</span>
                      ) : (
                        <span className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded font-medium">Unverified</span>
                      )}
                    </div>
                    {!skill.confirmed && (
                      <button
                        onClick={() => verifySkill(skill.name)}
                        className="text-[11px] text-steel-600 hover:text-steel-700 font-semibold"
                      >
                        Confirm
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </PanelBody>
          </Panel>

          {/* Master Resume Content Sections */}
          <Panel>
            <PanelHeader title="Master Resume Structure" subtitle="Extracted from document" />
            <div className="divide-y divide-charcoal-100 text-xs">
              <div className="p-4">
                <h4 className="font-bold text-charcoal-900 mb-1">Professional Summary</h4>
                <p className="text-charcoal-700 leading-relaxed bg-canvas-50 p-3 rounded border border-charcoal-200">
                  {profile.bio}
                </p>
              </div>

              <div className="p-4">
                <h4 className="font-bold text-charcoal-900 mb-2">Projects in Master Resume ({profile.projects.length})</h4>
                <div className="space-y-2">
                  {profile.projects.map(p => (
                    <div key={p.id} className="p-2.5 border border-charcoal-200 rounded bg-white">
                      <div className="flex justify-between font-semibold text-charcoal-900">
                        <span>{p.title}</span>
                        <span className="text-charcoal-600 text-[11px]">{p.role}</span>
                      </div>
                      <p className="text-charcoal-600 text-[11px] mt-0.5">{p.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4">
                <h4 className="font-bold text-charcoal-900 mb-2">Experience Entries ({profile.experience.length})</h4>
                {profile.experience.map(e => (
                  <div key={e.id} className="p-2.5 border border-charcoal-200 rounded bg-white">
                    <div className="flex justify-between font-semibold text-charcoal-900">
                      <span>{e.role} — {e.company}</span>
                      <span className="text-charcoal-600 text-[11px]">{e.startDate} – {e.endDate}</span>
                    </div>
                    <p className="text-charcoal-600 text-[11px] mt-0.5">{e.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </Panel>
        </div>

        {/* Right Col: Resume Studio Action & Integrity Guidelines */}
        <div className="space-y-6">
          <Panel className="border-steel-300 bg-steel-50/50">
            <PanelHeader title="Job-Specific Tailoring" />
            <PanelBody className="space-y-3 text-xs">
              <p className="text-charcoal-700 leading-relaxed">
                When you apply to specific roles, do not edit your master resume directly. Instead, use <strong>Resume Studio</strong> to highlight relevant experiences for that specific job posting.
              </p>
              <Button
                variant="primary"
                size="md"
                className="w-full"
                onClick={() => navigate('/app/resume-studio')}
                icon={<ArrowRight className="w-4 h-4" />}
              >
                Open Resume Studio
              </Button>
            </PanelBody>
          </Panel>

          <Panel>
            <PanelHeader title="Resume Integrity Policy" />
            <PanelBody className="space-y-3 text-xs text-charcoal-700">
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <p>
                  <strong>No fabricated claims:</strong> Nexora will only emphasize projects and skills you have verified.
                </p>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-steel-600 shrink-0 mt-0.5" />
                <p>
                  <strong>Explicit Approval:</strong> Tailored resumes are placed in the Approval Centre for your review before you apply.
                </p>
              </div>
            </PanelBody>
          </Panel>
        </div>
      </div>
    </div>
  );
};
