import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";
import { api, JobSummary } from "@/lib/api";
import { AlertCircle, CheckCircle, Clock, Eye, Home, Upload } from "lucide-react"; // ✅ ADDED Home
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function JobHistory() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true);
        const data = await api.getAllJobs();
        setJobs(data.jobs);
      } catch (err: any) {
        const errorMessage = err.response?.data?.error || "Failed to load job history";
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

    fetchJobs();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
        <Header />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[80vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading analysis history...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-destructive mb-4">
                <AlertCircle className="h-6 w-6" />
                <h2 className="text-2xl font-bold">Error Loading History</h2>
              </div>
              <p className="text-muted-foreground mb-4">{error}</p>
              <Button onClick={() => navigate("/")}>
                <Home className="mr-2 h-4 w-4" />
                Back to Home
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
      <Header />
      <div className="container mx-auto px-4 py-8 space-y-6">
        {/* Header Section */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Analysis History</h1>
            <p className="text-muted-foreground mt-1">
              {jobs.length} completed {jobs.length === 1 ? 'analysis' : 'analyses'}
            </p>
          </div>
          <Button onClick={() => navigate("/")} size="lg">
            <Home className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
        </div>

        {/* Empty State */}
        {jobs.length === 0 ? (
          <Card>
            <CardContent className="pt-6 text-center py-12">
              <Clock className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
              <h2 className="text-2xl font-bold mb-2">No Analyses Yet</h2>
              <p className="text-muted-foreground mb-6">
                Upload your first video to see detection results here
              </p>
              <Button onClick={() => navigate("/upload")} size="lg">
                <Upload className="mr-2 h-4 w-4" />
                Upload First Video
              </Button>
            </CardContent>
          </Card>
        ) : (
          /* Job List */
          <div className="grid grid-cols-1 gap-4">
            {jobs.map((job) => {
              const isFake = job.verdict.toUpperCase() === "FAKE";
              return (
                <Card
                  key={job.job_id}
                  className={`cursor-pointer hover:border-primary transition-all hover:shadow-lg ${
                    isFake ? "border-l-4 border-l-red-500" : "border-l-4 border-l-green-500"
                  }`}
                  onClick={() => navigate(`/results/${job.job_id}`)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between gap-4">
                      {/* Icon and Info */}
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        {isFake ? (
                          <AlertCircle className="h-10 w-10 text-red-500 flex-shrink-0" />
                        ) : (
                          <CheckCircle className="h-10 w-10 text-green-500 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-semibold truncate">{job.filename}</h3>
                          <p className="text-sm text-muted-foreground">
                            {new Date(job.upload_timestamp).toLocaleString()} • {job.file_size_mb.toFixed(1)} MB
                          </p>
                        </div>
                      </div>

                      {/* Verdict Badge */}
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p
                            className={`text-xl font-bold ${
                              isFake ? "text-red-500" : "text-green-500"
                            }`}
                          >
                            {isFake ? "FAKE" : "REAL"}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            {(job.confidence * 100).toFixed(1)}% confidence
                          </p>
                        </div>

                        {/* View Button */}
                        <Button
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/results/${job.job_id}`);
                          }}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
