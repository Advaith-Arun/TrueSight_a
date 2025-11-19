import Galaxy from "@/components/Galaxy";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { toast } from "@/hooks/use-toast";
import { api, ResultsResponse } from "@/lib/api";
import { ArrowLeft, FileText, Pause, Play } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

export default function GradCam() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Frame scrubber state
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

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

  // Auto-play frame scrubber
  useEffect(() => {
    if (!isPlaying || !results) return;

    const interval = setInterval(() => {
      setCurrentFrame((prev) => {
        if (prev >= results.gradcam_frame_count - 1) {
          setIsPlaying(false);
          return 0;
        }
        return prev + 1;
      });
    }, 500); // 500ms per frame

    return () => clearInterval(interval);
  }, [isPlaying, results]);

  if (loading) {
    return (
      <div className="min-h-screen relative overflow-hidden bg-black">
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
        <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[80vh] relative z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading Grad-CAM visualizations...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="min-h-screen relative overflow-hidden bg-black">
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
        <div className="container mx-auto px-4 py-8 relative z-10">
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <p className="text-muted-foreground mb-4">{error || "Grad-CAM data not found"}</p>
              <Button onClick={() => navigate(`/results/${jobId}`)}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Results
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!results.gradcam_enabled) {
    return (
      <div className="min-h-screen relative overflow-hidden bg-black">
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
        <div className="container mx-auto px-4 py-8 relative z-10">
          <Card>
            <CardContent className="pt-6">
              <p className="text-muted-foreground mb-4">
                Grad-CAM visualizations are not available for this analysis.
              </p>
              <Button onClick={() => navigate(`/results/${jobId}`)}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Results
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const getCurrentFrameFilename = () => {
    return `frame_${String(currentFrame).padStart(3, '0')}_overlay.jpg`;
  };

  const avgHeatmap = results.gradcam_avg_heatmap ? results.gradcam_avg_heatmap.split('/').pop() : '';

  return (
    <div className="min-h-screen relative overflow-hidden bg-black">
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
      <div className="container mx-auto px-4 py-8 space-y-8 relative z-10">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold upload-video-glow"><span className="text-white">Grad-CAM</span> <span className="text-red-500 ml-3">Forensic</span> <span className="text-white">Visualizations</span></h1>
          <Button onClick={() => navigate(`/results/${jobId}`)} variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Results
          </Button>
        </div>

        {/* Frame Scrubber */}
        {results.gradcam_frame_count > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Interactive Frame Scrubber
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Current Frame Display - WITH SIZING FIX */}
              <div className="relative bg-zinc-900 rounded-lg p-4">
                <img
                  src={api.getGradCamUrl(results.job_id, getCurrentFrameFilename())}
                  alt={`Frame ${currentFrame}`}
                  className="w-full max-w-4xl mx-auto rounded-lg border-2 border-border object-contain"
                  style={{ maxHeight: '600px' }}
                  onError={(e) => {
                    console.error('Image failed to load:', getCurrentFrameFilename());
                    e.currentTarget.src = 'https://via.placeholder.com/800x450?text=Frame+Not+Found';
                  }}
                />
                <div className="absolute top-8 left-8 bg-black/80 px-4 py-2 rounded-lg backdrop-blur-sm">
                  <span className="text-sm font-mono text-white font-semibold">
                    Frame {currentFrame + 1} / {results.gradcam_frame_count}
                  </span>
                </div>
              </div>

              {/* Controls */}
              <div className="space-y-4">
                {/* Play/Pause Button */}
                <div className="flex justify-center">
                  <Button
                    onClick={() => setIsPlaying(!isPlaying)}
                    variant={isPlaying ? "destructive" : "default"}
                    size="lg"
                  >
                    {isPlaying ? (
                      <>
                        <Pause className="mr-2 h-4 w-4" />
                        Pause
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Play
                      </>
                    )}
                  </Button>
                </div>

                {/* Slider */}
                <div className="px-4">
                  <Slider
                    value={[currentFrame]}
                    onValueChange={(value) => {
                      setCurrentFrame(value[0]);
                      setIsPlaying(false);
                    }}
                    max={results.gradcam_frame_count - 1}
                    step={1}
                    className="w-full"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Average Heatmap - WITH SIZING FIX */}
        {avgHeatmap && (
          <Card>
            <CardHeader>
              <CardTitle>Average Attention Heatmap</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-zinc-900 rounded-lg p-4">
                <img
                  src={api.getGradCamUrl(results.job_id, avgHeatmap)}
                  alt="Average heatmap"
                  className="w-full max-w-3xl mx-auto rounded-lg border border-border object-contain"
                  style={{ maxHeight: '500px' }}
                  onError={(e) => {
                    console.error('Average heatmap failed to load');
                    e.currentTarget.src = 'https://via.placeholder.com/800x450?text=Heatmap+Not+Found';
                  }}
                />
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
