// Smoke-test script for the Dida365/TickTick OpenAPI endpoints used by this repo.
//
// Usage:
//   DIDA_ACCESS_TOKEN=... node scripts/smoke_completed_tasks.mjs <projectId>
//
// Optional env:
//   DIDA_BASE_URL=https://api.dida365.com/open/v1
//
// Notes:
// - Official GET /project/{id}/data typically returns only active (uncompleted) tasks.
// - Completed tasks are available at GET /project/{id}/task/completed (underdocumented).

const baseUrl = String(process.env.DIDA_BASE_URL || "https://api.dida365.com/open/v1").replace(/\/+$/, "");
const token = process.env.DIDA_ACCESS_TOKEN;
const projectId = process.argv[2];

if (!token) {
  console.error("Missing env: DIDA_ACCESS_TOKEN");
  process.exit(2);
}
if (!projectId) {
  console.error("Usage: node scripts/smoke_completed_tasks.mjs <projectId>");
  process.exit(2);
}

async function hit(endpoint) {
  const url = baseUrl + "/" + endpoint.replace(/^\/+/, "");
  const res = await fetch(url, {
    headers: {
      Authorization: "Bearer " + token,
      Accept: "application/json"
    }
  });

  const text = await res.text();
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = null;
  }

  const len = Array.isArray(json)
    ? json.length
    : json && Array.isArray(json.tasks)
      ? json.tasks.length
      : null;

  console.log(endpoint + " -> status=" + res.status + " bodyLen=" + (text ? text.length : 0) + " items=" + (len === null ? "n/a" : String(len)));
}

await hit("project/" + projectId + "/data");
await hit("project/" + projectId + "/task/completed");
