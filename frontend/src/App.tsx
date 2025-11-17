import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import GradCam from "./pages/GradCam";
import Home from "./pages/Home"; // ✅ ADD THIS
import JobHistory from "./pages/JobHistory";
import NotFound from "./pages/NotFound";
import Processing from "./pages/Processing";
import Results from "./pages/Results";
import Upload from "./pages/Upload";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />                    {/* ✅ CHANGED */}
          <Route path="/upload" element={<Upload />} />            {/* ✅ CHANGED */}
          <Route path="/processing/:jobId" element={<Processing />} />
          <Route path="/results/:jobId" element={<Results />} />
          <Route path="/gradcam/:jobId" element={<GradCam />} />
          <Route path="/history" element={<JobHistory />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
