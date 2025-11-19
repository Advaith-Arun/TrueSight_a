import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { CloudUpload, Upload, X, CheckCircle2 } from "lucide-react";
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
    <div className="w-full space-y-6">
      {/* Upload Zone - Glassmorphic */}
      <div
        className={`relative group rounded-2xl overflow-hidden backdrop-blur-xl transition-all duration-500 ${
          isDragging
            ? 'bg-red-500/20 border border-red-500/40 shadow-lg shadow-red-500/20'
            : 'bg-white/5 border border-white/10 hover:border-white/20 hover:bg-white/8 shadow-lg shadow-black/20'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Gradient accent on hover */}
        <div className="absolute inset-0 bg-gradient-to-br from-red-500/0 to-red-500/0 group-hover:from-red-500/5 group-hover:to-transparent transition-all duration-500 pointer-events-none"></div>

        <input
          type="file"
          id="video-upload"
          className="hidden"
          accept=".mp4,.avi,.mov,video/mp4,video/avi,video/quicktime"
          onChange={handleInputChange}
          disabled={isUploading}
        />

        <div className="relative p-12 md:p-16 text-center">
          {/* Icon with subtle animation */}
          <div className="flex justify-center mb-6">
            <div className={`transition-all duration-500 ${
              isDragging ? 'scale-110 text-red-500' : 'text-zinc-500 group-hover:text-white'
            }`}>
              <CloudUpload className="w-20 h-20" strokeWidth={1.2} />
            </div>
          </div>

          {/* Text hierarchy - typography weight and opacity */}
          <div className="space-y-3">
            <h3 className="text-2xl font-semibold text-white tracking-tight">
              {isDragging ? 'Drop your video here' : 'Choose a video to analyze'}
            </h3>
            <p className="text-zinc-400 text-base leading-relaxed max-w-md mx-auto">
              {isDragging
                ? 'We\'re ready to receive your file'
                : 'Drag and drop MP4, AVI, or MOV • Maximum 500MB'}
            </p>
          </div>

          {/* Browse button - pill shaped with intentional hover */}
          <label htmlFor="video-upload" className="inline-block mt-8">
            <Button
              type="button"
              variant="outline"
              disabled={isUploading}
              onClick={(e) => {
                e.preventDefault();
                document.getElementById('video-upload')?.click();
              }}
              className="rounded-full px-8 py-6 text-base font-medium border border-white/20 hover:border-white/40 text-white hover:bg-white/10 transition-all duration-300 flex items-center gap-2"
            >
              <Upload className="w-5 h-5" strokeWidth={1.5} />
              Browse Files
            </Button>
          </label>
        </div>
      </div>

      {/* File preview - Layered glassmorphic panel */}
      {selectedFile && (
        <div className="rounded-2xl backdrop-blur-xl bg-white/5 border border-white/10 overflow-hidden shadow-lg shadow-black/20 transition-all duration-300 animate-in fade-in slide-in-from-bottom-4">
          {/* File info section */}
          <div className="p-6 md:p-8">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-4 flex-1 min-w-0">
                {/* Status indicator */}
                <div className="mt-1 flex-shrink-0">
                  <CheckCircle2 className="w-6 h-6 text-green-500" strokeWidth={1.5} />
                </div>

                {/* File details with typography hierarchy */}
                <div className="flex-1 min-w-0">
                  <p className="text-lg font-semibold text-white truncate tracking-tight">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-zinc-400 mt-1 font-medium tracking-wide">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
              </div>

              {/* Clear button - subtle and responsive */}
              <Button
                variant="ghost"
                size="icon"
                onClick={clearFile}
                disabled={isUploading}
                className="rounded-full text-zinc-400 hover:text-red-500 hover:bg-red-500/10 transition-colors duration-300 flex-shrink-0"
              >
                <X className="w-5 h-5" strokeWidth={1.5} />
              </Button>
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-gradient-to-r from-white/0 via-white/10 to-white/0"></div>

          {/* Action section */}
          <div className="p-6 md:p-8">
            <Button
              onClick={handleUpload}
              disabled={isUploading}
              className="w-full h-12 rounded-full bg-red-500 hover:bg-red-600 text-white font-semibold text-base tracking-wide transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isUploading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" strokeWidth={1.5} />
                  <span>Begin Analysis</span>
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
