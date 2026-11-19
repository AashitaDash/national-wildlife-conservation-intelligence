import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  Camera,
  MapPin,
  Calendar,
  FileText,
  AlertCircle,
  CheckCircle2,
  Compass,
  ArrowLeft,
} from 'lucide-react';
import { submissionService } from '../services/api';
import { speciesService } from '../services/api';
import { Species } from '../types';

export const SubmitSightingPage: React.FC = () => {
  const navigate = useNavigate();
  const [speciesList, setSpeciesList] = useState<Species[]>([]);
  const [searchSpecies, setSearchSpecies] = useState('');
  const [selectedSpeciesId, setSelectedSpeciesId] = useState<number | null>(null);

  const [latitude, setLatitude] = useState<string>('');
  const [longitude, setLongitude] = useState<string>('');
  const [accuracy, setAccuracy] = useState<string>('15');
  const [observedAt, setObservedAt] = useState<string>(
    new Date().toISOString().slice(0, 16)
  );

  const [description, setDescription] = useState('');
  const [habitatNotes, setHabitatNotes] = useState('');
  const [behaviorNotes, setBehaviorNotes] = useState('');
  const [identificationNotes, setIdentificationNotes] = useState('');

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    speciesService.getSpeciesList(1, 100).then((res) => {
      setSpeciesList(res.items || []);
    }).catch(console.error);
  }, []);

  const handleUseCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLatitude(pos.coords.latitude.toFixed(6));
          setLongitude(pos.coords.longitude.toFixed(6));
          setAccuracy(Math.round(pos.coords.accuracy).toString());
        },
        (err) => {
          setErrorMsg(`Geolocation error: ${err.message}`);
        }
      );
    } else {
      setErrorMsg('Geolocation is not supported by your browser.');
    }
  };

  const filteredSpecies = speciesList.filter(
    (s) =>
      s.common_name.toLowerCase().includes(searchSpecies.toLowerCase()) ||
      s.scientific_name.toLowerCase().includes(searchSpecies.toLowerCase())
  ).slice(0, 8);

  const handleSubmit = async (submitDirectly: boolean) => {
    if (!selectedSpeciesId) {
      setErrorMsg('Please select a species.');
      return;
    }
    const latNum = parseFloat(latitude);
    const lonNum = parseFloat(longitude);
    if (isNaN(latNum) || isNaN(lonNum)) {
      setErrorMsg('Please provide valid latitude and longitude coordinates.');
      return;
    }
    if (!description.trim()) {
      setErrorMsg('Please provide a field description of the observation.');
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);

      const created = await submissionService.createSubmission({
        species_id: selectedSpeciesId,
        observed_at: new Date(observedAt).toISOString(),
        latitude: latNum,
        longitude: lonNum,
        accuracy_meters: accuracy ? parseFloat(accuracy) : undefined,
        description,
        habitat_notes: habitatNotes || undefined,
        behavior_notes: behaviorNotes || undefined,
        identification_notes: identificationNotes || undefined,
        status: submitDirectly ? 'PENDING_REVIEW' : 'DRAFT',
      });

      // Upload photos if any
      if (selectedFiles.length > 0) {
        for (const file of selectedFiles) {
          try {
            await submissionService.uploadImage(created.id, file);
          } catch (uploadErr) {
            console.error('Failed to upload image', uploadErr);
          }
        }
      }

      setSuccessMsg(
        submitDirectly
          ? 'Observation submitted directly to Forest Officers for verification!'
          : 'Observation saved as a draft in your field station.'
      );

      setTimeout(() => {
        navigate('/my-submissions');
      }, 1500);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Submission failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-4 border-b border-[#e2ded5] pb-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 text-[#736f66] hover:text-[#1f1e1a] hover:bg-[#eae7df] rounded transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <div className="text-xs font-mono font-bold tracking-widest text-[#11682f] uppercase">
            Data Collection
          </div>
          <h1 className="text-2xl font-serif font-bold text-[#1f1e1a]">Field Observation / Incident Report</h1>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-[#fde8e7] border border-[#f5b8b5] text-[#932720] text-xs font-mono rounded flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-[#e7f6ed] border border-[#b8e5c8] text-[#11682f] text-xs font-mono rounded flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          {successMsg}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Form */}
        <div className="md:col-span-2 space-y-6">
          {/* Section 1: Species Selection */}
          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm space-y-4">
            <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase text-[#736f66]">
              <Compass className="w-4 h-4 text-[#11682f]" />
              Step 1: Taxonomic Identification
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#2c2b27] mb-1">
                Search Species (Common or Scientific Name) *
              </label>
              <input
                type="text"
                value={searchSpecies}
                onChange={(e) => setSearchSpecies(e.target.value)}
                placeholder="e.g. Bengal Tiger, Panthera tigris, King Cobra..."
                className="w-full px-3 py-2 text-sm border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
              />
            </div>

            {searchSpecies && filteredSpecies.length > 0 && (
              <div className="border border-[#e2ded5] rounded divide-y divide-[#f0ede6] max-h-48 overflow-y-auto bg-[#faf9f6]">
                {filteredSpecies.map((sp) => (
                  <button
                    key={sp.id}
                    type="button"
                    onClick={() => {
                      setSelectedSpeciesId(sp.id);
                      setSearchSpecies(`${sp.common_name} (${sp.scientific_name})`);
                    }}
                    className={`w-full text-left p-2.5 hover:bg-[#edeae1] transition-colors flex items-center justify-between text-xs ${
                      selectedSpeciesId === sp.id ? 'bg-[#d8f3e1] font-semibold' : ''
                    }`}
                  >
                    <div>
                      <div className="text-[#1f1e1a]">{sp.common_name}</div>
                      <div className="font-serif italic text-[#736f66]">{sp.scientific_name}</div>
                    </div>
                    {sp.iucn_category && (
                      <span className="font-mono text-[10px] px-1.5 py-0.5 bg-[#eae7df] rounded">
                        {sp.iucn_category}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Section 2: Spatial & Temporal Coordinates */}
          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase text-[#736f66]">
                <MapPin className="w-4 h-4 text-[#11682f]" />
                Step 2: Spatiotemporal Coordinates
              </div>
              <button
                type="button"
                onClick={handleUseCurrentLocation}
                className="text-[11px] font-mono font-bold text-[#11682f] hover:underline flex items-center gap-1"
              >
                Use GPS / Device Location
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[#2c2b27] mb-1">Latitude (DD) *</label>
                <input
                  type="text"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  placeholder="e.g. 21.6145"
                  className="w-full px-3 py-2 text-sm font-mono border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#2c2b27] mb-1">Longitude (DD) *</label>
                <input
                  type="text"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  placeholder="e.g. 88.0825"
                  className="w-full px-3 py-2 text-sm font-mono border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[#2c2b27] mb-1">Observed Timestamp *</label>
                <input
                  type="datetime-local"
                  value={observedAt}
                  onChange={(e) => setObservedAt(e.target.value)}
                  className="w-full px-3 py-2 text-sm font-mono border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#2c2b27] mb-1">Estimated GPS Accuracy (m)</label>
                <input
                  type="number"
                  value={accuracy}
                  onChange={(e) => setAccuracy(e.target.value)}
                  placeholder="e.g. 15"
                  className="w-full px-3 py-2 text-sm font-mono border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
                />
              </div>
            </div>
          </div>

          {/* Section 3: Field Notes */}
          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm space-y-4">
            <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase text-[#736f66]">
              <FileText className="w-4 h-4 text-[#11682f]" />
              Step 3: Field Description & Diagnostic Clues
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#2c2b27] mb-1">
                Field Description & Encounter Context *
              </label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Observed adult individual moving through riverine edge during morning transect..."
                className="w-full px-3 py-2 text-sm border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-[#2c2b27] mb-1">Habitat Notes</label>
                <input
                  type="text"
                  value={habitatNotes}
                  onChange={(e) => setHabitatNotes(e.target.value)}
                  placeholder="e.g. Moist deciduous forest canopy"
                  className="w-full px-3 py-2 text-sm border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#2c2b27] mb-1">Behavior Observed</label>
                <input
                  type="text"
                  value={behaviorNotes}
                  onChange={(e) => setBehaviorNotes(e.target.value)}
                  placeholder="e.g. Foraging, resting, vocalizing"
                  className="w-full px-3 py-2 text-sm border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#2c2b27] mb-1">Diagnostic Identification Clues</label>
              <input
                type="text"
                value={identificationNotes}
                onChange={(e) => setIdentificationNotes(e.target.value)}
                placeholder="e.g. Distinct white bib, stripe patterns, dorsal scale count"
                className="w-full px-3 py-2 text-sm border border-[#d6d2c7] rounded focus:outline-none focus:ring-1 focus:ring-[#11682f]"
              />
            </div>
          </div>
        </div>

        {/* Right Col: Photo Evidence & Actions */}
        <div className="space-y-6">
          <div className="bg-white p-5 rounded border border-[#e2ded5] shadow-sm space-y-4">
            <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase text-[#736f66]">
              <Camera className="w-4 h-4 text-[#11682f]" />
              Photo Evidence
            </div>

            <label className="border-2 border-dashed border-[#d6d2c7] hover:border-[#11682f] p-6 rounded cursor-pointer flex flex-col items-center justify-center text-center transition-colors bg-[#faf9f6]">
              <Upload className="w-8 h-8 text-[#736f66] mb-2" />
              <span className="text-xs font-mono font-bold text-[#1f1e1a]">Select Photos</span>
              <span className="text-[10px] text-[#736f66] mt-1">JPEG, PNG, WEBP (Max 10MB)</span>
              <input
                type="file"
                multiple
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files) {
                    setSelectedFiles(Array.from(e.target.files));
                  }
                }}
              />
            </label>

            {selectedFiles.length > 0 && (
              <div className="space-y-1.5 pt-2">
                <div className="text-[11px] font-mono font-bold uppercase text-[#736f66]">
                  {selectedFiles.length} file(s) selected:
                </div>
                {selectedFiles.map((f, i) => (
                  <div key={i} className="text-xs text-[#2c2b27] truncate bg-[#f0ede6] px-2 py-1 rounded">
                    {f.name} ({(f.size / 1024).toFixed(0)} KB)
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-[#f5f4ef] p-5 rounded border border-[#e2ded5] space-y-3">
            <div className="text-xs font-mono font-bold uppercase text-[#4d4a43]">
              Submission Action
            </div>
            <p className="text-[11px] text-[#736f66] leading-relaxed">
              Direct submission immediately notifies Forest Officers for peer verification and adds points to your researcher profile upon approval.
            </p>

            <button
              type="button"
              disabled={submitting}
              onClick={() => handleSubmit(true)}
              className="w-full py-2.5 bg-[#11682f] hover:bg-[#0e5426] text-white font-mono text-xs font-bold uppercase tracking-wider rounded transition-colors disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Submit For Review (+50 Pts)'}
            </button>

            <button
              type="button"
              disabled={submitting}
              onClick={() => handleSubmit(false)}
              className="w-full py-2 bg-white hover:bg-[#eae7df] border border-[#d6d2c7] text-[#2c2b27] font-mono text-xs font-bold uppercase tracking-wider rounded transition-colors disabled:opacity-50"
            >
              Save As Field Draft
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

