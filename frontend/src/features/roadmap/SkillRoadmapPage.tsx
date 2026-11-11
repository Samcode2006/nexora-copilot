import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  ExternalLink,
  BookOpen,
  Plus
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, Button, Modal } from '../../components/common/UIComponents';

export const SkillRoadmapPage: React.FC = () => {
  const { roadmapTasks, updateTaskStatus, addRoadmapTask } = useApp();

  const [activeTab, setActiveTab] = useState<'All' | 'High' | 'Recommended' | 'Optional'>('All');
  const [modalOpen, setModalOpen] = useState(false);

  // New task form state
  const [skillName, setSkillName] = useState('');
  const [category, setCategory] = useState<'Frontend' | 'Backend' | 'Database' | 'Systems' | 'Behavioral'>('Backend');
  const [priority, setPriority] = useState<'High' | 'Recommended' | 'Optional'>('High');
  const [estimatedHours, setEstimatedHours] = useState(8);
  const [reason, setReason] = useState('');

  const filteredTasks = roadmapTasks.filter(t => {
    if (activeTab === 'All') return true;
    return t.priority === activeTab;
  });

  const completedCount = roadmapTasks.filter(t => t.status === 'Completed').length;
  const progressPercent = Math.round((completedCount / roadmapTasks.length) * 100);

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!skillName.trim() || !reason.trim()) return;

    addRoadmapTask({
      skillName: skillName.trim(),
      category,
      priority,
      estimatedHours,
      reason: reason.trim(),
      targetRoles: ['Backend Engineer', 'Full Stack Developer'],
      resources: [
        { title: `${skillName.trim()} Documentation & Walkthrough`, type: 'Doc', link: 'https://docs.nexora.dev' }
      ]
    });

    setSkillName('');
    setReason('');
    setModalOpen(false);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Personalized Skill Roadmap</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-steel-100 text-steel-800 border border-steel-200">
              Gap Remediation Plan
            </span>
          </div>
          <p className="text-xs text-charcoal-600 mt-1 max-w-2xl leading-relaxed">
            Directly bridge identified gaps from target role postings and interview evaluations. Every task is tied to real opportunities in your pipeline.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => setModalOpen(true)}
            icon={<Plus className="w-3.5 h-3.5" />}
          >
            Add Personal Learning Task
          </Button>
        </div>
      </div>

      {/* Progress Metric Banner */}
      <Panel className="p-4 bg-white">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
          <div>
            <span className="font-semibold text-charcoal-800">Roadmap Completion Progress:</span>
            <span className="ml-2 font-bold text-steel-700">{completedCount} of {roadmapTasks.length} tasks completed ({progressPercent}%)</span>
          </div>
          <div className="w-full sm:w-64 bg-charcoal-100 h-2 rounded-full overflow-hidden">
            <div className="bg-steel-600 h-full rounded-full transition-all duration-300" style={{ width: `${progressPercent}%` }} />
          </div>
        </div>
      </Panel>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto text-xs font-medium border-b border-charcoal-200 pb-2">
        {(['All', 'High', 'Recommended', 'Optional'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === tab ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
            }`}
          >
            {tab === 'All' ? `All Tasks (${roadmapTasks.length})` : `${tab} Priority`}
          </button>
        ))}
      </div>

      {/* Roadmap Tasks List */}
      <div className="space-y-4">
        {filteredTasks.map((task) => (
          <Panel key={task.id} className="p-5 bg-white">
            <div className="flex flex-col md:flex-row items-start justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <button
                  onClick={() => updateTaskStatus(task.id, task.status === 'Completed' ? 'Not started' : 'Completed')}
                  className={`mt-0.5 w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                    task.status === 'Completed'
                      ? 'bg-emerald-600 border-emerald-600 text-white'
                      : 'border-charcoal-300 hover:border-steel-500 bg-white'
                  }`}
                  title={task.status === 'Completed' ? "Mark incomplete" : "Mark completed"}
                >
                  {task.status === 'Completed' && <CheckCircle2 className="w-3.5 h-3.5" />}
                </button>

                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className={`font-bold text-sm ${task.status === 'Completed' ? 'line-through text-charcoal-600' : 'text-charcoal-900'}`}>
                      {task.skillName}
                    </h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-canvas-100 text-charcoal-700 border border-charcoal-200">
                      {task.category}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        task.priority === 'High'
                          ? 'bg-red-50 text-red-800 border-red-200'
                          : task.priority === 'Recommended'
                          ? 'bg-amber-50 text-amber-800 border-amber-200'
                          : 'bg-canvas-100 text-charcoal-600 border-charcoal-200'
                      }`}
                    >
                      {task.priority} Priority
                    </span>
                    <span className="text-[11px] text-charcoal-600 flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3" /> ~{task.estimatedHours} hrs
                    </span>
                  </div>

                  <p className="text-xs text-charcoal-700 leading-relaxed max-w-3xl">
                    <span className="font-semibold text-charcoal-900">Why it matters:</span> {task.reason}
                  </p>

                  <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-charcoal-600">
                    <span className="text-[11px] font-medium text-charcoal-700">Targeted Roles:</span>
                    {task.targetRoles.map(r => (
                      <span key={r} className="px-2 py-0.5 bg-canvas-50 border border-charcoal-200 rounded text-[10px]">
                        {r}
                      </span>
                    ))}
                    <span>•</span>
                    <span className="text-[11px] text-steel-600 font-medium">Relevant to {task.relatedJobCount} matched jobs</span>
                  </div>

                  {/* Curated Resources */}
                  {task.resources && task.resources.length > 0 && (
                    <div className="pt-2 flex flex-wrap gap-2 text-xs">
                      {task.resources.map(res => (
                        <a
                          key={res.title}
                          href={res.link}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white border border-charcoal-200 hover:border-steel-400 rounded text-[11px] text-steel-700 hover:text-steel-900 transition-colors shadow-subtle"
                        >
                          <BookOpen className="w-3 h-3 text-steel-600" />
                          <span>{res.title}</span>
                          <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Status Switcher Tool */}
              <div className="flex items-center gap-2 shrink-0 ml-8 md:ml-0 mt-2 md:mt-0">
                <select
                  value={task.status}
                  onChange={(e) => updateTaskStatus(task.id, e.target.value as 'Not started' | 'In progress' | 'Completed')}
                  className="bg-white border border-charcoal-200 rounded px-2.5 py-1 text-xs font-semibold text-charcoal-800 focus:outline-none focus:border-steel-500"
                >
                  <option value="Not started">Not started</option>
                  <option value="In progress">In progress</option>
                  <option value="Completed">Completed</option>
                </select>
              </div>
            </div>
          </Panel>
        ))}
      </div>

      {/* Modal: Add Learning Task */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Add Learning Goal to Skill Roadmap"
        subtitle="Saved to your persistent development plan"
        maxWidth="max-w-md"
      >
        <form onSubmit={handleCreateTask} className="space-y-3.5 text-xs">
          <div>
            <label className="block font-semibold text-charcoal-800 mb-1">Skill or Concept Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Distributed Tracing with OpenTelemetry"
              value={skillName}
              onChange={(e) => setSkillName(e.target.value)}
              className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-charcoal-800 mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as 'Frontend' | 'Backend' | 'Database' | 'Systems' | 'Behavioral')}
                className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
              >
                <option value="Backend">Backend</option>
                <option value="Frontend">Frontend</option>
                <option value="Database">Database</option>
                <option value="Systems">Systems</option>
                <option value="Behavioral">Behavioral</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold text-charcoal-800 mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as 'High' | 'Recommended' | 'Optional')}
                className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
              >
                <option value="High">High Priority</option>
                <option value="Recommended">Recommended</option>
                <option value="Optional">Optional</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-charcoal-800 mb-1">Estimated Hours</label>
            <input
              type="number"
              min={1}
              max={100}
              value={estimatedHours}
              onChange={(e) => setEstimatedHours(Number(e.target.value))}
              className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
            />
          </div>

          <div>
            <label className="block font-semibold text-charcoal-800 mb-1">Why This Matters (Context / Roles)</label>
            <textarea
              rows={3}
              required
              placeholder="Why this skill is relevant for your target roles..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900 leading-relaxed"
            />
          </div>

          <div className="pt-3 border-t border-charcoal-100 flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Add to Roadmap
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
