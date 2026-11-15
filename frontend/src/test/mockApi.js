// mockApi.js — a fake Axios instance for page tests: route GET/POST/PUT/DELETE by URL to canned replies.
import { vi } from "vitest";

// routes: { "GET /ta/subjects": data | (config) => data, ... }
export function makeApi(routes = {}) {
  const call = (method) => vi.fn(async (url, bodyOrConfig, config) => {
    const key = `${method} ${url}`;
    if (!(key in routes)) throw Object.assign(new Error(`no mock for ${key}`), { response: { status: 404, data: {} } });
    const r = routes[key];
    const data = typeof r === "function" ? r(bodyOrConfig, config) : r;
    return { data };
  });
  return { get: call("GET"), post: call("POST"), put: call("PUT"), delete: call("DELETE"), routes };
}
