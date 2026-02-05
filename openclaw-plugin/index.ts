const DEFAULT_SSE_URL = "http://127.0.0.1:3000/sse";
const DEFAULT_TIMEOUT_MS = 15000;
const DEFAULT_PROTOCOL_VERSION = "2024-11-05";

export default function register(api: any) {
  registerTools(api);
}

function registerTools(api: any) {
  registerTool(api, {
    name: "dida_get_tasks",
    description: "获取滴答清单任务列表",
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
    mcpTool: "get_tasks"
  });

  registerTool(api, {
    name: "dida_create_task",
    description: "创建滴答清单任务",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        title: { type: "string", description: "任务标题" },
        content: { type: "string", description: "任务内容" },
        priority: { type: "integer", description: "优先级：0/1/3/5", enum: [0, 1, 3, 5] },
        project_name: { type: "string", description: "项目名称" },
        tag_names: { type: "array", items: { type: "string" }, description: "标签名称列表" },
        start_date: { type: "string", description: "开始时间，YYYY-MM-DD HH:MM:SS" },
        due_date: { type: "string", description: "截止时间，YYYY-MM-DD HH:MM:SS" },
        is_all_day: { type: "boolean", description: "是否全天任务" },
        reminder: { type: "string", description: "提醒选项，如 -5M / -1H" },
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
    mcpTool: "create_task"
  });

  registerTool(api, {
    name: "dida_update_task",
    description: "更新滴答清单任务",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id_or_title: { type: "string", description: "任务ID或标题" },
        title: { type: "string", description: "新标题" },
        content: { type: "string", description: "新内容" },
        priority: { type: "integer", description: "新优先级：0/1/3/5", enum: [0, 1, 3, 5] },
        project_name: { type: "string", description: "新项目名称" },
        tag_names: { type: "array", items: { type: "string" }, description: "新标签列表" },
        start_date: { type: "string", description: "新开始时间" },
        due_date: { type: "string", description: "新截止时间" },
        is_all_day: { type: "boolean", description: "是否全天任务" },
        reminder: { type: "string", description: "新提醒" },
        status: { type: "integer", description: "状态：0 未完成 / 2 已完成" }
      },
      required: ["task_id_or_title"]
    },
    mcpTool: "update_task"
  });

  registerTool(api, {
    name: "dida_complete_task",
    description: "完成滴答清单任务",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id_or_title: { type: "string", description: "任务ID或标题" }
      },
      required: ["task_id_or_title"]
    },
    mcpTool: "complete_task"
  });

  registerTool(api, {
    name: "dida_delete_task",
    description: "删除滴答清单任务",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        task_id_or_title: { type: "string", description: "任务ID或标题" }
      },
      required: ["task_id_or_title"]
    },
    mcpTool: "delete_task"
  });

  registerTool(api, {
    name: "dida_get_projects",
    description: "获取滴答清单项目列表",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {}
    },
    mcpTool: "get_projects"
  });

  registerTool(api, {
    name: "dida_create_project",
    description: "创建滴答清单项目",
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
    mcpTool: "create_project"
  });

  registerTool(api, {
    name: "dida_update_project",
    description: "更新滴答清单项目",
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
    mcpTool: "update_project"
  });

  registerTool(api, {
    name: "dida_delete_project",
    description: "删除滴答清单项目",
    parameters: {
      type: "object",
      additionalProperties: false,
      properties: {
        project_id_or_name: { type: "string", description: "项目ID或名称" }
      },
      required: ["project_id_or_name"]
    },
    mcpTool: "delete_project"
  });
}

