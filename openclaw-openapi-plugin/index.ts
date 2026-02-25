import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_BASE_URL = "https://api.dida365.com/open/v1";
const DEFAULT_AUTH_URL = "https://dida365.com/oauth/authorize";
const DEFAULT_TOKEN_URL = "https://dida365.com/oauth/token";
const DEFAULT_TIMEOUT_MS = 15000;
const PLUGIN_ID = "dida-openapi";

const state: {
  clientId?: string;
  clientSecret?: string;
  redirectUri?: string;
  accessToken?: string;
  refreshToken?: string;
} = {};

type ToolDef = {
  name: string;
  description: string;
  parameters: Record<string, any>;
  run: (api: any, params: Record<string, any>) => Promise<any>;
};

export default function register(api: any) {
  registerTools(api);
}

function registerTools(api: any) {
  registerTool(api, {
    name: "dida_auth_url",
    description: "生成滴答清单 OAuth 授权链接（首次绑定或 token 失效时使用）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        state: { type: "string", description: "可选 state 参数" },
        scope: { type: "string", description: "可选 scope 参数" },
        redirect_uri: { type: "string", description: "可选 redirect_uri，默认使用配置" }
      }
    },
    run: async (api, params) => buildAuthUrl(api, params)
  });

  registerTool(api, {
    name: "dida_exchange_code",
    description: "使用授权码换取 access_token/refresh_token，并用于后续所有滴答工具调用。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        code: { type: "string", description: "授权码 code" },
        redirect_uri: { type: "string", description: "可选 redirect_uri，默认使用配置" }
      },
      required: ["code"]
    },
    run: async (api, params) => exchangeCode(api, params)
  });

  registerTool(api, {
    name: "dida_refresh_token",
    description: "刷新 access_token（401/过期时使用）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        refresh_token: { type: "string", description: "可选 refresh_token，默认使用配置" }
      }
    },
    run: async (api, params) => refreshToken(api, params)
  });

  registerTool(api, {
    name: "dida_get_projects",
    description: "获取滴答清单项目列表。用户问“有几个项目/项目数量”时应优先调用本工具。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {}
    },
    run: async (api) => didaRequest(api, "GET", "project")
  });

  registerTool(api, {
    name: "dida_create_project",
    description: "创建滴答清单项目（至少提供 name）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        name: { type: "string", description: "项目名称" },
        color: { type: "string", description: "项目颜色，如 #FF0000" },
        view_mode: { type: "string", description: "视图模式" },
        kind: { type: "string", description: "项目类型" },
        sort_order: { type: "integer", description: "排序" }
      },
      required: ["name"]
    },
    run: async (api, params) => createProject(api, params)
  });

  registerTool(api, {
    name: "dida_update_project",
    description: "更新滴答清单项目（按 project_id_or_name 精确定位）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        project_id_or_name: { type: "string", description: "项目ID或名称" },
        name: { type: "string", description: "新项目名称" },
        color: { type: "string", description: "新项目颜色" },
        view_mode: { type: "string", description: "视图模式" },
        kind: { type: "string", description: "项目类型" },
        sort_order: { type: "integer", description: "排序" }
      },
      required: ["project_id_or_name"]
    },
    run: async (api, params) => updateProject(api, params)
  });

  registerTool(api, {
    name: "dida_delete_project",
    description: "删除滴答清单项目（按 project_id_or_name）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        project_id_or_name: { type: "string", description: "项目ID或名称" }
      },
      required: ["project_id_or_name"]
    },
    run: async (api, params) => deleteProject(api, params)
  });

  registerTool(api, {
    name: "dida_get_tasks",
    description:
      "查询任务列表（支持 mode/project_name/keyword/priority/completed 过滤）。用户问“今天任务/最近任务/某项目任务”时优先调用。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        mode: {
          type: "string",
          description: "任务模式：all/today/yesterday/recent_7_days",
          enum: ["all", "today", "yesterday", "recent_7_days"]
        },
        keyword: { type: "string", description: "关键词筛选" },
        priority: { type: "integer", description: "优先级：0/1/3/5", enum: [0, 1, 3, 5] },
        project_name: { type: "string", description: "项目名称筛选" },
        completed: { type: "boolean", description: "是否已完成" }
      }
    },
    run: async (api, params) => getTasks(api, params)
  });

  registerTool(api, {
    name: "tt_task_list",
    description: "dida_get_tasks 的英文别名（today/project/keyword 场景）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        mode: {
          type: "string",
          description: "task mode: all/today/yesterday/recent_7_days",
          enum: ["all", "today", "yesterday", "recent_7_days"]
        },
        keyword: { type: "string", description: "keyword filter" },
        priority: { type: "integer", description: "priority: 0/1/3/5", enum: [0, 1, 3, 5] },
        project_name: { type: "string", description: "project name filter" },
        completed: { type: "boolean", description: "completed?" }
      }
    },
    run: async (api, params) => getTasks(api, params)
  });

  registerTool(api, {
    name: "dida_create_task",
    description: "创建任务（title 必填；可选 due/start/project/priority 等）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        title: { type: "string", description: "任务标题" },
        content: { type: "string", description: "任务内容" },
        priority: { type: "integer", description: "优先级：0/1/3/5", enum: [0, 1, 3, 5] },
        project_name: { type: "string", description: "项目名称" },
        tag_names: { type: "array", items: { type: "string" }, description: "标签名称列表（官方 API 暂不支持）" },
        start_date: { type: "string", description: "开始时间，YYYY-MM-DD HH:MM:SS" },
        due_date: { type: "string", description: "截止时间，YYYY-MM-DD HH:MM:SS" },
        is_all_day: { type: "boolean", description: "是否全天任务" },
        reminder: { type: "string", description: "提醒选项" },
        project_id: { type: "string", description: "项目ID" },
        desc: { type: "string", description: "官方字段 desc" },
        time_zone: { type: "string", description: "时区" },
        reminders: { type: "array", items: { type: "string" }, description: "提醒列表" },
        repeat_flag: { type: "string", description: "重复规则" },
        sort_order: { type: "integer", description: "排序" },
        items: { type: "array", items: { type: "object", additionalProperties: true }, description: "子任务列表" }
      },
      required: ["title"]
    },
    run: async (api, params) => createTask(api, params)
  });

  registerTool(api, {
    name: "dida_update_task",
    description: "更新任务（按 task_id_or_title；status=2 可直接完成）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id_or_title: { type: "string", description: "任务ID或标题" },
        title: { type: "string", description: "新标题" },
        content: { type: "string", description: "新内容" },
        priority: { type: "integer", description: "新优先级：0/1/3/5", enum: [0, 1, 3, 5] },
        project_name: { type: "string", description: "新项目名称" },
        tag_names: { type: "array", items: { type: "string" }, description: "新标签列表（官方 API 暂不支持）" },
        start_date: { type: "string", description: "新开始时间" },
        due_date: { type: "string", description: "新截止时间" },
        is_all_day: { type: "boolean", description: "是否全天任务" },
        reminder: { type: "string", description: "新提醒" },
        status: { type: "integer", description: "状态：0 未完成 / 2 已完成" },
        project_id: { type: "string", description: "项目ID" },
        desc: { type: "string", description: "官方字段 desc" },
        time_zone: { type: "string", description: "时区" },
        reminders: { type: "array", items: { type: "string" }, description: "提醒列表" },
        repeat_flag: { type: "string", description: "重复规则" },
        sort_order: { type: "integer", description: "排序" },
        items: { type: "array", items: { type: "object", additionalProperties: true }, description: "子任务列表" }
      },
      required: ["task_id_or_title"]
    },
    run: async (api, params) => updateTask(api, params)
  });

  registerTool(api, {
    name: "dida_complete_task",
    description: "完成任务（按 task_id_or_title）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id_or_title: { type: "string", description: "任务ID或标题" }
      },
      required: ["task_id_or_title"]
    },
    run: async (api, params) => completeTask(api, params)
  });

  registerTool(api, {
    name: "dida_delete_task",
    description: "删除任务（按 task_id_or_title）。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id_or_title: { type: "string", description: "任务ID或标题" }
      },
      required: ["task_id_or_title"]
    },
    run: async (api, params) => deleteTask(api, params)
  });

  // Short aliases (keep dida_* for compatibility)
  registerTool(api, {
    name: "tt_task_create",
    description: "dida_create_task 的英文别名。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        title: { type: "string", description: "title" },
        content: { type: "string", description: "content" },
        priority: { type: "integer", description: "priority: 0/1/3/5", enum: [0, 1, 3, 5] },
        project_name: { type: "string", description: "project name" },
        start_date: { type: "string", description: "start (YYYY-MM-DD HH:MM:SS)" },
        due_date: { type: "string", description: "due (YYYY-MM-DD HH:MM:SS)" },
        is_all_day: { type: "boolean", description: "all-day?" }
      },
      required: ["title"]
    },
    run: async (api, params) => createTask(api, params)
  });

  registerTool(api, {
    name: "tt_task_update",
    description: "dida_update_task 的英文别名。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id_or_title: { type: "string", description: "task id or title" },
        title: { type: "string", description: "new title" },
        content: { type: "string", description: "new content" },
        due_date: { type: "string", description: "new due" },
        priority: { type: "integer", description: "new priority: 0/1/3/5", enum: [0, 1, 3, 5] },
        status: { type: "integer", description: "0=active, 2=completed" }
      },
      required: ["task_id_or_title"]
    },
    run: async (api, params) => updateTask(api, params)
  });

  registerTool(api, {
    name: "tt_task_complete",
    description: "dida_complete_task 的英文别名。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id_or_title: { type: "string", description: "task id or title" }
      },
      required: ["task_id_or_title"]
    },
    run: async (api, params) => completeTask(api, params)
  });

  registerTool(api, {
    name: "tt_task_delete",
    description: "dida_delete_task 的英文别名。",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id_or_title: { type: "string", description: "task id or title" }
      },
      required: ["task_id_or_title"]
    },
    run: async (api, params) => deleteTask(api, params)
  });
}

