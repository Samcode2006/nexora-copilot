import React, { useState } from 'react';
import {
  Save,
  CheckCircle2,
  Plus,
  Trash2
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, PanelHeader, PanelBody, Button } from '../../components/common/UIComponents';
import type { SkillItem, ProjectItem, ExperienceItem } from '../../types';

export const ProfilePage: React.FC = () => {
  const {
    profile,
    updateProfile,
    backendProfile,
    backendProfileLoading,
    backendProfileError,
    refreshBackendProfile,
  } = useApp();

  const [activeTab, setActiveTab] = useState<'personal' | 'academic' | 'skills' | 'projects' | 'experience' | 'preferences'>('personal');
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form states initialized with current profile
  const [fullName, setFullName] = useState(profile.fullName);
  const [email, setEmail] = useState(profile.email);
  const [phone, setPhone] = useState(profile.phone);
  const [location, setLocation] = useState(profile.location);
  const [bio, setBio] = useState(profile.bio);

  const [college, setCollege] = useState(profile.college);
  const [degree, setDegree] = useState(profile.degree);
  const [branch, setBranch] = useState(profile.branch);
  const [graduationYear] = useState(profile.graduationYear);
  const [currentYear, setCurrentYear] = useState(profile.currentYear);

  const [github, setGithub] = useState(profile.links.github);
  const [linkedin, setLinkedin] = useState(profile.links.linkedin);
  const [portfolio, setPortfolio] = useState(profile.links.portfolio);

  const [skills, setSkills] = useState<SkillItem[]>(profile.skills);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState<'frontend' | 'backend' | 'data' | 'tools' | 'core'>('frontend');
  const [newSkillLevel, setNewSkillLevel] = useState<'Beginner' | 'Intermediate' | 'Advanced'>('Intermediate');

  const [projects] = useState<ProjectItem[]>(profile.projects);
  const [experience] = useState<ExperienceItem[]>(profile.experience);

  const handleSave = () => {
    updateProfile({
      fullName,
      email,
      phone,
      location,
      bio,
      college,
      degree,
      branch,
      graduationYear,
      currentYear,
      links: {
        github,
        linkedin,
        portfolio
      },
      skills,
      projects,
      experience
    });

    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2500);
  };

  const addSkill = () => {
    if (!newSkillName.trim()) return;
    const newSkill: SkillItem = {
      id: `sk-${Date.now()}`,
      name: newSkillName.trim(),
      category: newSkillCategory,
      level: newSkillLevel,
      verified: true
    };
    setSkills([...skills, newSkill]);
    setNewSkillName('');
  };

  const removeSkill = (id: string) => {
    setSkills(skills.filter(s => s.id !== id));
  };

  return (
    <div className="space-y-6">
      {/* Profile Header Card */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-navy-800 text-white font-bold text-xl flex items-center justify-center shadow-xs">
            {profile.fullName.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-charcoal-900">{profile.fullName}</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                {profile.completeness}% Complete
              </span>
            </div>
            <p className="text-xs text-charcoal-600 mt-0.5">
              {profile.degree} in {profile.branch} • {profile.college}
            </p>
            <p className="text-[11px] text-charcoal-600 mt-1">
              Graduating {profile.graduationYear} • Looking for {profile.preferences.targetRoles.join(' / ')}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          {saveSuccess && (
            <span className="text-xs text-emerald-700 font-medium flex items-center gap-1 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Changes saved
            </span>
          )}
          <Button variant="primary" size="sm" onClick={handleSave} icon={<Save className="w-4 h-4" />}>
            Save Profile Changes
          </Button>
        </div>
      </div>

      {/* Tabs navigation */}
      <div className="border-b border-charcoal-200 flex items-center gap-2 overflow-x-auto text-xs font-medium">
        <button
          onClick={() => setActiveTab('personal')}
          className={`pb-2.5 px-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'personal'
              ? 'border-navy-800 text-navy-900 font-semibold'
              : 'border-transparent text-charcoal-600 hover:text-charcoal-900'
          }`}
        >
          Personal & Bio
        </button>
        <button
          onClick={() => setActiveTab('academic')}
          className={`pb-2.5 px-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'academic'
              ? 'border-navy-800 text-navy-900 font-semibold'
              : 'border-transparent text-charcoal-600 hover:text-charcoal-900'
          }`}
        >
          Academic Details
        </button>
        <button
          onClick={() => setActiveTab('skills')}
          className={`pb-2.5 px-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'skills'
              ? 'border-navy-800 text-navy-900 font-semibold'
              : 'border-transparent text-charcoal-600 hover:text-charcoal-900'
          }`}
        >
          Skills ({skills.length})
        </button>
        <button
          onClick={() => setActiveTab('projects')}
          className={`pb-2.5 px-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'projects'
              ? 'border-navy-800 text-navy-900 font-semibold'
              : 'border-transparent text-charcoal-600 hover:text-charcoal-900'
          }`}
        >
          Projects ({projects.length})
        </button>
        <button
          onClick={() => setActiveTab('experience')}
          className={`pb-2.5 px-3 border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'experience'
              ? 'border-navy-800 text-navy-900 font-semibold'
              : 'border-transparent text-charcoal-600 hover:text-charcoal-900'
          }`}
        >
          Experience ({experience.length})
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'personal' && (
        <Panel>
          <PanelHeader title="Personal Information & Online Presence" />
          <PanelBody className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-charcoal-700 mb-1">Full Legal Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal-700 mb-1">Primary Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal-700 mb-1">Phone Number</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal-700 mb-1">Target Locations</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-charcoal-700 mb-1">Professional Bio / Summary</label>
              <textarea
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
              />
            </div>

            <div className="pt-2 border-t border-charcoal-100">
              <h4 className="text-xs font-bold text-charcoal-900 mb-3">Portfolio & Code Profiles</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] text-charcoal-600 mb-1">GitHub Profile</label>
                  <input
                    type="text"
                    value={github}
                    onChange={(e) => setGithub(e.target.value)}
                    className="w-full bg-white border border-charcoal-200 rounded-md py-1.5 px-3 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-charcoal-600 mb-1">LinkedIn Profile</label>
                  <input
                    type="text"
                    value={linkedin}
                    onChange={(e) => setLinkedin(e.target.value)}
                    className="w-full bg-white border border-charcoal-200 rounded-md py-1.5 px-3 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-charcoal-600 mb-1">Personal Portfolio / Website</label>
                  <input
                    type="text"
                    value={portfolio}
                    onChange={(e) => setPortfolio(e.target.value)}
                    className="w-full bg-white border border-charcoal-200 rounded-md py-1.5 px-3 text-xs"
                  />
                </div>
              </div>
            </div>
            <div className="pt-2 border-t border-charcoal-100">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div>
                  <h4 className="text-xs font-bold text-charcoal-900">FastAPI Account Sync</h4>
                  <p className="text-[11px] text-charcoal-600">
                    Fetches your verified student record from <code className="font-mono">/api/v1/profile/me</code> using your Supabase Bearer token.
                  </p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={refreshBackendProfile}
                  disabled={backendProfileLoading}
                >
                  {backendProfileLoading ? 'Loading…' : 'Load my profile (FastAPI)'}
                </Button>
              </div>
              {backendProfileError && (
                <div className="p-2.5 bg-red-50 border border-red-200 rounded text-[11px] text-red-700">
                  {backendProfileError}
                </div>
              )}
              {backendProfile && (
                <pre className="p-3 bg-canvas-50 border border-charcoal-200 rounded text-[11px] text-charcoal-800 overflow-x-auto">
                  {JSON.stringify(backendProfile, null, 2)}
                </pre>
              )}
            </div>
          </PanelBody>
        </Panel>
      )}

      {activeTab === 'academic' && (
        <Panel>
          <PanelHeader title="Academic Standing & Degree Information" />
          <PanelBody className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-charcoal-700 mb-1">University / Institute</label>
                <input
                  type="text"
                  value={college}
                  onChange={(e) => setCollege(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal-700 mb-1">Degree</label>
                <input
                  type="text"
                  value={degree}
                  onChange={(e) => setDegree(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal-700 mb-1">Branch / Major</label>
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-charcoal-700 mb-1">Current Standing</label>
                <input
                  type="text"
                  value={currentYear}
                  onChange={(e) => setCurrentYear(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900"
                />
              </div>
            </div>

            <div className="p-4 bg-canvas-50 border border-charcoal-200 rounded-md">
              <h4 className="text-xs font-bold text-charcoal-900 mb-1">Verified Academic History</h4>
              {profile.education.map((edu) => (
                <div key={edu.id} className="text-xs text-charcoal-700 mt-2">
                  <div className="flex items-center justify-between font-semibold">
                    <span>{edu.degree}</span>
                    <span className="text-emerald-700">{edu.grade}</span>
                  </div>
                  <p className="text-[11px] text-charcoal-600">{edu.institution} ({edu.startYear} - {edu.endYear})</p>
                </div>
              ))}
            </div>
          </PanelBody>
        </Panel>
      )}

      {activeTab === 'skills' && (
        <Panel>
          <PanelHeader
            title="Confirmed Technical Skills"
            subtitle="Skills are evaluated during job matching and highlighted in resume drafts."
          />
          <PanelBody className="space-y-5">
            {/* Add skill row */}
            <div className="p-3 bg-canvas-50 border border-charcoal-200 rounded-md flex flex-wrap items-center gap-2">
              <input
                type="text"
                placeholder="Skill name (e.g. Apache Kafka)"
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                className="bg-white border border-charcoal-200 rounded px-2.5 py-1.5 text-xs text-charcoal-900 flex-1 min-w-[160px]"
              />
              <select
                value={newSkillCategory}
                onChange={(e) => setNewSkillCategory(e.target.value as SkillItem['category'])}
                className="bg-white border border-charcoal-200 rounded px-2.5 py-1.5 text-xs text-charcoal-900"
              >
                <option value="frontend">Frontend</option>
                <option value="backend">Backend</option>
                <option value="data">Data / Storage</option>
                <option value="tools">DevOps & Tools</option>
                <option value="core">Core CS</option>
              </select>
              <select
                value={newSkillLevel}
                onChange={(e) => setNewSkillLevel(e.target.value as SkillItem['level'])}
                className="bg-white border border-charcoal-200 rounded px-2.5 py-1.5 text-xs text-charcoal-900"
              >
                <option value="Beginner">Beginner</option>
                <option value="Intermediate">Intermediate</option>
                <option value="Advanced">Advanced</option>
              </select>
              <Button variant="secondary" size="sm" onClick={addSkill} icon={<Plus className="w-3.5 h-3.5" />}>
                Add Skill
              </Button>
            </div>

            {/* Current skill items */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
              {skills.map((s) => (
                <div
                  key={s.id}
                  className="p-2.5 border border-charcoal-200 rounded-md flex items-center justify-between bg-white text-xs"
                >
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-charcoal-900">{s.name}</span>
                      {s.verified && (
                        <span title="Verified in resume">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-charcoal-600 capitalize">{s.category} • {s.level}</span>
                  </div>
                  <button
                    onClick={() => removeSkill(s.id)}
                    className="text-charcoal-600 hover:text-red-600 p-1 rounded"
                    title="Remove skill"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </PanelBody>
        </Panel>
      )}

      {activeTab === 'projects' && (
        <Panel>
          <PanelHeader title="Projects & Technical Demonstrations" />
          <PanelBody className="space-y-4">
            {projects.map((proj) => (
              <div key={proj.id} className="p-4 border border-charcoal-200 rounded-md bg-canvas-50 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-xs text-charcoal-900">{proj.title}</h4>
                  <span className="text-[10px] px-2 py-0.5 bg-steel-100 text-steel-700 rounded font-medium">
                    {proj.role}
                  </span>
                </div>
                <p className="text-xs text-charcoal-600">{proj.description}</p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {proj.technologies.map(t => (
                    <span key={t} className="px-2 py-0.5 bg-white border border-charcoal-200 rounded text-[10px] text-charcoal-700">
                      {t}
                    </span>
                  ))}
                </div>
                <div className="pt-2 text-xs text-charcoal-700 space-y-1">
                  {proj.highlights.map((h, i) => (
                    <p key={i} className="flex items-start gap-1.5 text-[11px]">
                      <span className="text-steel-600">•</span>
                      <span>{h}</span>
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </PanelBody>
        </Panel>
      )}

      {activeTab === 'experience' && (
        <Panel>
          <PanelHeader title="Internship & Industry Experience" />
          <PanelBody className="space-y-4">
            {experience.map((exp) => (
              <div key={exp.id} className="p-4 border border-charcoal-200 rounded-md bg-white space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-xs text-charcoal-900">{exp.role}</h4>
                    <p className="text-xs text-charcoal-600">{exp.company} • {exp.location}</p>
                  </div>
                  <span className="text-[11px] font-mono text-charcoal-600">
                    {exp.startDate} – {exp.endDate}
                  </span>
                </div>
                <p className="text-xs text-charcoal-700">{exp.description}</p>
                <div className="pt-2 space-y-1">
                  {exp.highlights.map((h, i) => (
                    <p key={i} className="flex items-start gap-1.5 text-[11px] text-charcoal-600">
                      <span className="text-emerald-600 font-bold">✓</span>
                      <span>{h}</span>
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </PanelBody>
        </Panel>
      )}
    </div>
  );
};
