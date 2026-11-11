import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Trash2, ArrowRight, ArrowLeft } from 'lucide-react';
import { Button } from '../../components/common/UIComponents';
import { useApp } from '../../context/appContextDef';

export const StepResume: React.FC = () => {
  const navigate = useNavigate();
  const { resumeDoc, uploadResume, verifySkill } = useApp();

  const [fileName, setFileName] = useState(resumeDoc.fileName || 'Aarav_Sharma_Resume_2026.pdf');
  const [fileSize, setFileSize] = useState(resumeDoc.fileSize || '242 KB');
  const [uploading, setUploading] = useState(false);
  const [analyzed, setAnalyzed] = useState(true);
  const [skills, setSkills] = useState(resumeDoc.extractedSkills);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      alert('File size exceeds 5MB limit. Please select a smaller PDF or DOCX file.');
      return;
    }

    setUploading(true);
    setFileName(file.name);
    setFileSize(`${(file.size / 1024).toFixed(0)} KB`);

    setTimeout(() => {
      setUploading(false);
      setAnalyzed(true);
      uploadResume({ name: file.name, size: `${(file.size / 1024).toFixed(0)} KB` });
    }, 800);
  };

  const toggleSkillConfirmed = (skillName: string) => {
    setSkills(prev => prev.map(s => 
      s.name === skillName ? { ...s, confirmed: !s.confirmed } : s
    ));
    verifySkill(skillName);
  };

  const handleNext = () => {
    navigate('/onboarding/preferences');
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-bold text-charcoal-900">Upload Your Resume</h2>
        <p className="text-xs text-charcoal-600 mt-1">
          Nexora will extract your project experience and technical skills. You have full control to confirm or correct what was extracted.
        </p>
      </div>

      {/* Upload Dropzone */}
      <div className="border-2 border-dashed border-charcoal-200 rounded-lg p-6 text-center hover:border-steel-400 transition-colors bg-canvas-50">
        <UploadCloud className="w-8 h-8 text-steel-600 mx-auto mb-2" />
        <p className="text-xs font-semibold text-charcoal-800">
          Click to upload or drag & drop your resume
        </p>
        <p className="text-[11px] text-charcoal-600 mt-0.5">
          PDF or DOCX format (Max 5MB)
        </p>
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          className="hidden"
          id="resume-file-input"
        />
        <label
          htmlFor="resume-file-input"
          className="mt-3 inline-block px-3 py-1.5 bg-white border border-charcoal-200 rounded text-xs font-medium text-charcoal-800 hover:bg-canvas-100 cursor-pointer shadow-subtle"
        >
          Select File
        </label>
      </div>

      {/* Active File State */}
      {uploading && (
        <div className="mt-4 p-4 border border-charcoal-200 rounded bg-white text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-semibold text-charcoal-900">Parsing document structure...</span>
            <span className="text-steel-600 font-mono">Analyzing</span>
          </div>
          <div className="w-full h-1.5 bg-charcoal-100 rounded-full overflow-hidden">
            <div className="h-full bg-steel-600 animate-pulse w-3/4"></div>
          </div>
        </div>
      )}

      {analyzed && !uploading && (
        <div className="mt-4 space-y-4">
          {/* File Card */}
          <div className="flex items-center justify-between p-3 border border-charcoal-200 rounded-md bg-white">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-steel-100 text-steel-700 flex items-center justify-center">
                <FileText className="w-4 h-4" />
              </div>
              <div>
                <p className="font-semibold text-xs text-charcoal-900">{fileName}</p>
                <p className="text-[11px] text-charcoal-600">{fileSize} • Uploaded and parsed</p>
              </div>
            </div>
            <button
              onClick={() => {
                setFileName('');
                setAnalyzed(false);
              }}
              className="text-charcoal-600 hover:text-red-600 p-1 rounded"
              title="Remove file"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

          {/* Verification Section */}
          <div className="p-4 border border-charcoal-200 rounded-md bg-white">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold text-charcoal-900">
                Extracted Skills (Click to confirm accuracy)
              </h4>
              <span className="text-[10px] text-charcoal-600">
                {skills.filter(s => s.confirmed).length} of {skills.length} confirmed
              </span>
            </div>
            <p className="text-[11px] text-charcoal-600 mb-3">
              We never assume unverified skills are production-ready. Click each pill to confirm your confidence:
            </p>

            <div className="flex flex-wrap gap-2">
              {skills.map((s) => (
                <button
                  type="button"
                  key={s.name}
                  onClick={() => toggleSkillConfirmed(s.name)}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs transition-colors border ${
                    s.confirmed
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-300 font-medium'
                      : 'bg-canvas-100 text-charcoal-600 border-charcoal-200 line-through opacity-70'
                  }`}
                >
                  {s.confirmed ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <AlertCircle className="w-3.5 h-3.5" />}
                  <span>{s.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="pt-6 flex items-center justify-between border-t border-charcoal-100 mt-6">
        <Button
          type="button"
          variant="outline"
          onClick={() => navigate('/onboarding/profile')}
          icon={<ArrowLeft className="w-4 h-4" />}
        >
          Back
        </Button>

        <Button
          type="button"
          variant="primary"
          onClick={handleNext}
          icon={<ArrowRight className="w-4 h-4" />}
        >
          Next: Career Preferences
        </Button>
      </div>
    </div>
  );
};
