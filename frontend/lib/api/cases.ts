import { api } from "./client";
import type { CasesListResponse } from "../types";

export const casesApi = {
  /** GET /cases/ */
  listCases(limit = 50, offset = 0): Promise<CasesListResponse> {
    return api.get<CasesListResponse>(`/cases/?limit=${limit}&offset=${offset}`);
  },

  /** GET /cases/{case_id} */
  getCase(caseId: number): Promise<unknown> {
    return api.get(`/cases/${caseId}`);
  },
};
