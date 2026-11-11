import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  CheckCircle2
} from 'lucide-react';
import { useApp } from '../../context/appContextDef';
import { Panel, Button, Modal } from '../../components/common/UIComponents';
import type { CalendarEvent } from '../../types';

export const CalendarPage: React.FC = () => {
  const { calendarEvents, addCalendarEvent, toggleEventCompletion } = useApp();

  const [filterType, setFilterType] = useState<string>('all');
  const [modalOpen, setModalOpen] = useState(false);

  // New Event Form State
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('2026-11-16');
  const [time, setTime] = useState('14:00 IST');
  const [type, setType] = useState<CalendarEvent['type']>('personal');
  const [company] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');

  const filteredEvents = calendarEvents.filter(e => {
    if (filterType === 'all') return true;
    return e.type === filterType;
  }).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  const handleCreateEvent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !date) return;

    addCalendarEvent({
      title: title.trim(),
      date,
      time: time.trim() || undefined,
      type,
      company: company.trim() || undefined,
      description: description.trim() || undefined,
      priority,
      completed: false
    });

    setTitle('');
    setDescription('');
    setModalOpen(false);
  };

  const getEventBadge = (evtType: CalendarEvent['type']) => {
    switch (evtType) {
      case 'interview':
        return 'bg-emerald-50 text-emerald-800 border-emerald-300';
      case 'assessment':
        return 'bg-indigo-50 text-indigo-800 border-indigo-300';
      case 'deadline':
        return 'bg-amber-50 text-amber-800 border-amber-300';
      case 'follow_up':
        return 'bg-blue-50 text-blue-800 border-blue-300';
      case 'prep':
        return 'bg-purple-50 text-purple-800 border-purple-300';
      default:
        return 'bg-canvas-100 text-charcoal-700 border-charcoal-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white border border-charcoal-200 rounded-lg p-5 shadow-card flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-charcoal-900 tracking-tight">Placement Calendar & Deadlines</h2>
          <p className="text-xs text-charcoal-600 mt-1">
            Consolidated timeline for online coding assessments, interview rounds, portal submission deadlines, and personal practice tasks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => setModalOpen(true)}
            icon={<Plus className="w-3.5 h-3.5" />}
          >
            Add Personal Reminder
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto text-xs font-medium border-b border-charcoal-200 pb-2">
        <button
          onClick={() => setFilterType('all')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'all' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          All Deadlines ({calendarEvents.length})
        </button>
        <button
          onClick={() => setFilterType('interview')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'interview' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Interviews
        </button>
        <button
          onClick={() => setFilterType('assessment')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'assessment' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Assessments
        </button>
        <button
          onClick={() => setFilterType('deadline')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'deadline' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Portal Deadlines
        </button>
        <button
          onClick={() => setFilterType('personal')}
          className={`px-3 py-1.5 rounded-md transition-colors ${
            filterType === 'personal' ? 'bg-[#263747] text-white font-semibold' : 'text-charcoal-600 hover:bg-canvas-100'
          }`}
        >
          Personal Tasks
        </button>
      </div>

      {/* Calendar List View */}
      <div className="space-y-3">
        {filteredEvents.map((evt) => (
          <Panel key={evt.id} className="p-4 bg-white hover:border-steel-400 transition-colors">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-start gap-3">
                <button
                  onClick={() => toggleEventCompletion(evt.id)}
                  className={`mt-0.5 w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                    evt.completed
                      ? 'bg-emerald-600 border-emerald-600 text-white'
                      : 'border-charcoal-300 hover:border-steel-500 bg-white'
                  }`}
                  title={evt.completed ? "Mark incomplete" : "Mark completed"}
                >
                  {evt.completed && <CheckCircle2 className="w-3.5 h-3.5" />}
                </button>

                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className={`font-bold text-xs ${evt.completed ? 'line-through text-charcoal-600' : 'text-charcoal-900'}`}>
                      {evt.title}
                    </h4>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border uppercase ${getEventBadge(evt.type)}`}>
                      {evt.type}
                    </span>
                    {evt.priority === 'high' && (
                      <span className="text-[10px] font-bold text-red-700 bg-red-50 border border-red-200 px-1.5 py-0.2 rounded">
                        High Priority
                      </span>
                    )}
                  </div>

                  {evt.description && (
                    <p className="text-[11px] text-charcoal-600 mt-1 leading-relaxed">
                      {evt.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-4 text-right shrink-0 ml-8 sm:ml-0">
                <div>
                  <span className="font-semibold text-charcoal-900 font-mono block text-xs">{evt.date}</span>
                  {evt.time && <span className="text-[11px] text-charcoal-600">{evt.time}</span>}
                </div>

                {evt.applicationId && (
                  <Link to={`/app/applications/${evt.applicationId}`}>
                    <Button variant="outline" size="sm">
                      Inspect Application →
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          </Panel>
        ))}

        {filteredEvents.length === 0 && (
          <Panel className="p-8 text-center text-xs text-charcoal-600">
            No deadlines or events in this category.
          </Panel>
        )}
      </div>

      {/* Modal: Add Personal Reminder */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Create Placement Reminder or Task"
        subtitle="Saved to your local calendar state"
        maxWidth="max-w-md"
      >
        <form onSubmit={handleCreateEvent} className="space-y-3.5 text-xs">
          <div>
            <label className="block font-semibold text-charcoal-800 mb-1">Title</label>
            <input
              type="text"
              required
              placeholder="e.g. Solve 3 Graph Problems before Atlassian test"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900 focus:outline-none focus:border-steel-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-charcoal-800 mb-1">Target Date</label>
              <input
                type="date"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
              />
            </div>
            <div>
              <label className="block font-semibold text-charcoal-800 mb-1">Time (Optional)</label>
              <input
                type="text"
                placeholder="e.g. 15:00 IST"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-charcoal-800 mb-1">Category</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as CalendarEvent['type'])}
                className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
              >
                <option value="personal">Personal Task</option>
                <option value="prep">Preparation Session</option>
                <option value="assessment">Online Assessment</option>
                <option value="deadline">Portal Deadline</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold text-charcoal-800 mb-1">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as CalendarEvent['priority'])}
                className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
              >
                <option value="low">Low Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="high">High Priority</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-charcoal-800 mb-1">Notes / Description (Optional)</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add key reminders or links..."
              className="w-full bg-white border border-charcoal-200 rounded p-2 text-charcoal-900"
            />
          </div>

          <div className="pt-3 border-t border-charcoal-100 flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm">
              Save Reminder
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
