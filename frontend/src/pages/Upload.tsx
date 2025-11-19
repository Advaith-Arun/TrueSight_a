import { FileUpload } from "@/components/FileUpload";
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

      {/* 🔳 Subtle cyber grid */}
      <div className="absolute inset-0 cyber-grid pointer-events-none"></div>

      {/* 🔺 Pulsating red cyber squares */}
      <div className="absolute top-6 right-6 w-28 h-28 border-2 border-primary opacity-20 animate-pulse rounded-md"></div>
      <div className="absolute bottom-6 left-6 w-20 h-20 border border-primary opacity-15 animate-pulse rounded-sm"></div>

      <Header />

      <div className="container mx-auto px-4 py-8 relative z-10">

        {/* 🔙 Back button with glow */}
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="mb-4 white-cyber-glow"
        >
          <ArrowLeft className="mr-2 h-4 w-4 icon-pulse-soft" />
          Back to Home
        </Button>

        {/* Title + subtitle */}
        <div className="max-w-2xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2 red-soft-glow">
              New Analysis Request
            </h1>

            <p className="text-muted-foreground white-soft-glow">
              Upload a video file to begin deepfake detection analysis
            </p>
          </div>

          {/* Upload Box */}
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
