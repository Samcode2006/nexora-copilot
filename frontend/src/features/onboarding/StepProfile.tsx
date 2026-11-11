import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, User, School, MapPin } from 'lucide-react';
import { Button } from '../../components/common/UIComponents';
import { useApp } from '../../context/appContextDef';

export const StepProfile: React.FC = () => {
  const navigate = useNavigate();
  const { profile, updateProfile } = useApp();

  const [fullName, setFullName] = useState(profile.fullName || 'Aarav Sharma');
  const [college, setCollege] = useState(profile.college || '');
  const [degree, setDegree] = useState(profile.degree || 'Bachelor of Technology');
  const [branch, setBranch] = useState(profile.branch || 'Computer Science and Engineering');
  const [graduationYear, setGraduationYear] = useState(profile.graduationYear || '2027');
  const [currentYear, setCurrentYear] = useState(profile.currentYear || 'Final Year (4th Year)');
  const [location, setLocation] = useState(profile.location || 'Bangalore / Chennai / Remote');

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile({
      fullName,
      college,
      degree,
      branch,
      graduationYear,
      currentYear,
      location
    });
    navigate('/onboarding/resume');
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-bold text-charcoal-900">Academic &amp; Basic Profile</h2>
        <p className="text-xs text-charcoal-600 mt-1">
          Tell us about your college or university, department, and degree. Nexora supports students across any college, institute, or university.
        </p>
      </div>

      <form onSubmit={handleNext} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-charcoal-700 mb-1">
            Full Name
          </label>
          <div className="relative">
            <User className="w-4 h-4 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              className="w-full bg-white border border-charcoal-200 rounded-md py-2 pl-9 pr-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-charcoal-700 mb-1">
            College / University
          </label>
          <div className="relative">
            <School className="w-4 h-4 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={college}
              onChange={(e) => setCollege(e.target.value)}
              required
              placeholder="e.g. Your College / University / Institute Name"
              className="w-full bg-white border border-charcoal-200 rounded-md py-2 pl-9 pr-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
            />
          </div>
          <p className="text-[11px] text-charcoal-500 mt-1">Open to students from any college or university.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-charcoal-700 mb-1">
              Degree Program
            </label>
            <input
              type="text"
              value={degree}
              onChange={(e) => setDegree(e.target.value)}
              required
              placeholder="e.g. B.Tech"
              className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-charcoal-700 mb-1">
              Branch / Department
            </label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              required
              placeholder="e.g. Computer Science and Engineering"
              className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-charcoal-700 mb-1">
              Current Academic Year
            </label>
            <select
              value={currentYear}
              onChange={(e) => setCurrentYear(e.target.value)}
              className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
            >
              <option value="Final Year (4th Year)">Final Year (4th Year)</option>
              <option value="Pre-final Year (3rd Year)">Pre-final Year (3rd Year)</option>
              <option value="Sophomore (2nd Year)">Sophomore (2nd Year)</option>
              <option value="Freshman (1st Year)">Freshman (1st Year)</option>
              <option value="Master's / Postgrad">Master's / Postgrad</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-charcoal-700 mb-1">
              Graduation Year
            </label>
            <select
              value={graduationYear}
              onChange={(e) => setGraduationYear(e.target.value)}
              className="w-full bg-white border border-charcoal-200 rounded-md py-2 px-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
            >
              <option value="2027">2027</option>
              <option value="2026">2026</option>
              <option value="2028">2028</option>
              <option value="2025">2025</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-charcoal-700 mb-1">
            Current / Target Location(s)
          </label>
          <div className="relative">
            <MapPin className="w-4 h-4 text-charcoal-600 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Bangalore, Hyderabad, Remote"
              className="w-full bg-white border border-charcoal-200 rounded-md py-2 pl-9 pr-3 text-xs text-charcoal-900 focus:outline-none focus:border-steel-500"
            />
          </div>
        </div>

        <div className="pt-4 flex justify-end">
          <Button type="submit" variant="primary" icon={<ArrowRight className="w-4 h-4" />}>
            Next: Upload Resume
          </Button>
        </div>
      </form>
    </div>
  );
};
