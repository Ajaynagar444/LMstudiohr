import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { resumeApi } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, ArrowRight, CheckCircle2, Loader2 } from 'lucide-react';

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const validateFile = (file) => {
    if (!file) return "No file selected";
    if (file.type !== "application/pdf") return "Only PDF allowed";
    if (file.size > 5 * 1024 * 1024) return "Max size 5MB";
    return null;
  };

  const handleUpload = async () => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setUploading(true);
    setError("");

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', 1);

    try {
      const res = await resumeApi.post('/analyze', formData);

      if (!res.data?.resume_id) {
        throw new Error("Invalid response from server");
      }

      navigate(`/interview/${res.data.resume_id}`);

    } catch (err) {
      console.error(err);
      setError("Failed to analyze resume. Try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 pt-24 pb-12 px-6">
      <div className="max-w-4xl mx-auto">

        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <h1 className="text-5xl font-bold text-white text-center mb-4">
            AI Interview
          </h1>
        </motion.div>

        <div
          className={`p-10 border-2 border-dashed rounded-2xl cursor-pointer ${
            file ? "border-indigo-500" : "border-gray-500"
          }`}
          onClick={() => !uploading && document.getElementById('fileInput').click()}
        >
          <input
            id="fileInput"
            type="file"
            hidden
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
          />

          <div className="text-center text-white">
            {file ? <CheckCircle2 size={40} /> : <Upload size={40} />}
            <p className="mt-2">
              {file ? file.name : "Upload Resume (PDF)"}
            </p>
          </div>
        </div>

        {error && (
          <p className="text-red-400 mt-4 text-center">{error}</p>
        )}

        <AnimatePresence>
          {file && (
            <motion.button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-6 px-6 py-3 bg-indigo-600 rounded-lg text-white w-full"
            >
              {uploading ? (
                <>
                  <Loader2 className="animate-spin inline mr-2" />
                  Processing...
                </>
              ) : (
                <>
                  Start Interview <ArrowRight className="inline ml-2" />
                </>
              )}
            </motion.button>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
}