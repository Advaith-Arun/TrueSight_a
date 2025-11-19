import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { CloudUpload, Upload, X } from "lucide-react";
import { useCallback, useState } from "react";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isUploading: boolean;
}

export const FileUpload = ({ onFileSelect, isUploading }: FileUploadProps) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const { toast } = useToast();

  const validateFile = (file: File): boolean => {
    const validTypes = ['video/mp4', 'video/avi', 'video/x-msvideo', 'video/quicktime'];
    const maxSize = 500 * 1024 * 1024; // 500MB

    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov)$/i)) {
      toast({
        title: "Invalid file type",
        description: "Please upload a video file (MP4, AVI, MOV)",
        variant: "destructive",
      });
      return false;
    }

    if (file.size > maxSize) {
      toast({
        title: "File too large",
        description: "Maximum file size is 500MB",
        variant: "destructive",
      });
      return false;
    }

    return true;
  };

  const handleFileChange = useCallback((file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
    }
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileChange(file);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileChange(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(2)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 transition-all ${isDragging
          ? "border-primary bg-primary/10 shadow-red-glow"
          : "border-border/50 hover:border-primary/50"
          }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="video-upload"
          className="hidden"
          accept=".mp4,.avi,.mov,video/mp4,video/avi,video/quicktime"
          onChange={handleInputChange}
          disabled={isUploading}
        />

        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <CloudUpload className="w-16 h-16 text-primary/70 icon-upload-pulse" />

          </div>

          <div>
            <h3 className="text-lg font-semibold text-foreground mb-2 red-soft-glow">

              Upload Video (MP4, AVI, MOV)
            </h3>
            <p className="text-sm text-muted-foreground">
              Drag and drop file here
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Limit 500MB per file • MP4, AVI, MOV, MPEG4
            </p>
          </div>

          <label htmlFor="video-upload">
            <Button
              type="button"
              variant="outline"
              className="border-primary text-primary hover:bg-primary hover:text-primary-foreground white-soft-glow"
              disabled={isUploading}
              onClick={() => document.getElementById('video-upload')?.click()}
            >
              <Upload className="w-4 h-4 mr-2" />
              Browse files
            </Button>
          </label>
        </div>
      </div>

      {selectedFile && (
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="font-medium text-foreground">{selectedFile.name}</p>
              <p className="text-sm text-muted-foreground">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={clearFile}
              disabled={isUploading}
              className="text-muted-foreground hover:text-destructive"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          <Button
            className="w-full mt-4 bg-primary hover:bg-primary/90 text-primary-foreground font-bold uppercase tracking-wider"
            onClick={handleUpload}
            disabled={isUploading}
            size="lg"
          >
            {isUploading ? (
              <>
                <Upload className="w-4 h-4 mr-2 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Initiate Analysis
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
};