function registerTool(api: any, def: ToolDef) {
  api.registerTool(
    {
      name: def.name,
      description: def.description,
      parameters: def.parameters,
      async execute(_id: string, params: Record<string, any> | undefined) {
        try {
          const result = await def.run(api, params || {});
          return formatResult(result);
        } catch (error: any) {
          return formatError(error);
        }
      }
    },
    { optional: true }
  );
}

function formatResult(result: unknown) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(result, null, 2)
      }
    ]
  };
}

function formatError(error: any) {
  const message = error instanceof Error ? error.message : String(error);
  return {
    isError: true,
    content: [
      {
        type: "text",
        text: `调用失败: ${message}`
      }
    ]
  };
}

function loadConfigFallback() {
  try {
    const p =
      process.env.OPENCLAW_CONFIG_PATH ||
      path.join(os.homedir(), ".openclaw", "openclaw.json");
    const raw = fs.readFileSync(p, "utf8");
    const parsed = JSON.parse(raw);
    return (
      (parsed && parsed.plugins && parsed.plugins.entries && parsed.plugins.entries[PLUGIN_ID] && parsed.plugins.entries[PLUGIN_ID].config) ||
      {}
    );
  } catch {
    return {};
  }
}

function getConfig(api: any) {
  // Some OpenClaw builds redact plugin config when executing agent tools.
  // Fall back to reading from the local OpenClaw config file so the plugin can still work.
  const cfgFromApi = resolveConfigFromApi(api);
  const cfg = mergeDefined(loadConfigFallback(), cfgFromApi);
  if (cfg.clientId) state.clientId = cfg.clientId;
  if (cfg.clientSecret) state.clientSecret = cfg.clientSecret;
  if (cfg.redirectUri) state.redirectUri = cfg.redirectUri;
  if (cfg.accessToken) state.accessToken = cfg.accessToken;
  if (cfg.refreshToken) state.refreshToken = cfg.refreshToken;

  let systemTimeZone: string | undefined;
  try {
    systemTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    systemTimeZone = undefined;
  }

  return {
    clientId: state.clientId,
    clientSecret: state.clientSecret,
    redirectUri: state.redirectUri,
    accessToken: state.accessToken,
    refreshToken: state.refreshToken,
    baseUrl: cfg.baseUrl || DEFAULT_BASE_URL,
    authUrl: cfg.authUrl || DEFAULT_AUTH_URL,
    tokenUrl: cfg.tokenUrl || DEFAULT_TOKEN_URL,
    timeoutMs: normalizeTimeout(cfg.timeoutMs),
    // Default to system timezone so today/yesterday filters work for all-day tasks.
    // Fallback to Asia/Shanghai for this environment if system timezone isn't available.
    timeZone: cfg.timeZone || systemTimeZone || "Asia/Shanghai", 
    autoRefresh: cfg.autoRefresh !== false
  };
}

