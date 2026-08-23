import { api } from "./client";
import type { CasesListResponse } from "../types";

export const casesApi = {
  /**
   * GET /cases/ - requested without the trailing slash so it matches the
   * dedicated `/api/cases` rewrite, which restores the slash the backend needs.
   */
  listCases(limit = 50, offset = 0): Promise<CasesListResponse> {
    return api.get<CasesListResponse>(`/cases?limit=${limit}&offset=${offset}`);
  },

  /** GET /cases/{case_id} */
  getCase(caseId: number): Promise<unknown> {
    return api.get(`/cases/${caseId}`);
  },
};
