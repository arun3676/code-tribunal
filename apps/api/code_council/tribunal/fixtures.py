"""Demo dockets for the Tribunal.

Fixtures:
  auth-login-001     Hero BLOCK case — rate-limit omission + middleware drift + WARDEN
  health-check-002   Clean APPROVE — small observability change, everything MET
  payment-refund-003 Heavy BLOCK — two MUST omissions + config drift, lots of agent debate
  user-profile-004   Straightforward APPROVE — profile endpoint, agents confirm and close
"""

from __future__ import annotations

from .protocol import Docket, IntentSource

# ---------------------------------------------------------------------------
# auth-login-001 — hero BLOCK
# ---------------------------------------------------------------------------

_AUTH_TICKET = """\
Implement secure login.

R1 (MUST): Add a POST /api/login endpoint.
R2 (MUST): Verify the password using bcrypt.
R3 (MUST): Rate-limit failed logins to 5 attempts per 15 minutes.
R4 (MUST): Write an audit log entry for every failed login.
R5 (MUST): Add regression tests for the login flow.

Constraint: Do NOT change the behaviour of the existing auth middleware.
"""

_AUTH_DIFF = """\
+++ b/src/routes/login.ts
@@
+import bcrypt from "bcrypt";
+import { auditLog } from "../lib/audit";
+
+router.post("/api/login", async (req, res) => {
+  const { email, password } = req.body;
+  const user = await users.findByEmail(email);
+  if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
+    auditLog("login.failed", { email, ip: req.ip });
+    return res.status(401).json({ error: "invalid credentials" });
+  }
+  return res.json({ token: issueToken(user) });
+});

+++ b/src/middleware/auth.ts
@@
-  if (!token) return res.status(401).end();
+  if (!token) {
+    // allow unauthenticated read-only access to public routes
+    if (req.method === "GET") return next();
+    return res.status(401).end();
+  }

+++ b/test/login.test.ts
@@
+test("rejects bad password", async () => {
+  const res = await request(app).post("/api/login").send({ email, password: "wrong" });
+  expect(res.status).toBe(401);
+});
"""

# ---------------------------------------------------------------------------
# health-check-002 — clean APPROVE
# ---------------------------------------------------------------------------

_CLEAN_TICKET = """\
Add a health check endpoint.

R1 (MUST): Add a GET /api/health endpoint that returns 200 with { status: "ok" }.
R2 (SHOULD): Include the git commit sha in the response.
R3 (MUST): Add a test asserting a 200 response.
"""

_CLEAN_DIFF = """\
+++ b/src/routes/health.ts
@@
+router.get("/api/health", (_req, res) => {
+  res.json({ status: "ok", sha: process.env.GIT_SHA ?? "dev" });
+});

+++ b/test/health.test.ts
@@
+test("health returns ok", async () => {
+  const res = await request(app).get("/api/health");
+  expect(res.status).toBe(200);
+  expect(res.body.status).toBe("ok");
+});
"""

# ---------------------------------------------------------------------------
# payment-refund-003 — heavy BLOCK: two MUST omissions + payment config drift
# ---------------------------------------------------------------------------

_REFUND_TICKET = """\
Implement a payment refund endpoint.

R1 (MUST): Add a POST /api/refund endpoint.
R2 (MUST): Verify the caller owns the order before issuing a refund.
R3 (MUST): Validate that the refund amount does not exceed the original charge.
R4 (MUST): Write an audit log entry for every refund attempt.
R5 (MUST): Use an idempotency key to prevent duplicate refund processing.
R6 (MUST): Add regression tests covering the success and rejection paths.

Constraint: Do NOT modify payment gateway configuration files.
"""

_REFUND_DIFF = """\
+++ b/src/routes/refund.ts
@@
+import { authenticate } from "../middleware/auth";
+import { auditLog } from "../lib/audit";
+
+router.post("/api/refund", authenticate, async (req, res) => {
+  const { orderId, amount } = req.body;
+  const order = await orders.findById(orderId);
+  if (!order || order.userId !== req.user.id) {
+    auditLog("refund.rejected", { orderId, userId: req.user.id, reason: "not owner" });
+    return res.status(403).json({ error: "not your order" });
+  }
+  auditLog("refund.initiated", { orderId, amount, userId: req.user.id });
+  await payments.issueRefund({ orderId, amount });
+  return res.json({ status: "refunded", orderId });
+});

+++ b/test/refund.test.ts
@@
+test("rejects refund for non-owner", async () => {
+  const token = await loginAs("other@example.com");
+  const res = await request(app)
+    .post("/api/refund")
+    .set("Authorization", `Bearer ${token}`)
+    .send({ orderId: "ord_abc", amount: 50 });
+  expect(res.status).toBe(403);
+});
+
+test("issues refund for order owner", async () => {
+  const token = await loginAs("owner@example.com");
+  const res = await request(app)
+    .post("/api/refund")
+    .set("Authorization", `Bearer ${token}`)
+    .send({ orderId: "ord_abc", amount: 50 });
+  expect(res.status).toBe(200);
+});

+++ b/config/payment-gateway.ts
@@
-const PAYMENT_GATEWAY = process.env.PAYMENT_GATEWAY_URL ?? "https://payments.example.com";
+const PAYMENT_GATEWAY = "https://payments-v2.example.com";
+// switched to v2 for instant refund support
"""