function resolveConfigFromApi(api: any) {
  const root = (api && api.config) || {};
  if (root && typeof root === "object" && root.plugins?.entries) {
    const pluginId = api?.id || api?.pluginId || api?.manifest?.id || PLUGIN_ID;
    const entry = root.plugins.entries?.[pluginId];
    const pluginCfg = entry && entry.config;
    if (pluginCfg && typeof pluginCfg === "object") {
      return pluginCfg;
    }
  }
  if (root && typeof root === "object" && !Object.prototype.hasOwnProperty.call(root, "plugins")) {
    return root;
  }
  return {};
}

function mergeDefined(base: Record<string, any>, override: Record<string, any>) {
  const merged: Record<string, any> = { ...(base || {}) };
  if (override && typeof override === "object") {
    for (const [key, value] of Object.entries(override)) {
      if (value !== undefined && value !== null && value !== "") {
        merged[key] = value;
      }
    }
  }
  return merged;
}

function normalizeTimeout(value: any) {
  if (typeof value === "number" && Number.isFinite(value) && value >= 1000) {
    return Math.min(value, 120000);
  }
  return DEFAULT_TIMEOUT_MS;
}

function ensureAccessToken(cfg: ReturnType<typeof getConfig>) {
  if (!cfg.accessToken) {
    throw new Error("未配置 accessToken，请先完成 OAuth 授权");
  }
}

