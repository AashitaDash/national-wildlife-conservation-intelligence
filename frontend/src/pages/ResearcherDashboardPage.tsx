import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Award,
  TrendingUp,
  CheckCircle2,
  Clock,
  AlertCircle,
  Plus,
  Trophy,
  Compass,
  FileCheck,
  ChevronRight,
  Sparkles,
  Bot,
  FileText,
  Search,
  DownloadCloud,
  MapPin,
  Calendar,
  User,
  ShieldCheck,
  Activity
} from 'lucide-react';
import { submissionService, gamificationService } from '../services/api';
import { Submission, ResearcherProfile } from '../types';
import { useAuth } from '../hooks/useAuth';

export const ResearcherDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState<ResearcherProfile | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [profileRes, subRes] = await Promise.allSettled([
          gamificationService.getMyProfile(),
          submissionService.getMySubmissions(),
        ]);
        if (profileRes.status === 'fulfilled') setProfile(profileRes.value);
        if (subRes.status === 'fulfilled') setSubmissions(subRes.value);
      } catch (err) {
        console.error('Failed to load researcher dashboard', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const pendingCount = submissions.filter((s) => s.status === 'PENDING_REVIEW' || s.status === 'UNDER_REVIEW').length;
  const verifiedCount = submissions.filter((s) => s.status === 'VERIFIED').length;
  const actionNeededCount = submissions.filter((s) => s.status === 'MORE_INFO_NEEDED').length;

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#e2ded5] pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold tracking-widest text-[#11682f] uppercase mb-1">
            <Compass className="w-4 h-4" />
            Field Research Station
          </div>
          <h1 className="text-3xl font-serif font-bold text-[#1f1e1a]">Researcher Command</h1>
          <p className="text-sm text-[#736f66] mt-1">
            Log sightings, track verification progress, and contribute to national biodiversity surveillance.
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            to="/submit"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#11682f] hover:bg-[#0e5426] text-white text-xs font-mono font-bold tracking-wider uppercase rounded shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            Log New Sighting
          </Link>
          <Link
            to="/leaderboard"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#eae7df] hover:bg-[#dedad0] text-[#2c2b27] text-xs font-mono font-bold tracking-wider uppercase rounded transition-colors"
          >
            <Trophy className="w-4 h-4" />
            Leaderboard
          </Link>
        </div>
      </div>

      {/* Mandatory Research Tools — AI Assistant & NLP / Ask the Corpus */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          to="/assistant"
          className="group p-5 rounded border border-[#e2ded5] bg-white shadow-sm hover:border-[#11682f] hover:shadow-md transition-all flex items-start gap-4"
        >
          <div className="w-10 h-10 rounded bg-[#11682f15] text-[#11682f] flex items-center justify-center shrink-0 group-hover:bg-[#11682f] group-hover:text-white transition-colors">
            <Bot className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#11682f]">Evidence-Grounded AI</span>
              <ChevronRight className="w-4 h-4 text-[#736f66] group-hover:text-[#11682f] group-hover:translate-x-0.5 transition-all" />
            </div>
            <h3 className="font-serif font-bold text-base text-[#1f1e1a] mt-0.5">Conservation AI Assistant</h3>
            <p className="text-xs text-[#736f66] mt-1">
              Ask questions grounded strictly in national species databases, risk rankings, and spatial evidence with strict source attribution.
            </p>
          </div>
        </Link>

        <Link
          to="/documents"
          className="group p-5 rounded border border-[#e2ded5] bg-white shadow-sm hover:border-[#0891b2] hover:shadow-md transition-all flex items-start gap-4"
        >
          <div className="w-10 h-10 rounded bg-[#0891b215] text-[#0891b2] flex items-center justify-center shrink-0 group-hover:bg-[#0891b2] group-hover:text-white transition-colors">
            <FileText className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#0891b2]">Corpus Intelligence & QA</span>
              <ChevronRight className="w-4 h-4 text-[#736f66] group-hover:text-[#0891b2] group-hover:translate-x-0.5 transition-all" />
            </div>
            <h3 className="font-serif font-bold text-base text-[#1f1e1a] mt-0.5">NLP / Ask the Corpus</h3>
            <p className="text-xs text-[#736f66] mt-1">
              Upload research papers and query the unstructured conservation corpus with hybrid retrieval, topic extraction, and entity linking.
            </p>
          </div>
        </Link>
      </div>

      {/* Gamification / Impact Progress */}
      {profile && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-[#1f1e1a] text-white p-5 rounded border border-[#33312b] shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-mono text-[#a39e93] uppercase tracking-wider mb-2">
                <span>Researcher Rank</span>
                <Sparkles className="w-3.5 h-3.5 text-[#e5b53d]" />
              </div>
              <div className="text-2xl font-serif font-bold text-white mb-1">{profile.level}</div>
              <div className="text-xs text-[#a39e93]">
                {profile.total_points} total contribution points
              </div>
            </div>
            {profile.next_level_points && (
              <div className="mt-4 pt-3 border-t border-[#33312b]">
                <div className="flex justify-between text-[11px] font-mono text-[#a39e93] mb-1">
                  <span>Next Level</span>
                  <span>{profile.progress_to_next_pct ?? 0}%</span>
                </div>
                <div className="w-full bg-[#3a3731] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[#3fc067] h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(profile.progress_to_next_pct ?? 0, 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-mono text-[#736f66] uppercase tracking-wider mb-2">
                <span>Verified Sightings</span>
                <FileCheck className="w-4 h-4 text-[#11682f]" />
              </div>
              <div className="text-3xl font-serif font-bold text-[#1f1e1a]">{profile.verified_count}</div>
              <div className="text-xs text-[#736f66] mt-1">Promoted into official registry</div>
            </div>
            <div className="text-[11px] font-mono text-[#11682f] mt-3 pt-2 border-t border-[#f0ede6]">
              {profile.distinct_species} unique species surveyed
            </div>
          </div>

          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-mono text-[#736f66] uppercase tracking-wider mb-2">
                <span>Under Review</span>
                <Clock className="w-4 h-4 text-[#c4841d]" />
              </div>
              <div className="text-3xl font-serif font-bold text-[#1f1e1a]">{pendingCount}</div>
              <div className="text-xs text-[#736f66] mt-1">Awaiting Forest Officer audit</div>
            </div>
            <div className="text-[11px] font-mono text-[#736f66] mt-3 pt-2 border-t border-[#f0ede6]">
              Avg decision turnaround: 48h
            </div>
          </div>

          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-xs font-mono text-[#736f66] uppercase tracking-wider mb-2">
                <span>Field Badges</span>
                <Award className="w-4 h-4 text-[#8a3324]" />
              </div>
              <div className="text-3xl font-serif font-bold text-[#1f1e1a]">{profile.badges.length}</div>
              <div className="text-xs text-[#736f66] mt-1">Earned honors & achievements</div>
            </div>
            <div className="flex gap-1.5 mt-3 pt-2 border-t border-[#f0ede6] overflow-x-auto">
              {profile.badges.slice(0, 4).map((b) => (
                <span key={b.code} title={`${b.name}: ${b.description}`} className="text-lg">
                  {b.icon_emoji || '🏅'}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Action Needed Banner if submissions need info */}
      {actionNeededCount > 0 && (
        <div className="p-4 bg-[#fff9ed] border border-[#f0c36d] rounded flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-[#b07d1a] shrink-0" />
            <div>
              <div className="text-xs font-mono font-bold uppercase tracking-wider text-[#8a5b00]">
                Action Required
              </div>
              <p className="text-sm text-[#4d3a0e]">
                {actionNeededCount} of your submissions have requested revisions or additional photo evidence from Forest Officers.
              </p>
            </div>
          </div>
          <Link
            to="/my-submissions?status=MORE_INFO_NEEDED"
            className="px-3 py-1.5 bg-[#b07d1a] hover:bg-[#8f6412] text-white text-xs font-mono font-bold tracking-wider uppercase rounded transition-colors"
          >
            Review Feedback
          </Link>
        </div>
      )}

      {/* Recent Submissions Table */}
      <div className="bg-white rounded border border-[#e2ded5] shadow-sm overflow-hidden">
        <div className="p-5 border-b border-[#e2ded5] flex items-center justify-between">
          <div>
            <h3 className="font-serif font-bold text-lg text-[#1f1e1a]">Recent Field Logs</h3>
            <p className="text-xs text-[#736f66]">Sightings logged by your field account</p>
          </div>
          <Link
            to="/my-submissions"
            className="text-xs font-mono font-bold text-[#11682f] hover:underline uppercase tracking-wider flex items-center gap-1"
          >
            View All ({submissions.length}) <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm font-mono text-[#736f66]">
            Loading field records...
          </div>
        ) : submissions.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <Compass className="w-10 h-10 text-[#a39e93] mx-auto" />
            <h4 className="font-serif font-bold text-[#2c2b27]">No Field Logs Yet</h4>
            <p className="text-xs text-[#736f66] max-w-sm mx-auto">
              Start logging your field observations to earn points, unlock conservation badges, and build the verified national dataset.
            </p>
            <Link
              to="/submit"
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#11682f] text-white text-xs font-mono font-bold uppercase tracking-wider rounded"
            >
              <Plus className="w-4 h-4" /> Log First Sighting
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#e2ded5] bg-[#f9f8f5] text-[#736f66] font-mono uppercase tracking-wider">
                  <th className="py-3 px-4">Species</th>
                  <th className="py-3 px-4">Observed At</th>
                  <th className="py-3 px-4">Coordinates</th>
                  <th className="py-3 px-4">Evidence</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0ede6]">
                {submissions.slice(0, 8).map((sub) => (
                  <tr key={sub.id} className="hover:bg-[#faf9f6]">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-[#1f1e1a]">{sub.species_common_name || 'Unidentified'}</div>
                      <div className="font-serif italic text-[#736f66] text-[11px]">{sub.species_scientific_name}</div>
                    </td>
                    <td className="py-3 px-4 font-mono text-[#4d4a43]">
                      {new Date(sub.observed_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-[#736f66]">
                      {sub.latitude.toFixed(4)}, {sub.longitude.toFixed(4)}
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {sub.images && sub.images.length > 0 ? (
                        <span className="text-[#11682f] font-semibold">{sub.images.length} photo(s)</span>
                      ) : (
                        <span className="text-[#a39e93]">None</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider uppercase ${
                          sub.status === 'VERIFIED'
                            ? 'bg-[#d8f3e1] text-[#11682f]'
                            : sub.status === 'REJECTED'
                            ? 'bg-[#fde2e1] text-[#a8251e]'
                            : sub.status === 'MORE_INFO_NEEDED'
                            ? 'bg-[#fff1d0] text-[#8a5b00]'
                            : 'bg-[#edf1f7] text-[#345280]'
                        }`}
                      >
                        {sub.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/my-submissions#${sub.id}`}
                        className="text-[#11682f] font-mono font-bold hover:underline"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Verified Researcher Profile Card & Genuine Achievements */}
      <div className="bg-white rounded border border-[#e2ded5] shadow-sm p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#e2ded5] pb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-[#11682f] text-white flex items-center justify-center font-bold text-lg font-mono">
              {(user?.full_name || user?.username || 'R').slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-serif font-bold text-xl text-[#1f1e1a]">{user?.full_name || user?.username || 'Authenticated Researcher'}</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#d8f3e1] text-[#11682f]">
                  VERIFIED RESEARCHER
                </span>
              </div>
              <p className="text-xs text-[#736f66] mt-0.5">
                Username: @{user?.username} · Email: {user?.email}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="text-right">
              <span className="text-[#94918a] block text-[10px] uppercase">Total Submissions</span>
              <span className="text-base font-bold text-[#1f1e1a]">{submissions.length}</span>
            </div>
            <div className="text-right">
              <span className="text-[#94918a] block text-[10px] uppercase">Latest Contribution</span>
              <span className="text-base font-bold text-[#11682f]">
                {submissions.length > 0 && submissions[0].created_at
                  ? new Date(submissions[0].created_at).toLocaleDateString()
                  : 'No records'}
              </span>
            </div>
          </div>
        </div>

        {/* Genuine Database-backed Badges */}
        <div className="mt-5">
          <div className="flex items-center justify-between mb-3">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#736f66]">
              Earned Conservation Badges ({profile?.badges?.length ?? 0})
            </span>
            <span className="text-[11px] font-mono text-[#94918a]">Calculated strictly from database records</span>
          </div>

          {!profile?.badges || profile.badges.length === 0 ? (
            <div className="p-4 rounded bg-[#faf9f6] border border-[#f0ede6] text-xs text-[#736f66] text-center font-mono">
              No badges awarded yet. Submit verified observations to earn official field badges.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {profile.badges.map((b) => (
                <div
                  key={b.code}
                  className="p-3.5 rounded border border-[#f0ede6] bg-[#fdfcfa] flex items-start gap-3"
                >
                  <span className="text-2xl shrink-0">{b.icon_emoji || '🏅'}</span>
                  <div>
                    <h5 className="font-serif font-bold text-xs text-[#1f1e1a]">{b.name}</h5>
                    <p className="text-[11px] text-[#736f66] mt-0.5 leading-snug">{b.description}</p>
                    <span className="text-[9px] font-mono text-[#94918a] block mt-1">
                      Awarded: {new Date(b.awarded_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

