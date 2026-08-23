import { AmbientBackground } from "@/components/home/AmbientBackground";
import { NavBar } from "@/components/dashboard/NavBar";
import { HeroSection } from "@/components/home/HeroSection";
import { PipelineSection } from "@/components/home/PipelineSection";
import { ArchitectureStory } from "@/components/home/ArchitectureStory";
import { ProductPreview } from "@/components/home/ProductPreview";
import { TimeMachinePreview } from "@/components/home/TimeMachinePreview";
import { FinalCTA } from "@/components/home/FinalCTA";

export default function HomePage() {
  return (
    <>
      <AmbientBackground />

      <div className="relative z-content min-h-screen">
        <NavBar />

        <main>
          <HeroSection />

          <div className="mx-auto max-w-shell px-5 sm:px-8">
            <hr className="border-border-subtle" />
          </div>

          <PipelineSection />

          <div className="mx-auto max-w-shell px-5 sm:px-8">
            <hr className="border-border-subtle" />
          </div>

          <ArchitectureStory />

          <div className="mx-auto max-w-shell px-5 sm:px-8">
            <hr className="border-border-subtle" />
          </div>

          <ProductPreview />

          <div className="mx-auto max-w-shell px-5 sm:px-8">
            <hr className="border-border-subtle" />
          </div>

          <TimeMachinePreview />

          <FinalCTA />
        </main>
      </div>
    </>
  );
}
