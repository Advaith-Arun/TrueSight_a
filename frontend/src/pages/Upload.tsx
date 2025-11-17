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

      // Navigate to processing page
      navigate(`/processing/${response.job_id}`);
    } catch (error: any) {
      toast({
        title: "Upload failed",
        description: error.response?.data?.error || "Failed to upload video. Please try again.",
        variant: "destructive",
      });
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
      <Header />
      <div className="container mx-auto px-4 py-8">
        {/* ✅ BACK TO HOME BUTTON */}
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Home
        </Button>

        <div className="max-w-2xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">New Analysis Request</h1>
            <p className="text-muted-foreground">
              Upload a video file to begin deepfake detection analysis
            </p>
          </div>

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
