import {
  Activity,
  Bot,
  CalendarClock,
  Headphones,
  PhoneCall,
  Users,
  Workflow,
} from "lucide-react";
import { useEffect, useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type HealthState = "checking" | "online" | "offline";
type RecentActivityState = "loading" | "ready" | "error";
type CallsState = "idle" | "loading" | "ready" | "error";
type LeadsState = "idle" | "loading" | "ready" | "error";
type AgentsState = "idle" | "loading" | "ready" | "error";
type AppointmentsState = "idle" | "loading" | "ready" | "error";
type WorkflowsState = "idle" | "loading" | "ready" | "error";
type Section =
  | "Overview"
  | "Calls"
  | "Leads"
  | "Agents"
  | "Appointments"
  | "Workflows";

type LeadEvent = {
  id: string;
  event_type: string;
  source: string;
  customer_payload: {
    name: string;
    phone: string;
    email?: string | null;
  };
  payload: Record<string, unknown>;
  status: string;
  created_at: string;
};

type EventApiItem = LeadEvent;
type AppointmentEvent = LeadEvent;

type CallApiItem = {
  id: string;
  direction: string;
  status: string;
  provider: string | null;
  from_number: string | null;
  to_number: string | null;
  duration_seconds: number | null;
  outcome: string | null;
  summary: string | null;
  created_at: string;
};

type AgentApiItem = {
  id: string;
  name: string;
  language: string;
  voice: string | null;
  personality: string;
  is_active: boolean;
  created_at: string;
};

type WorkflowApiItem = {
  id: string;
  name: string;
  trigger: string;
  action: string;
  agent_id: string | null;
  timing: string;
  config: Record<string, unknown>;
  enabled: boolean;
  created_at: string;
};

type RecentActivityItem = {
  id: string;
  kind: "lead" | "appointment" | "event" | "inbound-call" | "outbound-call";
  title: string;
  detail: string;
  createdAt: string;
};

const navigation = [
  ["Overview", Activity],
  ["Calls", PhoneCall],
  ["Leads", Users],
  ["Agents", Headphones],
  ["Appointments", CalendarClock],
  ["Workflows", Workflow],
] as const;

function textValue(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function formatActivityTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? timestamp : date.toLocaleString();
}

function normalizeEvent(event: EventApiItem): RecentActivityItem {
  const customerName = textValue(event.customer_payload.name);
  const location = textValue(event.payload.location);
  const propertyType = textValue(
    event.payload.property_type ?? event.payload.propertyType,
  );
  const scheduledDate = textValue(
    event.payload.scheduled_date ?? event.payload.date ?? event.payload.preferred_date,
  );
  const scheduledTime = textValue(
    event.payload.scheduled_time ?? event.payload.time ?? event.payload.preferred_time,
  );
  const schedule = [scheduledDate, scheduledTime].filter(Boolean).join(" at ");
  const detail = [location, propertyType, schedule]
    .filter((value): value is string => Boolean(value))
    .join(" · ");

  if (event.event_type === "lead.created") {
    return {
      id: `event-${event.id}`,
      kind: "lead",
      title: customerName ? `New lead — ${customerName}` : "New lead",
      detail: detail || "Lead submitted",
      createdAt: event.created_at,
    };
  }

  if (event.event_type === "appointment.created") {
    return {
      id: `event-${event.id}`,
      kind: "appointment",
      title: customerName
        ? `Site visit scheduled — ${customerName}`
        : "Site visit scheduled",
      detail: detail || "Appointment created",
      createdAt: event.created_at,
    };
  }

  return {
    id: `event-${event.id}`,
    kind: "event",
    title: customerName ? `New activity — ${customerName}` : "New activity",
    detail: detail || event.event_type.replace(".", " "),
    createdAt: event.created_at,
  };
}

function normalizeCall(call: CallApiItem): RecentActivityItem {
  const isOutbound = call.direction === "OUTBOUND";
  const outcome = textValue(call.outcome);
  const summary = textValue(call.summary);
  const status = call.status.replace(/_/g, " ").toLowerCase();

  return {
    id: `call-${call.id}`,
    kind: isOutbound ? "outbound-call" : "inbound-call",
    title: isOutbound ? "Outbound call" : "Inbound call",
    detail: summary || outcome || `Call ${status}`,
    createdAt: call.created_at,
  };
}

function formatCallDuration(durationSeconds: number | null): string {
  if (typeof durationSeconds !== "number") return "Not available";

  const minutes = Math.floor(durationSeconds / 60);
  const seconds = durationSeconds % 60;
  return `${minutes}m ${seconds}s`;
}

function humanizeCallValue(value: string): string {
  return value.replace(/_/g, " ").toLowerCase();
}

function payloadDisplayValue(value: unknown): string | undefined {
  if (typeof value === "string") return textValue(value);
  if (typeof value === "number") return String(value);
  return undefined;
}

function recordValue(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

export default function App() {
  const [activeSection, setActiveSection] = useState<Section>("Overview");
  const [health, setHealth] = useState<HealthState>("checking");
  const [callsToday, setCallsToday] = useState<string>("--");
  const [newLeads, setNewLeads] = useState<string>("--");
  const [siteVisits, setSiteVisits] = useState<string>("--");
  const [recentActivity, setRecentActivity] = useState<RecentActivityItem[]>([]);
  const [recentActivityState, setRecentActivityState] =
    useState<RecentActivityState>("loading");
  const [calls, setCalls] = useState<CallApiItem[]>([]);
  const [callsState, setCallsState] = useState<CallsState>("idle");
  const [leads, setLeads] = useState<LeadEvent[]>([]);
  const [leadsState, setLeadsState] = useState<LeadsState>("idle");
  const [agents, setAgents] = useState<AgentApiItem[]>([]);
  const [agentsState, setAgentsState] = useState<AgentsState>("idle");
  const [appointments, setAppointments] = useState<AppointmentEvent[]>([]);
  const [appointmentsState, setAppointmentsState] =
    useState<AppointmentsState>("idle");
  const [workflows, setWorkflows] = useState<WorkflowApiItem[]>([]);
const [workflowsState, setWorkflowsState] =
  useState<WorkflowsState>("idle");
  const [updatingWorkflowId, setUpdatingWorkflowId] = useState<string | null>(null);
const [workflowUpdateError, setWorkflowUpdateError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;

    fetch(`${API_BASE_URL}/health`)
      .then((response) => {
        if (!response.ok) throw new Error("Health check failed");
        if (isCurrent) setHealth("online");
      })
      .catch(() => {
        if (isCurrent) setHealth("offline");
      });

    fetch(`${API_BASE_URL}/api/v1/calls/today/count`)
      .then((response) => {
        if (!response.ok) throw new Error("Calls count request failed");
        return response.json();
      })
      .then((data: { count: number }) => {
        if (isCurrent) setCallsToday(String(data.count));
      })
      .catch(() => {
        if (isCurrent) setCallsToday("--");
      });
    fetch(`${API_BASE_URL}/api/v1/events/leads/today/count`)
  .then((response) => {
    if (!response.ok) throw new Error("Leads count request failed");
    return response.json();
  })
  .then((data: { count: number }) => {
    if (isCurrent) setNewLeads(String(data.count));
  })
  .catch(() => {
    if (isCurrent) setNewLeads("--");
  });
  fetch(`${API_BASE_URL}/api/v1/events/appointments/today/count`)
  .then((response) => {
    if (!response.ok) throw new Error("Site visits count request failed");
    return response.json();
  })
  .then((data: { count: number }) => {
    if (isCurrent) setSiteVisits(String(data.count));
  })
  .catch(() => {
    if (isCurrent) setSiteVisits("--");
  });

    Promise.all([
      fetch(`${API_BASE_URL}/api/v1/events`).then((response) => {
        if (!response.ok) throw new Error("Events activity request failed");
        return response.json() as Promise<EventApiItem[]>;
      }),
      fetch(`${API_BASE_URL}/api/v1/calls`).then((response) => {
        if (!response.ok) throw new Error("Calls activity request failed");
        return response.json() as Promise<CallApiItem[]>;
      }),
    ])
      .then(([events, calls]) => {
        const activity = [...events.map(normalizeEvent), ...calls.map(normalizeCall)]
          .sort(
            (first, second) =>
              new Date(second.createdAt).getTime() -
              new Date(first.createdAt).getTime(),
          )
          .slice(0, 5);

        if (isCurrent) {
          setRecentActivity(activity);
          setRecentActivityState("ready");
        }
      })
      .catch(() => {
        if (isCurrent) setRecentActivityState("error");
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  useEffect(() => {
    if (activeSection !== "Calls" || callsState !== "idle") return;

    let isCurrent = true;
    setCallsState("loading");

    fetch(`${API_BASE_URL}/api/v1/calls`)
      .then((response) => {
        if (!response.ok) throw new Error("Calls request failed");
        return response.json() as Promise<CallApiItem[]>;
      })
      .then((data) => {
        if (isCurrent) {
          setCalls(data);
          setCallsState("ready");
        }
      })
      .catch(() => {
        if (isCurrent) setCallsState("error");
      });

    return () => {
      isCurrent = false;
    };
  }, [activeSection]);

  useEffect(() => {
    if (activeSection !== "Appointments" || appointmentsState !== "idle") return;

    let isCurrent = true;
    setAppointmentsState("loading");

    fetch(`${API_BASE_URL}/api/v1/events`)
      .then((response) => {
        if (!response.ok) throw new Error("Appointments request failed");
        return response.json() as Promise<AppointmentEvent[]>;
      })
      .then((data) => {
        const appointmentEvents = data
          .filter((event) => event.event_type === "appointment.created")
          .sort(
            (first, second) =>
              new Date(second.created_at).getTime() -
              new Date(first.created_at).getTime(),
          );

        if (isCurrent) {
          setAppointments(appointmentEvents);
          setAppointmentsState("ready");
        }
      })
      .catch(() => {
        if (isCurrent) setAppointmentsState("error");
      });

    return () => {
      isCurrent = false;
    };
  }, [activeSection]);

  
  useEffect(() => {
    if (activeSection !== "Workflows" || workflowsState !== "idle") return;

    let isCurrent = true;
    setWorkflowsState("loading");

    fetch(`${API_BASE_URL}/api/v1/workflows`)
      .then((response) => {
        if (!response.ok) throw new Error("Workflows request failed");
        return response.json() as Promise<WorkflowApiItem[]>;
      })
      .then((data) => {
        if (isCurrent) {
          setWorkflows(data);
          setWorkflowsState("ready");
        }
      })
      .catch(() => {
        if (isCurrent) setWorkflowsState("error");
      });

    return () => {
      isCurrent = false;
    };
  }, [activeSection]);

  useEffect(() => {
    if (activeSection !== "Agents" || agentsState !== "idle") return;

    let isCurrent = true;
    setAgentsState("loading");

    fetch(`${API_BASE_URL}/api/v1/agents`)
      .then((response) => {
        if (!response.ok) throw new Error("Agents request failed");
        return response.json() as Promise<AgentApiItem[]>;
      })
      .then((data) => {
        if (isCurrent) {
          setAgents(data);
          setAgentsState("ready");
        }
      })
      .catch(() => {
        if (isCurrent) setAgentsState("error");
      });

    return () => {
      isCurrent = false;
    };
  }, [activeSection]);

  useEffect(() => {
    if (activeSection !== "Leads" || leadsState !== "idle") return;

    let isCurrent = true;
    setLeadsState("loading");

    fetch(`${API_BASE_URL}/api/v1/events`)
      .then((response) => {
        if (!response.ok) throw new Error("Leads request failed");
        return response.json() as Promise<LeadEvent[]>;
      })
      .then((data) => {
        const leadEvents = data
          .filter((event) => event.event_type === "lead.created")
          .sort(
            (first, second) =>
              new Date(second.created_at).getTime() -
              new Date(first.created_at).getTime(),
          );

        if (isCurrent) {
          setLeads(leadEvents);
          setLeadsState("ready");
        }
      })
      .catch(() => {
        if (isCurrent) setLeadsState("error");
      });

    return () => {
      isCurrent = false;
    };
  }, [activeSection]);

  
  async function handleWorkflowEnabledChange(
    workflowId: string,
    enabled: boolean,
  ) {
    setUpdatingWorkflowId(workflowId);
    setWorkflowUpdateError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/workflows/${workflowId}/enabled`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ enabled }),
        },
      );

      if (!response.ok) {
        throw new Error("Workflow update failed");
      }

      const updatedWorkflow =
        (await response.json()) as WorkflowApiItem;

      setWorkflows((currentWorkflows) =>
        currentWorkflows.map((workflow) =>
          workflow.id === updatedWorkflow.id
            ? updatedWorkflow
            : workflow,
        ),
      );
    } catch {
      setWorkflowUpdateError(
        "Unable to update workflow status. Please try again.",
      );
    } finally {
      setUpdatingWorkflowId(null);
    }
  }

  const statusLabel =
    health === "checking"
      ? "Checking platform"
      : health === "online"
        ? "Platform online"
        : "Platform unavailable";

  const statusColor =
    health === "online"
      ? "bg-emerald-500"
      : health === "offline"
        ? "bg-red-500"
        : "bg-amber-500";

  return (
    <main className="min-h-screen bg-surface text-ink">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 border-r border-line bg-white px-5 py-6 lg:block">
          <div className="mb-8 flex items-center gap-3">
            <div
              className="grid h-10 w-10 place-items-center rounded bg-brand text-white"
              aria-hidden="true"
            >
              <Bot size={22} />
            </div>

            <div>
              <h1 className="text-lg font-semibold">SwarVox AI</h1>
              <p className="text-sm text-slate-500">Voice operations</p>
            </div>
          </div>

          <nav
            aria-label="Primary navigation"
            className="space-y-1 text-sm"
          >
            {navigation.map(([label, Icon], index) => (
              <button
                key={label}
                type="button"
                onClick={() => setActiveSection(label)}
                aria-current={activeSection === label ? "page" : undefined}
                className={`flex w-full items-center gap-3 rounded px-3 py-2 text-left ${
                  activeSection === label
                    ? "bg-teal-50 text-brand"
                    : "hover:bg-slate-100"
                }`}
              >
                <Icon size={17} />
                {label}
              </button>
            ))}
          </nav>
        </aside>

        <section className="flex-1 px-5 py-6 sm:px-8">
          {activeSection === "Calls" ? (
            <CallsView calls={calls} state={callsState} />
          ) : activeSection === "Leads" ? (
            <LeadsView leads={leads} state={leadsState} />
          ) : activeSection === "Agents" ? (
            <AgentsView agents={agents} state={agentsState} />
          
) : activeSection === "Appointments" ? (
  <AppointmentsView
    appointments={appointments}
    state={appointmentsState}
  />
) : activeSection === "Workflows" ? (
  <WorkflowsView
  workflows={workflows}
  state={workflowsState}
  onEnabledChange={handleWorkflowEnabledChange}
  updatingWorkflowId={updatingWorkflowId}
  updateError={workflowUpdateError}
/>
) : (
            <>
              <header className="flex flex-col gap-4 border-b border-line pb-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm font-medium text-brand">Workspace</p>
                  <h2 className="mt-1 text-2xl font-semibold">
                    Operations overview
                  </h2>
                </div>

                <div className="flex items-center gap-2 text-sm" role="status">
                  <span
                    className={`h-2 w-2 rounded-full ${statusColor}`}
                  />
                  {statusLabel}
                </div>
              </header>

              <section
                className="mt-8 grid gap-4 md:grid-cols-3"
                aria-label="Operational metrics"
              >
                <Metric label="Calls today" value={callsToday} />
                <Metric label="New leads" value={newLeads} />
                <Metric label="Site visits" value={siteVisits} />
              </section>

              <section className="mt-8 border-t border-line pt-5">
                <h3 className="text-base font-semibold">Recent activity</h3>
                {recentActivityState === "loading" ? (
                  <p className="mt-2 text-sm text-slate-600">
                    Loading recent activity...
                  </p>
                ) : recentActivityState === "error" ? (
                  <p className="mt-2 text-sm text-slate-600">
                    Unable to load recent activity.
                  </p>
                ) : recentActivity.length === 0 ? (
                  <p className="mt-2 text-sm text-slate-600">
                    No operational activity yet.
                  </p>
                ) : (
                  <ul className="mt-3 divide-y divide-line border-y border-line">
                    {recentActivity.map((item) => (
                      <li
                        key={item.id}
                        className="flex flex-col gap-1 py-3 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div>
                          <p className="text-sm font-medium">{item.title}</p>
                          <p className="text-sm text-slate-600">{item.detail}</p>
                        </div>
                        <time
                          className="text-sm text-slate-500"
                          dateTime={item.createdAt}
                        >
                          {formatActivityTimestamp(item.createdAt)}
                        </time>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </>
          )}
        </section>
      </div>
    </main>
  );
}

function CallsView({
  calls,
  state,
}: {
  calls: CallApiItem[];
  state: CallsState;
}) {
  return (
    <>
      <header className="border-b border-line pb-5">
        <p className="text-sm font-medium text-brand">Workspace</p>
        <h2 className="mt-1 text-2xl font-semibold">Calls</h2>
        <p className="mt-1 text-sm text-slate-600">Recent voice interactions</p>
      </header>

      {state === "loading" ? (
        <p className="mt-6 text-sm text-slate-600">Loading calls...</p>
      ) : state === "error" ? (
        <p className="mt-6 text-sm text-slate-600">Unable to load calls.</p>
      ) : state === "ready" && calls.length === 0 ? (
        <p className="mt-6 text-sm text-slate-600">No calls yet.</p>
      ) : (
        <div className="mt-6 space-y-3">
          {calls.map((call) => {
            const isOutbound = call.direction === "OUTBOUND";
            const phoneNumber = isOutbound ? call.to_number : call.from_number;
            const outcome = textValue(call.outcome);
            const summary = textValue(call.summary);

            return (
              <article key={call.id} className="rounded border border-line bg-white p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">
                      {isOutbound ? "Outbound" : "Inbound"} call
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      {phoneNumber || "Number not available"}
                    </p>
                  </div>
                  <p className="text-sm text-slate-500">
                    {humanizeCallValue(call.status)}
                  </p>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <dt className="text-slate-500">Duration</dt>
                    <dd className="mt-1">{formatCallDuration(call.duration_seconds)}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Provider</dt>
                    <dd className="mt-1">{call.provider || "Not available"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Created</dt>
                    <dd className="mt-1">
                      {formatActivityTimestamp(call.created_at)}
                    </dd>
                  </div>
                </dl>

                {outcome ? (
                  <p className="mt-4 text-sm text-slate-600">
                    Outcome: {outcome}
                  </p>
                ) : null}
                {summary ? (
                  <p className="mt-2 text-sm text-slate-600">{summary}</p>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}

function LeadsView({
  leads,
  state,
}: {
  leads: LeadEvent[];
  state: LeadsState;
}) {
  return (
    <>
      <header className="border-b border-line pb-5">
        <p className="text-sm font-medium text-brand">Workspace</p>
        <h2 className="mt-1 text-2xl font-semibold">Leads</h2>
        <p className="mt-1 text-sm text-slate-600">Recent customer enquiries</p>
      </header>

      {state === "loading" ? (
        <p className="mt-6 text-sm text-slate-600">Loading leads...</p>
      ) : state === "error" ? (
        <p className="mt-6 text-sm text-slate-600">Unable to load leads.</p>
      ) : state === "ready" && leads.length === 0 ? (
        <p className="mt-6 text-sm text-slate-600">No leads yet.</p>
      ) : (
        <div className="mt-6 space-y-3">
          {leads.map((lead) => {
            const email = textValue(lead.customer_payload.email);
            const phone = textValue(lead.customer_payload.phone);
            const payloadDetails: Array<[string, string | undefined]> = [
              ["Property type", payloadDisplayValue(lead.payload.property_type)],
              ["Location", payloadDisplayValue(lead.payload.location)],
              ["Budget", payloadDisplayValue(lead.payload.budget)],
              ["Service", payloadDisplayValue(lead.payload.service)],
              ["Preferred date", payloadDisplayValue(lead.payload.preferred_date)],
              ["Preferred time", payloadDisplayValue(lead.payload.preferred_time)],
            ];
            const availablePayloadDetails = payloadDetails.filter(
              (detail): detail is [string, string] => Boolean(detail[1]),
            );

            return (
              <article key={lead.id} className="rounded border border-line bg-white p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">{lead.customer_payload.name}</p>
                    {email ? (
                      <p className="mt-1 text-sm text-slate-600">{email}</p>
                    ) : null}
                    {phone ? (
                      <p className="mt-1 text-sm text-slate-600">{phone}</p>
                    ) : null}
                  </div>
                  <p className="text-sm text-slate-500">
                    {humanizeCallValue(lead.status)}
                  </p>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <dt className="text-slate-500">Source</dt>
                    <dd className="mt-1">{lead.source}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Status</dt>
                    <dd className="mt-1">{humanizeCallValue(lead.status)}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Created</dt>
                    <dd className="mt-1">
                      {formatActivityTimestamp(lead.created_at)}
                    </dd>
                  </div>
                </dl>

                {availablePayloadDetails.length > 0 ? (
                  <dl className="mt-4 grid gap-3 border-t border-line pt-4 text-sm sm:grid-cols-3">
                    {availablePayloadDetails.map(([label, value]) => (
                      <div key={label}>
                        <dt className="text-slate-500">{label}</dt>
                        <dd className="mt-1">{value}</dd>
                      </div>
                    ))}
                  </dl>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}

function AgentsView({
  agents,
  state,
}: {
  agents: AgentApiItem[];
  state: AgentsState;
}) {
  return (
    <>
      <header className="border-b border-line pb-5">
        <p className="text-sm font-medium text-brand">Workspace</p>
        <h2 className="mt-1 text-2xl font-semibold">Agents</h2>
        <p className="mt-1 text-sm text-slate-600">AI voice agents</p>
      </header>

      {state === "loading" ? (
        <p className="mt-6 text-sm text-slate-600">Loading agents...</p>
      ) : state === "error" ? (
        <p className="mt-6 text-sm text-slate-600">Unable to load agents.</p>
      ) : state === "ready" && agents.length === 0 ? (
        <p className="mt-6 text-sm text-slate-600">No agents configured.</p>
      ) : (
        <div className="mt-6 space-y-3">
          {agents.map((agent) => {
            const voice = textValue(agent.voice);
            const personality = textValue(agent.personality);

            return (
              <article key={agent.id} className="rounded border border-line bg-white p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <p className="text-sm font-medium">{agent.name}</p>
                  <span
                    className={`w-fit rounded px-2 py-1 text-xs font-medium ${
                      agent.is_active
                        ? "bg-emerald-50 text-emerald-700"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {agent.is_active ? "Active" : "Inactive"}
                  </span>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <dt className="text-slate-500">Language</dt>
                    <dd className="mt-1">{agent.language}</dd>
                  </div>
                  {voice ? (
                    <div>
                      <dt className="text-slate-500">Voice</dt>
                      <dd className="mt-1">{voice}</dd>
                    </div>
                  ) : null}
                  <div>
                    <dt className="text-slate-500">Created</dt>
                    <dd className="mt-1">
                      {formatActivityTimestamp(agent.created_at)}
                    </dd>
                  </div>
                </dl>

                {personality ? (
                  <p className="mt-4 border-t border-line pt-4 text-sm text-slate-600">
                    {personality}
                  </p>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}

function AppointmentsView({
  appointments,
  state,
}: {
  appointments: AppointmentEvent[];
  state: AppointmentsState;
}) {
  return (
    <>
      <header className="border-b border-line pb-5">
        <p className="text-sm font-medium text-brand">Workspace</p>
        <h2 className="mt-1 text-2xl font-semibold">Appointments</h2>
        <p className="mt-1 text-sm text-slate-600">
          Scheduled customer visits and appointments
        </p>
      </header>

      {state === "loading" ? (
        <p className="mt-6 text-sm text-slate-600">Loading appointments...</p>
      ) : state === "error" ? (
        <p className="mt-6 text-sm text-slate-600">Unable to load appointments.</p>
      ) : state === "ready" && appointments.length === 0 ? (
        <p className="mt-6 text-sm text-slate-600">No appointments scheduled.</p>
      ) : (
        <div className="mt-6 space-y-3">
          {appointments.map((appointment) => {
            const nestedAppointment = recordValue(appointment.payload.appointment);
            const payloadValue = (field: string) =>
              nestedAppointment?.[field] ?? appointment.payload[field];
            const email = textValue(appointment.customer_payload.email);
            const phone = textValue(appointment.customer_payload.phone);
            const appointmentType = textValue(payloadValue("appointment_type"));
            const service = payloadDisplayValue(payloadValue("service"));
            const propertyType = payloadDisplayValue(payloadValue("property_type"));
            const location = payloadDisplayValue(payloadValue("location"));
            const date =
  payloadDisplayValue(payloadValue("scheduled_date")) ??
  payloadDisplayValue(payloadValue("date")) ??
  payloadDisplayValue(payloadValue("preferred_date"));

const time =
  payloadDisplayValue(payloadValue("scheduled_time")) ??
  payloadDisplayValue(payloadValue("time")) ??
  payloadDisplayValue(payloadValue("preferred_time"));
            const schedule = [date, time].filter(Boolean).join(" at ");
            const details: Array<[string, string | undefined]> = [
              ["Service", service],
              ["Property type", propertyType],
              ["Location", location],
            ];
            const availableDetails = details.filter(
              (detail): detail is [string, string] => Boolean(detail[1]),
            );

            return (
              <article
                key={appointment.id}
                className="rounded border border-line bg-white p-4"
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">
                      {appointment.customer_payload.name}
                    </p>
                    {email ? (
                      <p className="mt-1 text-sm text-slate-600">{email}</p>
                    ) : null}
                    {phone ? (
                      <p className="mt-1 text-sm text-slate-600">{phone}</p>
                    ) : null}
                  </div>
                  <p className="text-sm text-slate-500">
                    {humanizeCallValue(appointment.status)}
                  </p>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <dt className="text-slate-500">Type</dt>
                    <dd className="mt-1">
                      {appointmentType === "site_visit" ? "Site visit" : "Appointment"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Scheduled</dt>
                    <dd className="mt-1">{schedule || "Not scheduled"}</dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Created</dt>
                    <dd className="mt-1">
                      {formatActivityTimestamp(appointment.created_at)}
                    </dd>
                  </div>
                </dl>

                {availableDetails.length > 0 ? (
                  <dl className="mt-4 grid gap-3 border-t border-line pt-4 text-sm sm:grid-cols-3">
                    {availableDetails.map(([label, value]) => (
                      <div key={label}>
                        <dt className="text-slate-500">{label}</dt>
                        <dd className="mt-1">{value}</dd>
                      </div>
                    ))}
                  </dl>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}


function WorkflowsView({
  workflows,
  state,
  onEnabledChange,
  updatingWorkflowId,
  updateError,
}: {
  workflows: WorkflowApiItem[];
  state: WorkflowsState;
  onEnabledChange: (workflowId: string, enabled: boolean) => Promise<void>;
  updatingWorkflowId: string | null;
  updateError: string | null;
}) {
  return (
    <>
      <header className="border-b border-line pb-5">
        <p className="text-sm font-medium text-brand">Workspace</p>
        <h2 className="mt-1 text-2xl font-semibold">Workflows</h2>
        <p className="mt-1 text-sm text-slate-600">
          Automation rules for incoming leads and appointments
        </p>
      </header>
      {updateError ? (
  <p role="alert" className="mt-4 text-sm text-red-600">
    {updateError}
  </p>
) : null}

      {state === "loading" ? (
        <p className="mt-6 text-sm text-slate-600">Loading workflows...</p>
      ) : state === "error" ? (
        <p className="mt-6 text-sm text-slate-600">
          Unable to load workflows.
        </p>
      ) : state === "ready" && workflows.length === 0 ? (
        <p className="mt-6 text-sm text-slate-600">
          No workflows configured.
        </p>
      ) : (
        <div className="mt-6 space-y-3">
          {workflows.map((workflow) => {
            const objective = textValue(workflow.config.objective);

            return (
              <article
                key={workflow.id}
                className="rounded border border-line bg-white p-4"
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">{workflow.name}</p>
                    <p className="mt-1 text-sm text-slate-600">
                      {workflow.trigger.replace(/[._]/g, " ")}
                    </p>
                  </div>

                  
<div className="flex items-center gap-2">
  <span
    className={`w-fit rounded px-2 py-1 text-xs font-medium ${
      workflow.enabled
        ? "bg-emerald-50 text-emerald-700"
        : "bg-slate-100 text-slate-600"
    }`}
  >
    {workflow.enabled ? "Enabled" : "Disabled"}
  </span>

  <button
    type="button"
    onClick={() =>
      void onEnabledChange(workflow.id, !workflow.enabled)
    }
    disabled={updatingWorkflowId === workflow.id}
    className="rounded border border-line px-3 py-1 text-xs font-medium hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
  >
    {updatingWorkflowId === workflow.id
      ? "Updating..."
      : workflow.enabled
        ? "Disable"
        : "Enable"}
  </button>
</div>
                </div>

                <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <dt className="text-slate-500">Action</dt>
                    <dd className="mt-1">
                      {humanizeCallValue(workflow.action)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Timing</dt>
                    <dd className="mt-1">
                      {humanizeCallValue(workflow.timing)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-slate-500">Created</dt>
                    <dd className="mt-1">
                      {formatActivityTimestamp(workflow.created_at)}
                    </dd>
                  </div>
                </dl>

                {objective ? (
                  <p className="mt-4 border-t border-line pt-4 text-sm text-slate-600">
                    Objective: {objective}
                  </p>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded border border-line bg-white p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}
