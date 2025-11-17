import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Eye, History, Shield, Upload, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-3 mb-6">
            <Shield className="h-16 w-16 text-primary" />
          </div>
          <h1 className="text-5xl font-black tracking-tight">
            True<span className="text-primary">Sight</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Advanced deepfake detection powered by ensemble deep learning and Grad-CAM visualization
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="border-border/50 bg-zinc-900/50">
            <CardContent className="pt-6 text-center">
              <Eye className="h-8 w-8 text-primary mx-auto mb-3" />
              <h3 className="font-semibold mb-2">AI-Powered Detection</h3>
              <p className="text-sm text-muted-foreground">
                Multi-model ensemble for accurate deepfake identification
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-zinc-900/50">
            <CardContent className="pt-6 text-center">
              <Zap className="h-8 w-8 text-primary mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Explainable AI</h3>
              <p className="text-sm text-muted-foreground">
                Grad-CAM visualizations show exactly what the AI sees
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-zinc-900/50">
            <CardContent className="pt-6 text-center">
              <History className="h-8 w-8 text-primary mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Analysis History</h3>
              <p className="text-sm text-muted-foreground">
                Track and review all your previous deepfake analyses
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            size="lg"
            onClick={() => navigate("/upload")}
            className="text-lg px-8 py-6"
          >
            <Upload className="mr-2 h-5 w-5" />
            Upload New Video
          </Button>

          <Button
            size="lg"
            variant="outline"
            onClick={() => navigate("/history")}
            className="text-lg px-8 py-6"
          >
            <History className="mr-2 h-5 w-5" />
            View Analysis History
          </Button>
        </div>

        {/* Footer Info */}
        <div className="text-center text-sm text-muted-foreground space-y-2">
          <p>Supports MP4, AVI, and MOV formats • Maximum file size: 500 MB</p>
        </div>
      </div>
    </div>
  );
}