function buildAuthUrl(api: any, params: Record<string, any>) {
  const cfg = getConfig(api);
  if (!cfg.clientId) {
    throw new Error("未配置 clientId");
  }
  const redirectUri = params.redirect_uri || cfg.redirectUri;
  if (!redirectUri) {
    throw new Error("未配置 redirectUri");
  }

  const url = new URL(cfg.authUrl);
  url.searchParams.set("client_id", cfg.clientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("response_type", "code");
  if (params.state) {
    url.searchParams.set("state", params.state);
  }
  if (params.scope) {
    url.searchParams.set("scope", params.scope);
  }

  return {
    url: url.toString(),
    clientId: cfg.clientId,
    redirectUri
  };
}

async function exchangeCode(api: any, params: Record<string, any>) {
  const cfg = getConfig(api);
  if (!params.code) {
    throw new Error("缺少 code 参数");
  }
  if (!cfg.clientId || !cfg.clientSecret) {
    throw new Error("未配置 clientId/clientSecret");
  }
  const redirectUri = params.redirect_uri || cfg.redirectUri;
  if (!redirectUri) {
    throw new Error("未配置 redirectUri");
  }

  const payload = new URLSearchParams({
    client_id: cfg.clientId,
    client_secret: cfg.clientSecret,
    code: params.code,
    redirect_uri: redirectUri,
    grant_type: "authorization_code"
  });

  const data = await requestToken(cfg.tokenUrl, payload, cfg.timeoutMs);
  updateTokens(data);
  return {
    ...data,
    note: "请将 access_token/refresh_token 写入 OpenClaw 配置以持久化"
  };
}

async function refreshToken(api: any, params: Record<string, any>) {
  const cfg = getConfig(api);
  if (!cfg.clientId || !cfg.clientSecret) {
    throw new Error("未配置 clientId/clientSecret");
  }
  const refreshTokenValue = params.refresh_token || cfg.refreshToken;
  if (!refreshTokenValue) {
    throw new Error("未配置 refreshToken");
  }

  const payload = new URLSearchParams({
    client_id: cfg.clientId,
    client_secret: cfg.clientSecret,
    refresh_token: refreshTokenValue,
    grant_type: "refresh_token"
  });

  const data = await requestToken(cfg.tokenUrl, payload, cfg.timeoutMs);
  updateTokens(data, refreshTokenValue);
  return {
    ...data,
    note: "请将 access_token/refresh_token 写入 OpenClaw 配置以持久化"
  };
}

function updateTokens(data: any, fallbackRefreshToken?: string) {
  if (data && data.access_token) {
    state.accessToken = data.access_token;
  }
  if (data && data.refresh_token) {
    state.refreshToken = data.refresh_token;
  } else if (fallbackRefreshToken) {
    state.refreshToken = fallbackRefreshToken;
  }
}

async function requestToken(url: string, payload: URLSearchParams, timeoutMs: number) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Accept: "application/json"
      },
      body: payload.toString(),
      signal: controller.signal
    });

    const data = await safeReadJson(response);
    if (!response.ok) {
      const message = data?.error_description || data?.error || data?.message || `Token 请求失败: ${response.status}`;
      throw new Error(message);
    }
    return data;
  } finally {
    clearTimeout(timeout);
  }
}

