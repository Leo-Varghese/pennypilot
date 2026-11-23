"use client";

const decisions = [
 {title:"Decimal-safe finance",decision:"Python Decimal + PostgreSQL NUMERIC",value:"Reduces avoidable rounding errors in authoritative money calculations.",tradeoff:"API money values are serialised as strings."},
 {title:"Persistent cloud data",decision:"PostgreSQL on Neon",value:"Records survive browser resets and application redeployments.",tradeoff:"Availability, migrations, backups, and connection limits require management."},
 {title:"Controlled AI",decision:"Read-only Groq AI through FastAPI",value:"Explains deterministic aggregates without receiving permission to modify records.",tradeoff:"Responses depend on provider quotas and still require verification."},
 {title:"Bank data onboarding",decision:"User-reviewed CSV import first",value:"Provides real statement ingestion without requesting passwords, OTPs, CVVs, or UPI PINs.",tradeoff:"Bank formats vary and users must review mappings."},
];

const risks = [
 ["Cross-user data exposure","Server-side ownership filters and isolation tests","Implemented"],
 ["Incorrect financial totals","Decimal arithmetic and calculation tests","Implemented"],
 ["AI hallucination","Aggregate-only context and read-only boundary","Partially controlled"],
 ["Duplicate statement imports","File digest and transaction fingerprints","Implemented"],
 ["Free-tier cold starts","Readiness endpoint and controlled retry guidance","Residual risk"],
 ["Production security assurance","Secure defaults and tests; independent audit pending","Planned"],
];

export function SolutionOverview(){
 return <div className="solution-page">
 <section className="solution-hero">
 <p className="eyebrow">CLOUD + AI SOLUTION CASE STUDY</p>
 <h2>Personal finance clarity, engineered with cloud-native architecture.</h2>
 <p>PennyPilot centralises transactions, budgets, goals, recurring payments, statement imports, analytics, and controlled AI explanations in one deployed platform.</p>
 <div className="solution-proof">
 {["Full-stack deployment","Decimal-safe calculations","User-isolated records","Read-only AI","Schema migrations","Reviewed CI/CD"].map(item=><span key={item}>{item}</span>)}
 </div>
 </section>

 <section className="solution-scr">
 <article><small>SITUATION</small><h3>Fragmented financial data</h3><p>Transactions are spread across statements, payment methods, spreadsheets, and budgeting tools.</p></article>
 <article><small>COMPLICATION</small><h3>Incorrect semantics distort insight</h3><p>Transfers, refunds, card repayments, recurring projections, and duplicate imports can misstate cash flow.</p></article>
 <article><small>RESPONSE</small><h3>A governed cloud platform</h3><p>PennyPilot combines a structured ledger, persistent storage, analytics, import controls, and read-only AI.</p></article>
 </section>

 <section className="card solution-section">
 <div><p className="eyebrow">SOLUTION ARCHITECTURE</p><h2>From interface to controlled intelligence</h2></div>
 <div className="solution-architecture simple-architecture" role="group" aria-label="PennyPilot solution architecture">
 <div className="simple-architecture-box"><b>1. User</b><span>Uses PennyPilot in a web browser</span></div>
 <div className="simple-architecture-label">Website runs on</div>
 <div className="simple-architecture-box"><b>2. Vercel</b><span>Hosts the Next.js and TypeScript website</span></div>
 <div className="simple-architecture-label">Website sends secure requests to</div>
 <div className="simple-architecture-box"><b>3. Render</b><span>Runs FastAPI, login, financial rules, and imports</span></div>
 <div className="simple-architecture-label">Backend connects to</div>
 <div className="simple-architecture-grid">
 <div className="simple-architecture-box"><b>4. Neon PostgreSQL</b><span>Stores accounts, transactions, budgets, and goals</span></div>
 <div className="simple-architecture-box"><b>5. GroqCloud AI</b><span>Explains limited financial summaries in read-only mode</span></div>
 </div>
 </div>
 <p className="muted small">Current architecture is a cost-conscious MVP using free-tier allowances. Capacity, availability, backups, and pricing must be reassessed before production scaling.</p>
 </section>

 <section className="solution-section">
 <p className="eyebrow">ARCHITECTURE DECISIONS</p><h2>Decisions, value, and trade-offs</h2>
 <div className="solution-decisions">{decisions.map(item=><article className="card" key={item.title}><h3>{item.title}</h3><b>{item.decision}</b><p>{item.value}</p><small><strong>Trade-off:</strong> {item.tradeoff}</small></article>)}</div>
 </section>

 <section className="card solution-section">
 <p className="eyebrow">RISK & CONTROL VIEW</p><h2>Transparent controls, not exaggerated claims</h2>
 <div className="table-wrap"><table><thead><tr><th>Risk</th><th>Current control</th><th>Status</th></tr></thead><tbody>{risks.map(([risk,control,status])=><tr key={risk}><td>{risk}</td><td>{control}</td><td><span className="solution-status">{status}</span></td></tr>)}</tbody></table></div>
 </section>

 <section className="solution-section solution-grid">
 <article className="card"><p className="eyebrow">CLOUD ECONOMICS</p><h3>Scaling triggers</h3><ul><li>Move backend to always-on hosting when cold starts affect adoption.</li><li>Move receipts to private object storage as volume grows.</li><li>Add distributed rate limiting when multiple API workers are used.</li><li>Reassess AI quotas and provider cost before commercial use.</li></ul></article>
 <article className="card"><p className="eyebrow">DELIVERY EVIDENCE</p><h3>What the repository demonstrates</h3><ul><li>Versioned REST API and Alembic migrations</li><li>Frontend production build and backend tests</li><li>User-isolated financial records</li><li>Controlled dependency proposals and CI</li><li>Documented risks, requirements, FinOps, and ADRs</li></ul></article>
 <article className="card"><p className="eyebrow">NEXT HARDENING STEP</p><h3>From portfolio MVP to production discipline</h3><ul><li>Email verification, password recovery, and MFA</li><li>Backup restoration testing and incident procedures</li><li>Structured logs, correlation IDs, and error tracking</li><li>Accessibility, security, and load testing</li></ul></article>
 </section>

 <section className="solution-links card">
 <div><p className="eyebrow">DOCUMENTATION</p><h2>Review the complete solution case</h2></div>
 <div className="row wrap"><a className="button" href="https://github.com/Leo-Varghese/pennypilot/tree/main/docs" target="_blank" rel="noreferrer">Solution documentation</a><a className="button" href="https://github.com/Leo-Varghese" target="_blank" rel="noreferrer">GitHub profile</a><a className="button" href="https://www.linkedin.com/in/leo-varghese-in/" target="_blank" rel="noreferrer">LinkedIn profile</a></div>
 </section>
 </div>;
}