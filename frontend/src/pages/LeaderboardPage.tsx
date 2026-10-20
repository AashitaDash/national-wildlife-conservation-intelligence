import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Trophy,
  Award,
  Medal,
  Users,
  Compass,
  Sparkles,
  TrendingUp,
  ShieldCheck,
} from 'lucide-react';
import { gamificationService } from '../services/api';
import { LeaderboardEntry, Badge } from '../types';

export const LeaderboardPage: React.FC = () => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [lbRes, badgeRes] = await Promise.allSettled([
          gamificationService.getLeaderboard(25),
          gamificationService.getBadges(),
        ]);
        if (lbRes.status === 'fulfilled') setLeaderboard(lbRes.value);
        if (badgeRes.status === 'fulfilled') setBadges(badgeRes.value);
      } catch (err) {
        console.error('Failed to load leaderboard', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[#e2ded5] pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold tracking-widest text-[#11682f] uppercase mb-1">
            <Trophy className="w-4 h-4 text-[#e5b53d]" />
            National Field Network
          </div>
          <h1 className="text-3xl font-serif font-bold text-[#1f1e1a]">Researcher Honor Roll</h1>
          <p className="text-sm text-[#736f66] mt-1">
            Recognizing dedicated researchers logging verified wildlife records across Indian sanctuaries.
          </p>
        </div>
        <Link
          to="/submit"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#11682f] hover:bg-[#0e5426] text-white text-xs font-mono font-bold tracking-wider uppercase rounded shadow-sm transition-colors"
        >
          <Compass className="w-4 h-4" /> Log Sightings to Climb
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Main Column: Leaderboard Table */}
        <div className="lg:col-span-8 space-y-4">
          <div className="bg-white rounded border border-[#e2ded5] shadow-sm overflow-hidden">
            <div className="p-5 border-b border-[#e2ded5] flex items-center justify-between">
              <div>
                <h3 className="font-serif font-bold text-lg text-[#1f1e1a]">Top Conservation Contributors</h3>
                <p className="text-xs text-[#736f66]">Ranked by verified sighting points and taxonomy breadth</p>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-mono text-[#11682f]">
                <Users className="w-3.5 h-3.5" />
                <span>{leaderboard.length} Field Naturalists</span>
              </div>
            </div>

            {loading ? (
              <div className="p-8 text-center text-xs font-mono text-[#736f66]">Loading standings...</div>
            ) : leaderboard.length === 0 ? (
              <div className="p-8 text-center text-xs font-mono text-[#736f66]">
                No rankings recorded yet. Be the first to log a verified observation!
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[#e2ded5] bg-[#f9f8f5] text-[#736f66] font-mono uppercase tracking-wider">
                      <th className="py-3 px-4 text-center w-12">Rank</th>
                      <th className="py-3 px-4">Researcher</th>
                      <th className="py-3 px-4">Rank Tier</th>
                      <th className="py-3 px-4 text-center">Verified Sightings</th>
                      <th className="py-3 px-4 text-center">Unique Species</th>
                      <th className="py-3 px-4 text-right">Points</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f0ede6]">
                    {leaderboard.map((user) => (
                      <tr
                        key={user.user_id}
                        className={`hover:bg-[#faf9f6] transition-colors ${
                          user.rank === 1
                            ? 'bg-[#fffdf7]'
                            : user.rank === 2
                            ? 'bg-[#fafafa]'
                            : user.rank === 3
                            ? 'bg-[#fffaf8]'
                            : ''
                        }`}
                      >
                        <td className="py-3.5 px-4 text-center">
                          {user.rank === 1 ? (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#fdeaa8] text-[#8a6805] font-bold font-mono">
                              🥇
                            </span>
                          ) : user.rank === 2 ? (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#e3e2de] text-[#4d4a43] font-bold font-mono">
                              🥈
                            </span>
                          ) : user.rank === 3 ? (
                            <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#ebd7c8] text-[#8a4f21] font-bold font-mono">
                              🥉
                            </span>
                          ) : (
                            <span className="font-mono font-bold text-[#736f66]">#{user.rank}</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-sm text-[#1f1e1a]">{user.display_name}</div>
                          <div className="flex items-center gap-1.5 text-[11px] font-mono text-[#736f66] mt-0.5">
                            <Award className="w-3 h-3 text-[#11682f]" />
                            <span>{user.badge_count} badges unlocked</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="inline-block px-2 py-0.5 bg-[#eae7df] text-[#2c2b27] font-mono text-[10px] font-bold rounded uppercase tracking-wider">
                            {user.level}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-center font-mono font-semibold text-[#11682f]">
                          {user.verified_count}
                        </td>
                        <td className="py-3.5 px-4 text-center font-mono text-[#2c2b27]">
                          {user.distinct_species}
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-bold text-sm text-[#1f1e1a]">
                          {user.total_points.toLocaleString()} pts
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Badge Catalog */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white rounded border border-[#e2ded5] shadow-sm p-5 space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-[#736f66]">
              <Sparkles className="w-4 h-4 text-[#e5b53d]" />
              Conservation Badge Catalog
            </div>
            <p className="text-xs text-[#736f66] leading-relaxed">
              Earn distinctive recognition for taxonomic breadth, field surveillance consistency, and rare species documentation.
            </p>

            <div className="space-y-3 pt-2">
              {badges.map((badge) => (
                <div
                  key={badge.code}
                  className="p-3 bg-[#faf9f6] rounded border border-[#f0ede6] flex items-start gap-3"
                >
                  <span className="text-2xl shrink-0 p-1 bg-white rounded border border-[#e2ded5] shadow-xs">
                    {badge.icon_emoji || '🏅'}
                  </span>
                  <div>
                    <h5 className="font-semibold text-xs text-[#1f1e1a]">{badge.name}</h5>
                    <p className="text-[11px] text-[#736f66] mt-0.5 leading-snug">
                      {badge.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-[#1f1e1a] text-white rounded border border-[#33312b] p-5 space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-[#a7ebba]">
              <ShieldCheck className="w-4 h-4" />
              Verification Rewards
            </div>
            <ul className="text-xs text-[#c5c0b5] space-y-2 font-mono">
              <li className="flex items-center justify-between border-b border-[#33312b] pb-1.5">
                <span>Field Log Logged</span>
                <span className="text-[#3fc067] font-bold">+10 pts</span>
              </li>
              <li className="flex items-center justify-between border-b border-[#33312b] pb-1.5">
                <span>Officer Peer Verification</span>
                <span className="text-[#3fc067] font-bold">+50 pts</span>
              </li>
              <li className="flex items-center justify-between border-b border-[#33312b] pb-1.5">
                <span>First Species Survey</span>
                <span className="text-[#3fc067] font-bold">+100 pts</span>
              </li>
              <li className="flex items-center justify-between">
                <span>Photo Evidence Included</span>
                <span className="text-[#3fc067] font-bold">+25 pts</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
