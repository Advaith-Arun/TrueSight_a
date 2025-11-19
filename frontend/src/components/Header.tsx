import { Search } from "lucide-react";

export const Header = () => {
  return (
    <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center gap-3">

          <Search className="w-8 h-8 text-primary icon-upload-pulse" />

          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-wider white-soft-glow">
              TrueSight | Forensic Digital Authenticator
            </h1>

            <p className="text-xs md:text-sm tracking-wide white-cyber-glow">
              Advanced AI-Powered Deepfake Detection & Forensic Analysis
            </p>
          </div>

        </div>
      </div>
    </header>
  );
};