async function didaRequest(
  api: any,
  method: string,
  endpoint: string,
  opts: { data?: Record<string, any>; params?: Record<string, any>; allowRefresh?: boolean } = {}
) {
  const cfg = getConfig(api);
  ensureAccessToken(cfg);

  const url = buildUrl(cfg.baseUrl, endpoint, opts.params);
  const response = await requestJson(url, method, opts.data, cfg.accessToken!, cfg.timeoutMs);

  if (response.status === 401 && cfg.autoRefresh && opts.allowRefresh !== false) {
    const refreshed = await tryRefresh(cfg);
    if (refreshed) {
      return didaRequest(api, method, endpoint, { ...opts, allowRefresh: false });
    }
  }

  const payload = await parseResponse(response);
  if (!response.ok) {
    const message = payload?.errorMessage || payload?.message || `请求失败: ${response.status}`;
    throw new Error(message);
  }
  return payload;
}

async function tryRefresh(cfg: ReturnType<typeof getConfig>) {
  if (!cfg.clientId || !cfg.clientSecret || !cfg.refreshToken) {
    return false;
  }
  try {
    const payload = new URLSearchParams({
      client_id: cfg.clientId,
      client_secret: cfg.clientSecret,
      refresh_token: cfg.refreshToken,
      grant_type: "refresh_token"
    });
    const data = await requestToken(cfg.tokenUrl, payload, cfg.timeoutMs);
    updateTokens(data, cfg.refreshToken);
    return true;
  } catch {
    return false;
  }
}

async function requestJson(
  url: string,
  method: string,
  data: Record<string, any> | undefined,
  accessToken: string,
  timeoutMs: number
) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method,
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        Accept: "application/json"
      },
      body: data ? JSON.stringify(data) : undefined,
      signal: controller.signal
    });
    return response;
  } finally {
    clearTimeout(timeout);
  }
}