function registerTool(api: any, def: { name: string; description: string; parameters: any; mcpTool: string }) {
  api.registerTool(
    {
      name: def.name,
      description: def.description,
      parameters: def.parameters,
      async execute(_id: string, params: Record<string, any> | undefined) {
        try {
          const result = await callMcpTool(api, def.mcpTool, params || {});
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
        text: `调用 MCP 失败: ${message}`
      }
    ]
  };
}

async function callMcpTool(api: any, toolName: string, args: Record<string, any>) {
  const config = getConfig(api);
  return callMcpOverSse({
    sseUrl: config.sseUrl,
    apiKey: config.apiKey,
    timeoutMs: config.timeoutMs,
    protocolVersion: config.protocolVersion,
    toolName,
    args
  });
}

function getConfig(api: any) {
  const cfg = (api && api.config) || {};
  const apiKey = cfg.apiKey;
  if (!apiKey) {
    throw new Error("未配置 MCP API Key（plugins.entries.dida-todo.config.apiKey）");
  }
  return {
    sseUrl: cfg.sseUrl || DEFAULT_SSE_URL,
    apiKey,
    timeoutMs: normalizeTimeout(cfg.timeoutMs),
    protocolVersion: cfg.protocolVersion || DEFAULT_PROTOCOL_VERSION
  };
}

function normalizeTimeout(value: any) {
  if (typeof value === "number" && Number.isFinite(value) && value >= 1000) {
    return Math.min(value, 120000);
  }
  return DEFAULT_TIMEOUT_MS;
}

async function callMcpOverSse(opts: {
  sseUrl: string;
  apiKey: string;
  timeoutMs: number;
  protocolVersion: string;
  toolName: string;
  args: Record<string, any>;
}) {
  const headers = buildHeaders(opts.apiKey, opts.protocolVersion);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), opts.timeoutMs);

  try {
    const sseResponse = await fetch(opts.sseUrl, {
      method: "GET",
      headers: {
        Accept: "text/event-stream",
        ...headers
      },
      signal: controller.signal
    });

    if (!sseResponse.ok || !sseResponse.body) {
      const detail = await safeReadText(sseResponse);
      throw new Error(`SSE 连接失败: ${sseResponse.status} ${detail}`.trim());
    }

    const reader = sseResponse.body.getReader();
    const pending = new Map<number, { resolve: (value: any) => void; reject: (err: any) => void }>();

    const endpointPromise = new Promise<string>((resolve, reject) => {
      startEventLoop(reader, opts.sseUrl, {
        onEndpoint: (url) => {
          resolve(url);
        },
        onMessage: (message) => {
          if (typeof message?.id === "number" && pending.has(message.id)) {
            const handlers = pending.get(message.id)!;
            pending.delete(message.id);
            if (message.error) {
              handlers.reject(new Error(message.error.message || "MCP 返回错误"));
            } else {
              handlers.resolve(message.result);
            }
          }
        },
        onError: (err) => {
          for (const handlers of pending.values()) {
            handlers.reject(err);
          }
          pending.clear();
          reject(err);
        }
      });
    });

    const messageEndpoint = await withTimeout(endpointPromise, opts.timeoutMs, "等待 MCP endpoint 超时");

    await sendRequest({
      endpoint: messageEndpoint,
      headers,
      controller,
      method: "initialize",
      params: {
        protocolVersion: opts.protocolVersion,
        capabilities: {},
        clientInfo: {
          name: "dida-openclaw-plugin",
          version: "0.1.0"
        }
      },
      pending
    });

    await sendNotification({
      endpoint: messageEndpoint,
      headers,
      controller,
      method: "notifications/initialized",
      params: {}
    });

    const result = await sendRequest({
      endpoint: messageEndpoint,
      headers,
      controller,
      method: "tools/call",
      params: {
        name: opts.toolName,
        arguments: args
      },
      pending
    });

    return result;
  } finally {
    clearTimeout(timeout);
    controller.abort();
  }
}

function buildHeaders(apiKey: string, protocolVersion: string) {
  return {
    "x-api-key": apiKey,
    "MCP-Protocol-Version": protocolVersion
  };
}

async function sendRequest(opts: {
  endpoint: string;
  headers: Record<string, string>;
  controller: AbortController;
  method: string;
  params: Record<string, any>;
  pending: Map<number, { resolve: (value: any) => void; reject: (err: any) => void }>;
}) {
  const id = nextId();
  const payload = {
    jsonrpc: "2.0",
    id,
    method: opts.method,
    params: opts.params
  };

  const responsePromise = new Promise((resolve, reject) => {
    opts.pending.set(id, { resolve, reject });
  });

  await postJson(opts.endpoint, payload, opts.headers, opts.controller);
  return responsePromise;
}

async function sendNotification(opts: {
  endpoint: string;
  headers: Record<string, string>;
  controller: AbortController;
  method: string;
  params: Record<string, any>;
}) {
  const payload = {
    jsonrpc: "2.0",
    method: opts.method,
    params: opts.params
  };
  await postJson(opts.endpoint, payload, opts.headers, opts.controller);
}

async function postJson(
  endpoint: string,
  payload: Record<string, any>,
  headers: Record<string, string>,
  controller: AbortController
) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...headers
    },
    body: JSON.stringify(payload),
    signal: controller.signal
  });

  if (!response.ok) {
    const detail = await safeReadText(response);
    throw new Error(`MCP 请求失败: ${response.status} ${detail}`.trim());
  }
}

async function safeReadText(response: Response) {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

function startEventLoop(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  baseUrl: string,
  handlers: {
    onEndpoint: (url: string) => void;
    onMessage: (message: any) => void;
    onError: (err: any) => void;
  }
) {
  const decoder = new TextDecoder();
  let buffer = "";

  (async () => {
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        buffer = buffer.replace(/\r\n/g, "\n");
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const part of parts) {
          const event = parseSseEvent(part);
          if (!event) {
            continue;
          }
          if (event.event === "endpoint") {
            handlers.onEndpoint(resolveEndpoint(event.data, baseUrl));
          } else if (event.event === "message") {
            const payload = safeParseJson(event.data);
            if (payload) {
              handlers.onMessage(payload);
            }
          }
        }
      }
    } catch (error) {
      handlers.onError(error);
    }
  })();
}

function parseSseEvent(raw: string) {
  const lines = raw.split("\n");
  let event = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (!dataLines.length) {
    return null;
  }

  return { event, data: dataLines.join("\n") };
}

function resolveEndpoint(data: string, fallbackBase: string) {
  let endpoint = data;
  const parsed = safeParseJson(data);
  if (parsed && typeof parsed === "object") {
    const candidate = (parsed as any).endpoint || (parsed as any).uri;
    if (typeof candidate === "string") {
      endpoint = candidate;
    }
  }
  try {
    return new URL(endpoint, fallbackBase).toString();
  } catch {
    return endpoint;
  }
}

function safeParseJson(data: string) {
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

function withTimeout<T>(promise: Promise<T>, ms: number, message: string) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  const timeoutPromise = new Promise<T>((_, reject) => {
    timer = setTimeout(() => reject(new Error(message)), ms);
  });

  return Promise.race([promise, timeoutPromise]).finally(() => {
    if (timer) {
      clearTimeout(timer);
    }
  }) as Promise<T>;
}

let _idCounter = 1;
function nextId() {
  const id = _idCounter;
  _idCounter += 1;
  return id;
}
