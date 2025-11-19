import Galaxy from "@/components/Galaxy";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";
import { api, ResultsResponse } from "@/lib/api";
import { Activity, AlertCircle, ArrowLeft, CheckCircle, Clock, Eye } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

export default function Results() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data for frontend preview
  const mockResults: ResultsResponse = {
    job_id: "mock_job_001",
    filename: "sample_video.mp4",
    status: "completed",
    verdict: "FAKE",
    confidence: 0.92,
    probability: 0.87,
    file_size_mb: 125.5,
    processing_time_seconds: 45.23,
    upload_timestamp: new Date().toISOString(),
    completion_timestamp: new Date().toISOString(),
    gradcam_enabled: true,
    gradcam_frame_count: 24,
    gradcam_avg_heatmap: "/heatmap.jpg",
    gradcam_dir: "/gradcam_frames",
    threshold: 0.5,
    error_message: null,
  };

  useEffect(() => {
    const fetchResults = async () => {
      if (!jobId) {
        // Use mock data for frontend preview
        setResults(mockResults);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await api.getResults(jobId);
        setResults(data);
      } catch (err: any) {
        const errorMessage = err.response?.data?.error || "Failed to load results";
        setError(errorMessage);
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [jobId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
        <Header />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[80vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading results...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-destructive mb-4">
                <AlertCircle className="h-6 w-6" />
                <h2 className="text-2xl font-bold">Error Loading Results</h2>
              </div>
              <p className="text-muted-foreground mb-4">{error || "Results not found"}</p>
              <Button onClick={() => navigate("/")}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Upload
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const fakeProb = results.probability;
  const realProb = 1.0 - fakeProb;
  const isFake = results.verdict.toUpperCase() === "FAKE";

  return (
    <div className="min-h-screen relative overflow-hidden bg-black">
      {/* Galaxy background */}
      <Galaxy
        mouseInteraction={false}
        mouseRepulsion={false}
        hueShift={0}
        density={0.8}
        glowIntensity={0.4}
        saturation={1.0}
        speed={0.8}
        twinkleIntensity={0.4}
      />

      <Header />
      <div className="container mx-auto px-4 py-12 max-w-4xl relative z-10">
        {/* Verdict Banner */}
        <div
          className={`relative overflow-hidden rounded-3xl p-8 text-center backdrop-blur-xl border mb-12 ${isFake
            ? "bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/30 shadow-lg shadow-red-500/10"
            : "bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/30 shadow-lg shadow-green-500/10"
            }`}
        >
          <div className="flex items-center justify-center gap-4 mb-4">
            {isFake ? (
              <AlertCircle className="h-16 w-16 text-red-400" />
            ) : (
              <CheckCircle className="h-16 w-16 text-green-400" />
            )}
          </div>
          <h2 className={`text-5xl font-black uppercase tracking-wider mb-2 ${isFake ? "text-red-400" : "text-green-400"}`}>
            {isFake ? "DEEPFAKE DETECTED" : "AUTHENTIC VIDEO"}
          </h2>
          <p className={`text-xl font-bold ${isFake ? "text-red-300" : "text-green-300"}`}>
            Confidence: {(results.confidence * 100).toFixed(2)}%
          </p>
        </div>

        <h1 className="text-4xl font-black tracking-tight mb-8 text-center">
          <span className="text-white">Analysis </span>
          <span className="text-red-500">Report</span>
        </h1>

        {/* Overall Prediction */}
        <Card className="backdrop-blur-xl bg-white/5 border-white/10 shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Activity className="h-5 w-5 text-red-400" />
              Overall Prediction
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Fake Probability</span>
                  <span className="font-bold text-red-400">
                    {(fakeProb * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="h-3 bg-white/10 rounded-full overflow-hidden border border-white/5">
                  <div
                    className="h-full bg-gradient-to-r from-red-500 to-red-400"
                    style={{ width: `${fakeProb * 100}%` }}
                  ></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Real Probability</span>
                  <span className="font-bold text-green-400">
                    {(realProb * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="h-3 bg-white/10 rounded-full overflow-hidden border border-white/5">
                  <div
                    className="h-full bg-gradient-to-r from-green-500 to-green-400"
                    style={{ width: `${realProb * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Processing Metrics */}
        <Card className="backdrop-blur-xl bg-white/5 border-white/10 shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Clock className="h-5 w-5 text-red-400" />
              Processing Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Filename</p>
                <p className="font-semibold text-white">{results.filename}</p>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">File Size</p>
                <p className="font-semibold text-white">{results.file_size_mb.toFixed(2)} MB</p>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Processing Time</p>
                <p className="font-semibold text-white">{results.processing_time_seconds.toFixed(2)}s</p>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Job ID</p>
                <p className="font-mono text-xs text-gray-300">{results.job_id}</p>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Upload Time</p>
                <p className="font-semibold text-white text-sm">
                  {new Date(results.upload_timestamp).toLocaleString()}
                </p>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Frames Analyzed</p>
                <p className="font-semibold text-white">{results.gradcam_frame_count}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4 pt-4">
          {results.gradcam_enabled && (
            <Button
              size="lg"
              onClick={() => navigate(`/gradcam/${jobId}`)}
              className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-bold rounded-full px-8"
            >
              <Eye className="mr-2 h-4 w-4" />
              View Grad-CAM Visualizations
            </Button>
          )}

          <Button
            size="lg"
            onClick={() => navigate("/")}
            className="bg-white/10 hover:bg-white/20 text-white font-bold rounded-full px-8 border border-white/20 backdrop-blur-xl"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
        </div>
      </div>
    </div>
  );
}
