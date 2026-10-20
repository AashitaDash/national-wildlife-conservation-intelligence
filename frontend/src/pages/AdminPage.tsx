import React from 'react';
import { Settings, Users, Database, Cpu, ShieldCheck } from 'lucide-react';
import { DemoBanner } from '../components/DemoBanner';

export const AdminPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <DemoBanner />

      <div className="bg-white p-6 rounded-sm border border-[#e5e0d8]">
        <h1 className="text-xl font-bold text-[#1a1916] flex items-center gap-2 font-serif">
          <Settings className="w-5 h-5 text-emerald-700" />
          System Administration & ML Governance Console
        </h1>
        <p className="text-xs text-[#77746c] mt-1 font-mono uppercase tracking-wider">
          Role-Based Access Control, Data Sources, PostGIS Vector Indexes & Model Artifacts
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm space-y-3 shadow-sm hover:-translate-y-0.5 transition-transform">
          <div className="flex items-center gap-2 text-emerald-700">
            <Users className="w-5 h-5" />
            <h3 className="text-sm font-semibold text-[#1a1916]">User & Role Management</h3>
          </div>
          <p className="text-xs text-[#77746c] leading-relaxed">
            Manage system permissions, user registrations, and RBAC role assignments across RESEARCHER, FOREST_OFFICER, NGO, CITIZEN, and ADMIN.
          </p>
          <div className="pt-2 text-[10px] font-mono text-emerald-700 font-semibold uppercase tracking-wider">
            Status: Active & Enforced via FastAPI JWT
          </div>
        </div>

        <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm space-y-3 shadow-sm hover:-translate-y-0.5 transition-transform">
          <div className="flex items-center gap-2 text-emerald-700">
            <Database className="w-5 h-5" />
            <h3 className="text-sm font-semibold text-[#1a1916]">PostgreSQL + PostGIS + pgvector</h3>
          </div>
          <p className="text-xs text-[#77746c] leading-relaxed">
            Database instance health, Alembic schema migrations, 384-dimensional cosine index status, and geospatial spatial query logs.
          </p>
          <div className="pt-2 text-[10px] font-mono text-emerald-700 font-semibold uppercase tracking-wider">
            Index: HNSW / IVFFlat Enabled
          </div>
        </div>

        <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm space-y-3 shadow-sm hover:-translate-y-0.5 transition-transform">
          <div className="flex items-center gap-2 text-rose-700">
            <Cpu className="w-5 h-5" />
            <h3 className="text-sm font-semibold text-[#1a1916]">ML Model Governance</h3>
          </div>
          <p className="text-xs text-[#77746c] leading-relaxed">
            Serialized artifacts: random_forest_risk_v1.joblib, isolation_forest_anomaly_v1.joblib. Model evaluation metrics & drift logs.
          </p>
          <div className="pt-2 text-[10px] font-mono text-rose-700 font-semibold uppercase tracking-wider">
            Status: Model Version v1.0 Operational
          </div>
        </div>
      </div>
    </div>
  );
};