# ---------------------------------------------------------------------------
# user-profile-004 — clean APPROVE: auth-gated profile endpoint
# ---------------------------------------------------------------------------

_PROFILE_TICKET = """\
Add a user profile endpoint.

R1 (MUST): Add a GET /api/user/profile endpoint returning { name, email, avatar }.
R2 (MUST): Require a valid auth token — reject unauthenticated requests with 401.
R3 (MUST): Return 401 with { error: "unauthorized" } for missing or invalid tokens.
R4 (SHOULD): Add tests covering both the authenticated and unauthenticated paths.
"""

_PROFILE_DIFF = """\
+++ b/src/routes/user.ts
@@
+import { authenticate } from "../middleware/auth";
+
+router.get("/api/user/profile", authenticate, async (req, res) => {
+  const user = await users.findById(req.user.id);
+  return res.json({
+    name: user.name,
+    email: user.email,
+    avatar: user.avatarUrl ?? null,
+  });
+});

+++ b/test/user.test.ts
@@
+test("returns profile for authenticated user", async () => {
+  const token = await loginAs("alice@example.com");
+  const res = await request(app)
+    .get("/api/user/profile")
+    .set("Authorization", `Bearer ${token}`);
+  expect(res.status).toBe(200);
+  expect(res.body).toHaveProperty("name");
+  expect(res.body).toHaveProperty("email");
+});
+
+test("returns 401 for unauthenticated request", async () => {
+  const res = await request(app).get("/api/user/profile");
+  expect(res.status).toBe(401);
+  expect(res.body.error).toBe("unauthorized");
+});
"""


FIXTURES: list[Docket] = [
    Docket(
        trial_id="auth-login-001",
        title="Implement secure login",
        intent_sources=[
            IntentSource(source_ref="JIRA-481", title="Secure login", text=_AUTH_TICKET),
        ],
        diff=_AUTH_DIFF,
        touched_files=[
            "src/routes/login.ts",
            "src/middleware/auth.ts",
            "test/login.test.ts",
        ],
        touched_domains=["auth", "security"],
    ),
    Docket(
        trial_id="health-check-002",
        title="Add health check endpoint",
        intent_sources=[
            IntentSource(source_ref="JIRA-502", title="Health check", text=_CLEAN_TICKET),
        ],
        diff=_CLEAN_DIFF,
        touched_files=["src/routes/health.ts", "test/health.test.ts"],
        touched_domains=["observability"],
    ),
    Docket(
        trial_id="payment-refund-003",
        title="Payment refund endpoint",
        intent_sources=[
            IntentSource(source_ref="JIRA-617", title="Refund endpoint", text=_REFUND_TICKET),
        ],
        diff=_REFUND_DIFF,
        touched_files=[
            "src/routes/refund.ts",
            "test/refund.test.ts",
            "config/payment-gateway.ts",
        ],
        touched_domains=["payments", "security"],
    ),
    Docket(
        trial_id="user-profile-004",
        title="User profile endpoint",
        intent_sources=[
            IntentSource(source_ref="JIRA-634", title="User profile", text=_PROFILE_TICKET),
        ],
        diff=_PROFILE_DIFF,
        touched_files=["src/routes/user.ts", "test/user.test.ts"],
        touched_domains=["users"],
    ),
]

FIXTURES_BY_ID: dict[str, Docket] = {fixture.trial_id: fixture for fixture in FIXTURES}


def list_fixtures() -> list[dict]:
    """Compact summaries for the War Room "Load Demo Case" dropdown."""
    return [
        {
            "id": fixture.trial_id,
            "title": fixture.title,
            "ticket": "\n\n".join(source.text for source in fixture.intent_sources),
            "diff": fixture.diff,
            "touched_domains": fixture.touched_domains,
        }
        for fixture in FIXTURES
    ]


def get_fixture(trial_id: str) -> Docket | None:
    return FIXTURES_BY_ID.get(trial_id)
