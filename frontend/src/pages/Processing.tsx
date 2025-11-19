import Galaxy from "@/components/Galaxy";
import { Header } from "@/components/Header";
import { useToast } from "@/hooks/use-toast";
import { api, StatusResponse } from "@/lib/api";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

const Processing = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [status, setStatus] = useState<StatusResponse | null>(null);

  useEffect(() => {
    if (!jobId) {
      navigate("/");
      return;
    }

    const pollStatus = async () => {
      try {
        const response = await api.getStatus(jobId);
        setStatus(response);

        if (response.status === "completed") {
          navigate(`/results/${jobId}`);
        } else if (response.status === "failed") {
          toast({
            title: "Analysis failed",
            description: response.error || "Video processing failed. Please try again.",
            variant: "destructive",
          });
        }
      } catch (error: any) {
        toast({
          title: "Error",
          description: "Failed to fetch status. Please try again.",
          variant: "destructive",
        });
      }
    };

    // Poll immediately
    pollStatus();

    // Set up polling interval (every 2 seconds)
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [jobId, navigate, toast]);

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
        transparent={false}
      />

      <Header />

      <main className="container mx-auto px-4 py-12 relative z-10">
        <div className="max-w-3xl mx-auto">
          <div className="bg-card border border-primary/30 rounded-lg p-8 shadow-card">
            <div className="text-center space-y-8">
              <div className="relative inline-block">
                <Loader2 className="w-24 h-24 text-red-500 spin-slow" />
                <div className="absolute inset-0 bg-gradient-radial from-red-500/20 to-transparent blur-xl" />
              </div>

              <div>
                <h2 className="text-2xl md:text-3xl font-bold text-white mb-4 upload-video-glow">
                  Analysis In Progress
                </h2>
                <p className="text-lg text-muted-foreground">
                  {status?.message || "Initializing video processing..."}
                </p>
              </div>

              <div className="text-sm text-muted-foreground space-y-2">
                <p>Job ID: <span className="text-foreground font-mono">{jobId}</span></p>
                <p className="text-xs">This page will automatically update when analysis is complete</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Processing;