async function parseResponse(response: Response) {
  if (response.status === 204) {
    return true;
  }
  const text = await safeReadText(response);
  if (!text) {
    return true;
  }
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function safeReadJson(response: Response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function safeReadText(response: Response) {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

function buildUrl(baseUrl: string, endpoint: string, params?: Record<string, any>) {
  const trimmedBase = baseUrl.replace(/\/+$/, "");
  const trimmedEndpoint = endpoint.replace(/^\/+/, "");
  const url = new URL(`${trimmedBase}/${trimmedEndpoint}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null) {
        continue;
      }
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function createProject(api: any, params: Record<string, any>) {
  const payload: Record<string, any> = { name: params.name };
  if (params.color) payload.color = params.color;
  if (params.view_mode) payload.viewMode = params.view_mode;
  if (params.kind) payload.kind = params.kind;
  if (params.sort_order !== undefined) payload.sortOrder = params.sort_order;
  return didaRequest(api, "POST", "project", { data: payload });
}

async function updateProject(api: any, params: Record<string, any>) {
  const projectId = await resolveProjectId(api, params.project_id_or_name);
  const payload: Record<string, any> = {};
  if (params.name !== undefined) payload.name = params.name;
  if (params.color !== undefined) payload.color = params.color;
  if (params.view_mode !== undefined) payload.viewMode = params.view_mode;
  if (params.kind !== undefined) payload.kind = params.kind;
  if (params.sort_order !== undefined) payload.sortOrder = params.sort_order;
  return didaRequest(api, "POST", `project/${projectId}`, { data: payload });
}

async function deleteProject(api: any, params: Record<string, any>) {
  const projectId = await resolveProjectId(api, params.project_id_or_name);
  return didaRequest(api, "DELETE", `project/${projectId}`);
}

async function resolveProjectId(api: any, projectIdOrName: string) {
  if (!projectIdOrName) {
    throw new Error("缺少 project_id_or_name");
  }
  const projects = await didaRequest(api, "GET", "project");
  if (Array.isArray(projects)) {
    const exact = projects.find((p) => p.id === projectIdOrName);
    if (exact) return exact.id;

    const exactName = projects.find((p) => p.name === projectIdOrName);
    if (exactName) return exactName.id;

    const lower = projectIdOrName.toLowerCase();
    const lowerName = projects.find((p) => String(p.name || "").toLowerCase() === lower);
    if (lowerName) return lowerName.id;

    const partial = projects.find((p) => {
      const name = String(p.name || "").toLowerCase();
      return name.includes(lower) || lower.includes(name);
    });
    if (partial) return partial.id;
  }
  throw new Error(`未找到项目: ${projectIdOrName}`);
}

async function getTasks(api: any, params: Record<string, any>) {
  const completed = params.completed;
  // The official "project/{id}/data" endpoint returns only active (uncompleted) tasks.
  // Completed tasks live behind "project/{id}/task/completed".
  const { tasks } = await listAllTasks(api, { completed });
  const mode = params.mode || "all";
  const keyword = params.keyword ? String(params.keyword).toLowerCase() : "";
  const priority = params.priority;
  const projectName = params.project_name ? String(params.project_name) : "";
  const cfg = getConfig(api);

  const todayKey = mode === "today" || mode === "yesterday" ? dateKey(new Date(), cfg.timeZone) : null;
  const yesterdayKey = mode === "yesterday" ? dateKey(addDays(new Date(), -1), cfg.timeZone) : null;
  const recentThreshold = Date.now() - 7 * 24 * 60 * 60 * 1000;

  return tasks.filter((task) => {
    if (completed !== undefined && task.isCompleted !== completed) {
      return false;
    }

    const taskDate = getTaskDate(task);
    if (mode === "today") {
      if (!taskDate || dateKey(taskDate, cfg.timeZone) !== todayKey) return false;
    } else if (mode === "yesterday") {
      if (!taskDate || dateKey(taskDate, cfg.timeZone) !== yesterdayKey) return false;
    } else if (mode === "recent_7_days") {
      if (!taskDate || taskDate.getTime() < recentThreshold) return false;
    }

    if (keyword) {
      const title = String(task.title || "").toLowerCase();
      const content = String(task.content || "").toLowerCase();
      if (!title.includes(keyword) && !content.includes(keyword)) return false;
    }

    if (priority !== undefined && task.priority !== priority) {
      return false;
    }

    if (projectName) {
      const name = String(task.projectName || "");
      if (!name.includes(projectName)) return false;
    }

    return true;
  });
}

async function listAllTasks(api: any, opts: { completed?: boolean } = {}) {
  const projects = await didaRequest(api, "GET", "project");
  const tasks: any[] = [];

  if (Array.isArray(projects)) {
    for (const project of projects) {
      if (!project?.id) continue;

      if (opts.completed === true) {
        const completedTasks = await listProjectCompletedTasks(api, project.id);
        for (const task of completedTasks) {
          tasks.push(normalizeTask(task, project));
        }
      } else {
        const data = await didaRequest(api, "GET", `project/${project.id}/data`);
        const projectTasks = Array.isArray(data?.tasks) ? data.tasks : [];
        for (const task of projectTasks) {
          tasks.push(normalizeTask(task, project));
        }
      }
    }
  }

  return { tasks, projects };
}

async function listProjectCompletedTasks(api: any, projectId: string) {
  // NOTE: This endpoint isn't documented on the older OpenAPI markdown pages in this repo,
  // but it exists in production and is required to fetch completed tasks.
  const data = await didaRequest(api, "GET", `project/${projectId}/task/completed`);

  // Some accounts/projects may return an empty body with 200; our parser converts that to `true`.
  if (!data || data === true) {
    return [];
  }

  // Be defensive: accept either a raw array or an object wrapper.
  if (Array.isArray(data)) {
    return data;
  }
  if (Array.isArray((data as any).tasks)) {
    return (data as any).tasks;
  }
  return [];
}

function normalizeTask(task: any, project: any) {
  const normalized = { ...task };
  if (!normalized.projectId) normalized.projectId = project?.id;
  if (!normalized.projectName) normalized.projectName = project?.name;

  const hasIsCompleted = normalized.isCompleted !== undefined && normalized.isCompleted !== null;
  const isCompleted = Boolean(
    hasIsCompleted
      ? normalized.isCompleted
      : String(normalized.completed || "").toLowerCase() === "true" || normalized.status === 2
  );

  normalized.isCompleted = isCompleted;
  if (normalized.status === undefined) {
    normalized.status = isCompleted ? 2 : 0;
  }

  return normalized;
}

function getTaskDate(task: any) {
  const dueDate = parseApiDate(task.dueDate);
  const startDate = parseApiDate(task.startDate);
  return dueDate || startDate || null;
}

function parseApiDate(value: any) {
  if (!value) return null;
  if (value instanceof Date) return value;
  if (typeof value !== "string") return null;
  const normalized = normalizeApiDateString(value);
  const timestamp = Date.parse(normalized);
  if (Number.isNaN(timestamp)) return null;
  return new Date(timestamp);
}

function normalizeApiDateString(value: string) {
  let str = value.trim();
  if (str.endsWith("Z")) return str;
  const match = str.match(/([+-]\d{2})(\d{2})$/);
  if (match) {
    str = str.replace(/([+-]\d{2})(\d{2})$/, "$1:$2");
  }
  return str;
}

function dateKey(date: Date, timeZone?: string) {
  if (!timeZone) {
    return date.toISOString().slice(0, 10);
  }
  try {
    const formatter = new Intl.DateTimeFormat("en-CA", {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    });
    return formatter.format(date);
  } catch {
    return date.toISOString().slice(0, 10);
  }
}

function addDays(date: Date, days: number) {
  const next = new Date(date.getTime());
  next.setDate(next.getDate() + days);
  return next;
}

async function createTask(api: any, params: Record<string, any>) {
  const payload = await buildTaskPayload(api, params, true);
  return didaRequest(api, "POST", "task", { data: payload });
}

async function updateTask(api: any, params: Record<string, any>) {
  const task = await findTask(api, params.task_id_or_title);
  const payload = await buildTaskPayload(api, { ...params, project_id: params.project_id || task.projectId }, false);
  payload.id = task.id;
  payload.projectId = task.projectId || payload.projectId;
  return didaRequest(api, "POST", `task/${task.id}`, { data: payload });
}

async function completeTask(api: any, params: Record<string, any>) {
  const task = await findTask(api, params.task_id_or_title);
  return didaRequest(api, "POST", `project/${task.projectId}/task/${task.id}/complete`, { data: {} });
}

async function deleteTask(api: any, params: Record<string, any>) {
  const task = await findTask(api, params.task_id_or_title);
  return didaRequest(api, "DELETE", `project/${task.projectId}/task/${task.id}`);
}

async function findTask(api: any, taskIdOrTitle: string) {
  if (!taskIdOrTitle) {
    throw new Error("缺少 task_id_or_title");
  }
  const { tasks } = await listAllTasks(api);
  const exactId = tasks.find((task) => task.id === taskIdOrTitle);
  if (exactId) return exactId;

  const matched = tasks.filter((task) => task.title === taskIdOrTitle);
  if (matched.length === 1) return matched[0];
  if (matched.length > 1) {
    throw new Error("任务标题重复，请使用任务ID");
  }

  const lower = taskIdOrTitle.toLowerCase();
  const partial = tasks.filter((task) => String(task.title || "").toLowerCase().includes(lower));
  if (partial.length === 1) return partial[0];
  if (partial.length > 1) {
    throw new Error("任务标题匹配多个结果，请使用任务ID");
  }

  throw new Error(`未找到任务: ${taskIdOrTitle}`);
}

async function buildTaskPayload(api: any, params: Record<string, any>, requireProject: boolean) {
  const payload: Record<string, any> = {};
  if (params.title !== undefined) payload.title = params.title;
  if (params.content !== undefined) payload.content = params.content;
  if (params.priority !== undefined) payload.priority = params.priority;
  if (params.desc !== undefined) payload.desc = params.desc;
  if (params.is_all_day !== undefined) payload.isAllDay = params.is_all_day;
  if (params.status !== undefined) payload.status = params.status;

  if (params.project_id) {
    payload.projectId = params.project_id;
  } else if (params.project_name) {
    payload.projectId = await resolveProjectId(api, params.project_name);
  }

  if (requireProject && !payload.projectId) {
    throw new Error("创建任务需要 project_id 或 project_name");
  }

  if (params.start_date) payload.startDate = toApiDateTime(params.start_date);
  if (params.due_date) payload.dueDate = toApiDateTime(params.due_date);
  if (params.time_zone) payload.timeZone = params.time_zone;
  if (params.reminders) payload.reminders = params.reminders;
  if (params.reminder && !payload.reminders) payload.reminders = [params.reminder];
  if (params.repeat_flag) payload.repeatFlag = params.repeat_flag;
  if (params.sort_order !== undefined) payload.sortOrder = params.sort_order;

  if (Array.isArray(params.items)) {
    payload.items = params.items.map((item: Record<string, any>) => normalizeItem(item));
  }

  return payload;
}

function normalizeItem(item: Record<string, any>) {
  const normalized: Record<string, any> = { ...item };
  if (item.start_date !== undefined) normalized.startDate = toApiDateTime(item.start_date);
  if (item.completed_time !== undefined) normalized.completedTime = toApiDateTime(item.completed_time);
  if (item.is_all_day !== undefined) normalized.isAllDay = item.is_all_day;
  if (item.sort_order !== undefined) normalized.sortOrder = item.sort_order;
  if (item.time_zone !== undefined) normalized.timeZone = item.time_zone;
  delete normalized.start_date;
  delete normalized.completed_time;
  delete normalized.is_all_day;
  delete normalized.sort_order;
  delete normalized.time_zone;
  return normalized;
}

function toApiDateTime(value: string) {
  if (!value) return value;
  if (value.includes("T")) return value;
  const normalized = value.trim().replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  const iso = date.toISOString();
  return iso.endsWith("Z") ? iso.replace("Z", "+0000") : iso;
}
