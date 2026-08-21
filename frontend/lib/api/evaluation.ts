import { api } from "./client";
import type {
  EvaluationRunResponse,
  EvaluationRunRecord,
  MultiSeedResponse,
} from "../types";

export const evaluationApi = {
  /** POST /evaluation/run — trigger one evaluation run */
  runEvaluation(seed: number, cohortSize: number): Promise<EvaluationRunResponse> {
    return api.post<EvaluationRunResponse>("/evaluation/run", {
      seed,
      cohort_size: cohortSize,
    });
  },

  /** POST /evaluation/run/multi-seed */
  runMultiSeed(cohortSize: number, seeds: number[]): Promise<MultiSeedResponse> {
    return api.post<MultiSeedResponse>("/evaluation/run/multi-seed", {
      cohort_size: cohortSize,
      seeds,
    });
  },

  /** GET /evaluation/run/{run_id} */
  getRun(runId: string): Promise<EvaluationRunResponse> {
    return api.get<EvaluationRunResponse>(`/evaluation/run/${runId}`);
  },

  /** GET /evaluation/runs */
  listRuns(limit = 20): Promise<EvaluationRunRecord[]> {
    return api.get<EvaluationRunRecord[]>(`/evaluation/runs?limit=${limit}`);
  },
};
