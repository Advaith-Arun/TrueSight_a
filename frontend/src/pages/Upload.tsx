import { FileUpload } from "@/components/FileUpload";
import Galaxy from "@/components/Galaxy";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import { ArrowLeft } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const Upload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleFileSelect = async (file: File) => {
    setIsUploading(true);

    try {
      const response = await api.uploadVideo(file);

      toast({
        title: "Upload successful",
        description: response.message,
      });

      navigate(`/processing/${response.job_id}`);
    } catch (error: any) {
      toast({
        title: "Upload failed",
        description:
          error.response?.data?.error ||
          "Failed to upload video. Please try again.",
        variant: "destructive",
      });
      setIsUploading(false);
    }
  };

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

      <div className="container mx-auto px-4 py-12 relative z-10">
        {/* Back button - subtle and intentional */}
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="mb-12 text-zinc-300 hover:text-white transition-colors duration-300 flex items-center gap-2 text-sm font-medium tracking-wide"
        >
          <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
          <span>Return</span>
        </Button>

        {/* Glassmorphic header section */}
        <div className="max-w-3xl mx-auto mb-12">
          <div className="space-y-4">
            <h1 className="text-3xl md:text-4xl font-black tracking-tight upload-video-glow">
              <span className="text-white">Upload</span>
              <span className="text-red-500 ml-3">Video</span>
            </h1>
            <p className="text-lg text-zinc-400 max-w-xl leading-relaxed tracking-wide">
              Submit your video for advanced deepfake detection analysis. Our ensemble model will identify and visualize suspicious regions with precision.
            </p>
          </div>
        </div>

        {/* Content wrapper with layered glassmorphism */}
        <div className="max-w-3xl mx-auto">
          <FileUpload
            onFileSelect={handleFileSelect}
            isUploading={isUploading}
          />
        </div>
      </div>
    </div>
  );
};

export default Upload;
