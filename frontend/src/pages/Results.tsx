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

  useEffect(() => {
    const fetchResults = async () => {
      if (!jobId) {
        setError("No job ID provided");
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
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
      <Header />
      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Verdict Banner */}
        <div
          className={`relative overflow-hidden rounded-lg p-8 text-center ${
            isFake
              ? "bg-gradient-to-r from-red-900/50 to-red-800/50 border-2 border-red-500"
              : "bg-gradient-to-r from-green-900/50 to-green-800/50 border-2 border-green-500"
          }`}
        >
          <div className="flex items-center justify-center gap-4 mb-4">
            {isFake ? (
              <AlertCircle className="h-16 w-16 text-red-500" />
            ) : (
              <CheckCircle className="h-16 w-16 text-green-500" />
            )}
          </div>
          <h2 className="text-4xl font-black uppercase tracking-wider mb-2">
            {isFake ? "DEEPFAKE DETECTED" : "AUTHENTIC VIDEO"}
          </h2>
          <p className="text-2xl font-bold">
            Confidence: {(results.confidence * 100).toFixed(2)}%
          </p>
        </div>

        <h1 className="text-3xl font-bold text-center">Analysis Report</h1>

        {/* Overall Prediction */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Overall Prediction
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Fake Probability</span>
                  <span className="font-bold text-red-500">
                    {(fakeProb * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-500"
                    style={{ width: `${fakeProb * 100}%` }}
                  ></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Real Probability</span>
                  <span className="font-bold text-green-500">
                    {(realProb * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500"
                    style={{ width: `${realProb * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Processing Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Processing Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Filename</p>
                <p className="font-semibold">{results.filename}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">File Size</p>
                <p className="font-semibold">{results.file_size_mb.toFixed(2)} MB</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Processing Time</p>
                <p className="font-semibold">{results.processing_time_seconds.toFixed(2)}s</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Job ID</p>
                <p className="font-mono text-xs">{results.job_id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Upload Time</p>
                <p className="font-semibold">
                  {new Date(results.upload_timestamp).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Frames Analyzed</p>
                <p className="font-semibold">{results.gradcam_frame_count}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4">
          {results.gradcam_enabled && (
            <Button 
              size="lg" 
              onClick={() => navigate(`/gradcam/${jobId}`)}
              variant="default"
            >
              <Eye className="mr-2 h-4 w-4" />
              View Grad-CAM Visualizations
            </Button>
          )}
          

          <Button size="lg" onClick={() => navigate("/")} variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
        </div>
      </div>
    </div>
  );
}
