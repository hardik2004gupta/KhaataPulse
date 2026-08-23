import { api } from "./client";
import type { HeroCase, SimulationResponse } from "../types";

export const demoApi = {
  /** GET /demo/hero — deterministic hero case (no DB required) */
  getHeroCase(): Promise<HeroCase> {
    return api.get<HeroCase>("/demo/hero");
  },

  /** POST /demo/simulate — full pipeline steps for live animation */
  runSimulation(): Promise<SimulationResponse> {
    return api.post<SimulationResponse>("/demo/simulate");
  },
};
