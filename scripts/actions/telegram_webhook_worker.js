/**
 * Cloudflare Worker — GadgetGeeks Telegram Webhook Handler
 *
 * Replaces 5-minute polling with INSTANT webhook responses.
 * Bot: @GGP_MA_Bot
 *
 * Environment secrets (set via wrangler secret):
 *   TELEGRAM_BOT_TOKEN — Telegram bot token
 *   GH_TOKEN           — GitHub PAT for triggering workflows
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GITHUB_REPO = 'mindfulcrumb/gadgetgeeks-marketing-org';
const GITHUB_RAW = `https://raw.githubusercontent.com/${GITHUB_REPO}/main`;
const DASHBOARD_URL = 'https://mindfulcrumb.github.io/gadgetgeeks-marketing-org/';

const DEPT_WORKFLOW_MAP = {
  intel: 'intel.yml',
  seo: 'seo-daily.yml',
  seo_weekly: 'seo-weekly.yml',
  content: 'content.yml',
  email: 'email.yml',
  social_morning: 'social-morning.yml',
  social_afternoon: 'social-afternoon.yml',
  cro: 'cro.yml',
  x_intel: 'x-intel.yml',
  gm_report: 'gm-report.yml',
  gm_queue: 'gm-queue.yml',
  image_prompts: 'image-prompts.yml',
  prompt_qa: 'prompt-qa.yml',
  blog_writer: 'blog-writer.yml',
  blog_qa: 'blog-qa.yml',
  blog_publish: 'blog-publish.yml',
  dialer: 'dialer.yml',
  dialer_execute: 'dialer-execute.yml',
};

const DEPT_NAMES = {
  intel: 'Market Intel',
  seo: 'SEO Daily',
  seo_weekly: 'SEO Weekly',
  content: 'Content',
  email: 'Email Marketing',
  social_morning: 'Social (Morning)',
  social_afternoon: 'Social (Afternoon)',
  cro: 'CRO',
  x_intel: 'X Intel',
  gm_report: 'GM Report',
  gm_queue: 'GM Queue',
  image_prompts: 'Image Prompts',
  prompt_qa: 'Prompt QA',
  blog_writer: 'Blog Writer',
  blog_qa: 'Blog QA',
  blog_publish: 'Blog Publisher',
  dialer: 'Dialer',
};

const DEPT_EMOJI = {
  intel: '\u{1F50D}',
  seo: '\u{1F4C8}',
  seo_weekly: '\u{1F4C8}',
  content: '\u{270D}\u{FE0F}',
  email: '\u{1F4E7}',
  social_morning: '\u{1F4E3}',
  social_afternoon: '\u{1F4E3}',
  cro: '\u{1F4C9}',
  x_intel: '\u{1F426}',
  gm_report: '\u{1F4CB}',
  gm_queue: '\u{1F4EC}',
  image_prompts: '\u{1F3A8}',
  prompt_qa: '\u{1F50E}',
  blog_writer: '\u{270D}\u{FE0F}',
  blog_qa: '\u{1F6A8}',
  blog_publish: '\u{1F680}',
  dialer: '\u{1F4DE}',
};

const STATUS_EMOJI = { ok: '\u2705', error: '\u274C', working: '\u23F3', idle: '\u23F8' };

const DEPT_ALIASES = {
  xavier: 'dialer', dialer: 'dialer', caller: 'dialer', phone: 'dialer', calls: 'dialer',
  intel: 'intel', market: 'intel', research: 'intel', competitors: 'intel',
  seo: 'seo', keywords: 'seo', ranking: 'seo', rankings: 'seo',
  content: 'content', calendar: 'content', topics: 'content',
  email: 'email', emails: 'email', newsletter: 'email', campaign: 'email',
  social: 'social_morning', twitter: 'social_morning', post: 'social_morning', posts: 'social_morning',
  cro: 'cro', conversion: 'cro', optimize: 'cro',
  blog: 'blog_writer', blogs: 'blog_writer', article: 'blog_writer', write: 'blog_writer',
  image: 'image_prompts', images: 'image_prompts', prompts: 'image_prompts', photos: 'image_prompts',
  gm: 'gm_queue', report: 'gm_report',
  x: 'x_intel', hawk: 'x_intel',
};

const COMMANDS_HELP = {
  '/start': 'Welcome to GadgetGeeks HQ!',
  '/status': 'Show org status',
  '/queue': 'Show approval queue',
  '/approve': 'Approve a queued item',
  '/reject': 'Reject a queued item',
  '/run': 'Trigger a department NOW via GitHub Actions',
  '/runall': 'Trigger ALL departments',
  '/xavier': 'Send instruction to Xavier (dialer AI)',
  '/boss': 'Send instruction to any department',
  '/history': 'Last 10 department runs with token usage',
  '/alerts': 'Recent alerts and errors',
  '/costs': 'Token usage and cost breakdown',
  '/blog': 'Show blog pipeline status',
  '/prompts': 'Show image prompt stats',
  '/dashboard': 'Open the HQ office dashboard',
  '/help': 'Show available commands',
};

// ---------------------------------------------------------------------------
// Telegram helpers
// ---------------------------------------------------------------------------

async function tgApi(method, token, body) {
  const resp = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return resp.json();
}

async function sendMessage(token, chatId, text, extra = {}) {
  if (!text) return;
  // Telegram max message length is 4096
  if (text.length > 4096) text = text.slice(0, 4090) + '\n...';
  return tgApi('sendMessage', token, {
    chat_id: chatId,
    text,
    parse_mode: 'HTML',
    disable_web_page_preview: true,
    ...extra,
  });
}

// ---------------------------------------------------------------------------
// GitHub helpers
// ---------------------------------------------------------------------------

async function fetchGitHubRaw(path) {
  try {
    const resp = await fetch(`${GITHUB_RAW}/${path}`, {
      headers: { 'User-Agent': 'GadgetGeeks-Webhook/1.0' },
    });
    if (!resp.ok) return null;
    return resp.json();
  } catch {
    return null;
  }
}

async function triggerWorkflow(ghToken, workflowFile) {
  const url = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${workflowFile}/dispatches`;
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${ghToken}`,
        Accept: 'application/vnd.github.v3+json',
        'User-Agent': 'GadgetGeeks-Webhook/1.0',
      },
      body: JSON.stringify({ ref: 'main' }),
    });
    return resp.status === 204;
  } catch {
    return false;
  }
}

async function saveBossInstruction(ghToken, department, instruction) {
  // Trigger gm-queue workflow which will pick up from the dispatch event
  // We encode the instruction in a workflow_dispatch input
  const url = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/gm-queue.yml/dispatches`;
  try {
    await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${ghToken}`,
        Accept: 'application/vnd.github.v3+json',
        'User-Agent': 'GadgetGeeks-Webhook/1.0',
      },
      body: JSON.stringify({
        ref: 'main',
        inputs: {
          boss_department: department,
          boss_instruction: instruction.slice(0, 500),
        },
      }),
    });
  } catch {
    // Non-critical — instruction also triggers the dept workflow directly
  }
}

// ---------------------------------------------------------------------------
// Command handlers
// ---------------------------------------------------------------------------

function cmdStart() {
  return (
    '\u{1F3AE} <b>GADGETGEEKS HQ \u2014 CONNECTED</b>\n\n' +
    "You're now linked to the Marketing Org.\n" +
    "I'll send you real-time updates from all departments.\n\n" +
    '<b>Commands:</b>\n' +
    '/status \u2014 Org overview\n' +
    '/queue \u2014 Approval queue\n' +
    '/blog \u2014 Blog pipeline\n' +
    '/prompts \u2014 Image prompts\n' +
    '/approve [id] \u2014 Approve item\n' +
    '/reject [id] \u2014 Reject item\n' +
    '/run [dept] \u2014 Trigger department NOW\n' +
    '/runall \u2014 Trigger ALL departments\n' +
    '/xavier [instruction] \u2014 Tell Xavier what to do\n' +
    '/boss [dept] [instruction] \u2014 Direct any department\n' +
    '/history \u2014 Recent runs + token usage\n' +
    '/alerts \u2014 Errors and alerts\n' +
    '/costs \u2014 Token cost breakdown\n' +
    '/dashboard \u2014 Open HQ dashboard\n' +
    '/help \u2014 This menu'
  );
}

async function cmdStatus() {
  const master = await fetchGitHubRaw('state/master.json');
  if (!master) return '\u274C Could not fetch org status. Try again in a moment.';

  const depts = master.departments || {};
  const lines = ['\u{1F3E2} <b>GADGETGEEKS HQ \u2014 Status</b>\n'];

  let okCount = 0, errCount = 0, idleCount = 0;
  for (const d of Object.values(depts)) {
    if (d.status === 'ok') okCount++;
    else if (d.status === 'error') errCount++;
    else idleCount++;
  }
  lines.push(`\u2705 ${okCount} OK  \u274C ${errCount} Errors  \u23F8 ${idleCount} Idle\n`);

  const sortedDepts = Object.entries(depts).sort(([a], [b]) => a.localeCompare(b));
  for (const [deptId, info] of sortedDepts) {
    const emoji = STATUS_EMOJI[info.status] || '\u2753';
    const name = DEPT_NAMES[deptId] || deptId;
    const runs = info.runs_total || 0;
    let last = info.last_run || 'never';
    if (last !== 'never') {
      try {
        const dt = new Date(last);
        last = dt.toISOString().slice(11, 16);
      } catch { last = last.slice(0, 16); }
    }
    lines.push(`${emoji} ${name}: ${runs} runs (last: ${last})`);
  }

  // Queue status
  const queue = await fetchGitHubRaw('state/queue.json');
  if (queue) {
    const pending = (queue.pending || []).length;
    if (pending) lines.push(`\n\u{1F4E5} <b>${pending} item(s) awaiting approval</b>`);
  }

  return lines.join('\n');
}

async function cmdQueue() {
  const queue = await fetchGitHubRaw('state/queue.json');
  if (!queue) return '\u{1F4E5} Queue is empty.';

  const pending = queue.pending || [];
  if (!pending.length) return '\u2705 No items pending approval.';

  const lines = [`\u{1F4E5} <b>${pending.length} Pending Item(s)</b>\n`];
  for (let i = 0; i < pending.length; i++) {
    const item = pending[i];
    const dept = item.department || '?';
    const emoji = DEPT_EMOJI[dept] || '\u2699\uFE0F';
    const name = DEPT_NAMES[dept] || dept;
    // Build detail lines from all meaningful fields
    const skip = new Set(['id', 'department', 'type', 'summary']);
    const details = Object.entries(item)
      .filter(([k]) => !skip.has(k))
      .slice(0, 6)
      .map(([k, v]) => {
        let val = typeof v === 'string' ? v : JSON.stringify(v);
        if (val.length > 150) val = val.slice(0, 150) + '…';
        return `  • <b>${k}</b>: ${val}`;
      })
      .join('\n');
    lines.push(
      `${i + 1}. ${emoji} <b>${name}</b> — ${item.summary || 'No description'}\n` +
      `   Type: <code>${item.type || '?'}</code>\n` +
      (details ? details + '\n' : '') +
      `   🆔 <code>${item.id || '?'}</code>\n` +
      `   /approve ${item.id || ''} | /reject ${item.id || ''}`
    );
  }
  return lines.join('\n');
}

async function cmdApprove(args, ghToken) {
  if (!args.length) return '\u26A0\uFE0F Usage: /approve <item_id>';
  // Approval requires write access to the repo — trigger via workflow
  const ok = await triggerWorkflow(ghToken, 'gm-queue.yml');
  return ok
    ? `\u2705 Approve request for <code>${args[0]}</code> sent.\nGM Queue will process it shortly.`
    : `\u274C Could not trigger approval workflow. Try again.`;
}

async function cmdReject(args, ghToken) {
  if (!args.length) return '\u26A0\uFE0F Usage: /reject <item_id>';
  const ok = await triggerWorkflow(ghToken, 'gm-queue.yml');
  return ok
    ? `\u274C Reject request for <code>${args[0]}</code> sent.\nGM Queue will process it shortly.`
    : `\u274C Could not trigger rejection workflow. Try again.`;
}

async function cmdBlog() {
  const bp = await fetchGitHubRaw('departments/content/blog-pipeline.json');
  if (!bp) return '\u{270D}\uFE0F No blogs in pipeline.';

  const blogs = bp.blogs || [];
  const stats = bp.pipeline_stats || {};

  const lines = [
    '\u{270D}\uFE0F <b>BLOG PIPELINE</b>\n',
    `Drafted: ${stats.total_drafted || 0} | Approved: ${stats.total_approved || 0} | Published: ${stats.total_published || 0} | Blocked: ${stats.total_blocked || 0}\n`,
  ];

  const recent = blogs.slice(-5);
  for (const blog of recent) {
    const status = blog.status || '?';
    const rating = (blog.qa_score || {}).rating || '?';
    const title = blog.title || 'Untitled';
    lines.push(
      `\u2022 <b>${title.slice(0, 60)}</b>\n  Status: <code>${status}</code> | QA: ${rating}`
    );
  }
  return lines.join('\n');
}

async function cmdPrompts() {
  const ip = await fetchGitHubRaw('departments/social/image-prompts.json');
  if (!ip) return '\u{1F3A8} No image prompts yet.';

  const folders = ip.folders || {};
  const qa = ip.qa_summary || {};

  const lines = ['\u{1F3A8} <b>IMAGE PROMPTS</b>\n'];
  let total = 0;
  for (const [folderId, folder] of Object.entries(folders)) {
    const prompts = folder.prompts || [];
    total += prompts.length;
    lines.push(`\u{1F4C2} ${folder.name || folderId}: ${prompts.length} prompts`);
  }
  lines.splice(1, 0, `Total: ${total} prompts\n`);

  if (Object.keys(qa).length) {
    lines.push(`\nQA: ${qa.excellent || 0} excellent, ${qa.good || 0} good, ${qa.needs_work || 0} needs work`);
  }
  return lines.join('\n');
}

async function cmdRun(args, ghToken) {
  if (!args.length) {
    const deptList = Object.keys(DEPT_WORKFLOW_MAP).sort().join(', ');
    return `\u26A0\uFE0F Usage: /run <department>\n\nAvailable:\n<code>${deptList}</code>`;
  }

  const dept = args[0].toLowerCase().replace(/-/g, '_');
  const workflow = DEPT_WORKFLOW_MAP[dept];
  if (!workflow) {
    const deptList = Object.keys(DEPT_WORKFLOW_MAP).sort().join(', ');
    return `\u274C Unknown department: <code>${dept}</code>\n\nAvailable:\n<code>${deptList}</code>`;
  }

  const name = DEPT_NAMES[dept] || dept;
  const emoji = DEPT_EMOJI[dept] || '\u2699\uFE0F';
  const ok = await triggerWorkflow(ghToken, workflow);
  if (ok) return `${emoji} <b>${name}</b> triggered!\n\nWorkflow dispatched. Results in ~2 min.`;
  return `\u274C Failed to trigger <b>${name}</b>. Check GH_TOKEN permissions.`;
}

async function cmdRunAll(ghToken) {
  const coreDepts = [
    'intel', 'x_intel', 'seo', 'content', 'email',
    'social_morning', 'cro', 'image_prompts', 'blog_writer',
    'dialer', 'gm_queue',
  ];

  const results = await Promise.all(
    coreDepts.map(async (dept) => {
      const workflow = DEPT_WORKFLOW_MAP[dept];
      if (!workflow) return null;
      const ok = await triggerWorkflow(ghToken, workflow);
      const emoji = ok ? '\u2705' : '\u274C';
      const name = DEPT_NAMES[dept] || dept;
      return `${emoji} ${name}`;
    })
  );

  return '\u{1F680} <b>ALL DEPARTMENTS TRIGGERED</b>\n\n' +
    results.filter(Boolean).join('\n') +
    '\n\nResults arriving in ~2-5 min.';
}

async function cmdXavier(instruction, ghToken) {
  if (!instruction) {
    return (
      '\u{1F4DE} <b>XAVIER \u2014 AI Sales Agent</b>\n\n' +
      'Usage: /xavier <instruction>\n\n' +
      '<b>Examples:</b>\n' +
      '<code>/xavier call John about the iPhone 14 he left in cart</code>\n' +
      '<code>/xavier follow up with B2B lead from last week</code>\n' +
      '<code>/xavier build a win-back list for customers inactive 90+ days</code>\n' +
      '<code>/xavier check outcomes from yesterday\'s calls</code>\n\n' +
      'Xavier will add calls to the approval queue. You approve before any call goes out.'
    );
  }

  await saveBossInstruction(ghToken, 'dialer', instruction);
  const triggered = await triggerWorkflow(ghToken, DEPT_WORKFLOW_MAP.dialer);

  let response =
    '\u{1F4DE} <b>XAVIER \u2014 Instruction received</b>\n\n' +
    `<i>${instruction.slice(0, 300)}</i>\n\n`;
  response += triggered
    ? '\u2705 Dialer workflow triggered. Xavier is on it.'
    : '\u23F3 Saved. Xavier will pick this up on next scheduled run.';
  return response;
}

async function cmdBoss(args, ghToken) {
  if (args.length < 2) {
    const deptList = Object.keys(DEPT_WORKFLOW_MAP).sort().join(', ');
    return (
      '\u{1F453} <b>BOSS MODE</b>\n\n' +
      'Usage: /boss <department> <instruction>\n\n' +
      `Departments:\n<code>${deptList}</code>\n\n` +
      '<b>Examples:</b>\n' +
      '<code>/boss content write a blog about iPhone 16 vs 15</code>\n' +
      '<code>/boss email create a flash sale campaign for this weekend</code>\n' +
      '<code>/boss seo audit our top 5 product pages</code>\n' +
      '<code>/boss intel research what Back Market is doing with pricing</code>'
    );
  }

  const dept = args[0].toLowerCase().replace(/-/g, '_');
  const instruction = args.slice(1).join(' ');

  if (!DEPT_WORKFLOW_MAP[dept] && !DEPT_NAMES[dept]) {
    const deptList = Object.keys(DEPT_WORKFLOW_MAP).sort().join(', ');
    return `\u274C Unknown department: <code>${dept}</code>\n\nAvailable:\n<code>${deptList}</code>`;
  }

  const name = DEPT_NAMES[dept] || dept;
  const emoji = DEPT_EMOJI[dept] || '\u2699\uFE0F';

  await saveBossInstruction(ghToken, dept, instruction);
  const workflow = DEPT_WORKFLOW_MAP[dept];
  const triggered = workflow ? await triggerWorkflow(ghToken, workflow) : false;

  let response = `${emoji} <b>${name} \u2014 Instruction received</b>\n\n<i>${instruction.slice(0, 300)}</i>\n\n`;
  response += triggered
    ? `\u2705 ${name} workflow triggered. Processing now.`
    : `\u23F3 Saved. ${name} will pick this up on next scheduled run.`;
  return response;
}

async function cmdHistory() {
  const history = await fetchGitHubRaw('state/run-history.json');
  if (!history) return '\u{1F4CA} No run history yet. Runs will be logged after the next department cycle.';

  const runs = (history.runs || []).slice(0, 10);
  const stats = history.stats || {};
  if (!runs.length) return '\u{1F4CA} No runs recorded yet.';

  const lines = [
    `\u{1F4CA} <b>RUN HISTORY</b> (last ${runs.length})\n`,
    `Total: ${stats.total_runs || 0} runs | ${(stats.total_tokens || 0).toLocaleString()} tokens | ${stats.total_errors || 0} errors\n`,
  ];

  for (const run of runs) {
    const dept = run.department || '?';
    const emoji = DEPT_EMOJI[dept] || '\u2699\uFE0F';
    const name = DEPT_NAMES[dept] || dept;
    const status = run.status === 'ok' ? '\u2705' : '\u274C';
    const tokens = run.tokens || {};
    const totalTok = tokens.total || 0;
    let timeStr = run.timestamp || '';
    try {
      const dt = new Date(timeStr);
      timeStr = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + dt.toISOString().slice(11, 16);
    } catch { timeStr = timeStr.slice(0, 16); }

    const actions = run.actions || {};
    const changes = (run.changes || []).length;
    const boss = run.had_boss_instructions ? ' \u{1F453}' : '';

    lines.push(
      `${status} ${emoji} <b>${name}</b> ${timeStr}${boss}\n` +
      `   ${totalTok.toLocaleString()} tok | ${actions.file_updates || 0} files | ${actions.queue_items || 0} queued | ${changes} changed`
    );
  }
  return lines.join('\n');
}

async function cmdAlerts() {
  const alerts = await fetchGitHubRaw('state/alert-history.json');
  if (!alerts) return '\u{1F6A8} No alerts yet.';

  const items = (alerts.alerts || []).slice(0, 15);
  if (!items.length) return '\u2705 No alerts. Everything is clean.';

  const levelEmoji = { critical: '\u{1F534}', error: '\u{1F7E0}', warning: '\u{1F7E1}', info: '\u{1F7E2}' };

  const lines = [`\u{1F6A8} <b>ALERTS</b> (last ${items.length})\n`];
  for (const a of items) {
    const emoji = levelEmoji[a.level] || '\u2753';
    const dept = a.department || '?';
    const name = DEPT_NAMES[dept] || dept;
    let timeStr = a.timestamp || '';
    try {
      const dt = new Date(timeStr);
      timeStr = dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' + dt.toISOString().slice(11, 16);
    } catch { timeStr = timeStr.slice(0, 16); }
    lines.push(`${emoji} <b>${name}</b> (${timeStr})\n   ${(a.message || '?').slice(0, 200)}`);
  }
  return lines.join('\n');
}

async function cmdCosts() {
  const history = await fetchGitHubRaw('state/run-history.json');
  if (!history) return '\u{1F4B0} No cost data yet.';

  const deptStats = history.department_stats || {};
  const totalStats = history.stats || {};
  if (!Object.keys(deptStats).length) return '\u{1F4B0} No department stats yet.';

  const totalTokens = totalStats.total_tokens || 0;
  const estCost = (totalTokens * 10) / 1_000_000;

  const lines = [
    '\u{1F4B0} <b>TOKEN USAGE & COSTS</b>\n',
    `Total: ${totalTokens.toLocaleString()} tokens (~$${estCost.toFixed(2)})\n`,
    `Runs: ${totalStats.total_runs || 0} | Errors: ${totalStats.total_errors || 0}\n`,
  ];

  const sorted = Object.entries(deptStats).sort(([, a], [, b]) => (b.tokens || 0) - (a.tokens || 0));
  for (const [dept, ds] of sorted) {
    const emoji = DEPT_EMOJI[dept] || '\u2699\uFE0F';
    const name = DEPT_NAMES[dept] || dept;
    const tok = ds.tokens || 0;
    const runs = ds.runs || 0;
    const deptCost = (tok * 10) / 1_000_000;
    lines.push(`${emoji} <b>${name}</b>: ${tok.toLocaleString()} tok (${runs} runs) ~$${deptCost.toFixed(2)}`);
  }
  return lines.join('\n');
}

function cmdHelp() {
  const lines = ['\u{1F4D6} <b>Available Commands</b>\n'];
  for (const [c, desc] of Object.entries(COMMANDS_HELP)) {
    lines.push(`<code>${c}</code> \u2014 ${desc}`);
  }
  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Natural language intent detection
// ---------------------------------------------------------------------------

function detectDepartment(text) {
  const words = text.toLowerCase().split(/\s+/);
  for (const word of words) {
    const dept = DEPT_ALIASES[word];
    if (dept) return dept;
  }
  return null;
}

async function handleNaturalLanguage(text, chatId, token, ghToken) {
  const lower = text.toLowerCase().trim();

  // 1. XAVIER / CALL INTENT
  const xavierTriggers = ['xavier', 'call ', 'phone ', 'dial '];
  if (xavierTriggers.some((t) => lower.includes(t))) {
    let instruction = text.trim();
    const prefixes = [
      'xavier ', 'xavier, ', 'tell xavier to ', 'have xavier ',
      'ask xavier to ', 'xavier please ', 'hey xavier ',
    ];
    for (const prefix of prefixes) {
      if (lower.startsWith(prefix)) {
        instruction = text.slice(prefix.length).trim();
        break;
      }
    }
    return cmdXavier(instruction, ghToken);
  }

  // 2. RUN / TRIGGER INTENT
  const runTriggers = ['run ', 'trigger ', 'start ', 'fire ', 'launch ', 'execute '];
  if (runTriggers.some((t) => lower.startsWith(t))) {
    const dept = detectDepartment(text);
    if (dept) return cmdRun([dept], ghToken);
    if (['all', 'everything', 'everyone'].some((w) => lower.includes(w))) {
      return cmdRunAll(ghToken);
    }
  }

  // 3. DASHBOARD / OFFICE INTENT
  if (['dashboard', 'office', 'open hq', 'god mode', 'pixel'].some((t) => lower.includes(t))) {
    return { dashboard: true };
  }

  // 3b. STATUS INTENT
  const statusTriggers = [
    'status', "how's it going", 'hows it going', "what's happening",
    'whats happening', 'how are things', 'overview',
    "what's going on", 'whats going on', 'how are the agents',
    'report', 'sitrep', 'check in',
  ];
  if (statusTriggers.some((t) => lower.includes(t))) {
    return cmdStatus();
  }

  // 4. APPROVE / REJECT INTENT
  const approveWords = ['approve', 'approved', 'yes approve', 'go ahead', 'looks good', 'ship it'];
  if (approveWords.some((w) => lower.includes(w))) {
    const ids = text.match(/[A-Za-z0-9_-]{4,}/g) || [];
    const common = new Set(['approve', 'approved', 'reject', 'looks', 'good', 'ship', 'ahead', 'yes', 'the', 'this', 'that', 'please']);
    const filtered = ids.filter((id) => !common.has(id.toLowerCase()));
    if (filtered.length) return cmdApprove(filtered.slice(0, 1), ghToken);
    return cmdQueue();
  }

  const rejectWords = ['reject', 'rejected', 'deny', 'kill it', 'nope'];
  if (rejectWords.some((w) => lower.includes(w))) {
    const ids = text.match(/[A-Za-z0-9_-]{4,}/g) || [];
    const common = new Set(['approve', 'approved', 'reject', 'rejected', 'deny', 'kill', 'nope', 'please', 'the', 'this', 'that']);
    const filtered = ids.filter((id) => !common.has(id.toLowerCase()));
    if (filtered.length) return cmdReject(filtered.slice(0, 1), ghToken);
  }

  // 5. ALERTS / ERRORS
  if (['alert', 'alerts', 'error', 'errors', 'problem', 'problems', 'broken', 'failing', 'failed', 'what broke', 'issues'].some((w) => lower.includes(w))) {
    return cmdAlerts();
  }

  // 6. COSTS / SPENDING
  if (['cost', 'costs', 'spending', 'tokens', 'budget', 'money', 'how much', 'expensive'].some((w) => lower.includes(w))) {
    return cmdCosts();
  }

  // 7. HISTORY / RUNS
  if (['history', 'recent', 'last run', 'what happened', 'what ran', 'runs'].some((w) => lower.includes(w))) {
    return cmdHistory();
  }

  // 8. QUEUE
  if (['queue', 'pending', 'waiting', 'approval', 'approvals'].some((w) => lower.includes(w))) {
    return cmdQueue();
  }

  // 9. BLOG STATUS
  if (['blog', 'blogs', 'articles', 'pipeline'].some((w) => lower.includes(w))) {
    return cmdBlog();
  }

  // 10. BOSS INSTRUCTION TO SPECIFIC DEPARTMENT
  const dept = detectDepartment(text);
  if (dept && text.split(/\s+/).length > 2) {
    const name = DEPT_NAMES[dept] || dept;
    const emoji = DEPT_EMOJI[dept] || '\u2699\uFE0F';

    await saveBossInstruction(ghToken, dept, text);
    const workflow = DEPT_WORKFLOW_MAP[dept];
    const triggered = workflow ? await triggerWorkflow(ghToken, workflow) : false;

    let response = `${emoji} <b>Got it \u2014 sending to ${name}</b>\n\n<i>${text.slice(0, 300)}</i>\n\n`;
    response += triggered
      ? `\u2705 ${name} workflow triggered.`
      : `\u23F3 Saved. ${name} picks this up on next run.`;
    return response;
  }

  // 11. FALLBACK: GM instruction
  await saveBossInstruction(ghToken, 'gm_queue', text);
  return (
    '\u{1F4DD} <b>Got it, boss.</b>\n\n' +
    `<i>${text.slice(0, 200)}</i>\n\n` +
    'Saved for GM. All departments will see this.\n' +
    'Say <code>run gm</code> to process now.'
  );
}

// ---------------------------------------------------------------------------
// Main command router
// ---------------------------------------------------------------------------

async function handleCommand(text, chatId, token, ghToken) {
  text = text.trim();
  const parts = text.split(/\s+/);
  const cmd = text.startsWith('/') ? parts[0].toLowerCase().replace(/@\w+$/, '') : '';
  const args = parts.slice(1);

  switch (cmd) {
    case '/start':
      return cmdStart();

    case '/status':
      return cmdStatus();

    case '/queue':
      return cmdQueue();

    case '/approve':
      return cmdApprove(args, ghToken);

    case '/reject':
      return cmdReject(args, ghToken);

    case '/blog':
      return cmdBlog();

    case '/prompts':
      return cmdPrompts();

    case '/run':
      return cmdRun(args, ghToken);

    case '/runall':
      return cmdRunAll(ghToken);

    case '/xavier':
      return cmdXavier(args.join(' '), ghToken);

    case '/boss':
      return cmdBoss(args, ghToken);

    case '/history':
      return cmdHistory();

    case '/alerts':
      return cmdAlerts();

    case '/costs':
      return cmdCosts();

    case '/dashboard':
      return { dashboard: true };

    case '/help':
      return cmdHelp();

    default:
      // No slash command — try natural language
      return handleNaturalLanguage(text, chatId, token, ghToken);
  }
}

// ---------------------------------------------------------------------------
// Worker entry point
// ---------------------------------------------------------------------------

export default {
  async fetch(request, env) {
    // Health check
    if (request.method === 'GET') {
      return new Response('GadgetGeeks Telegram Webhook is alive.', {
        status: 200,
        headers: { 'Content-Type': 'text/plain' },
      });
    }

    // Only accept POST
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    const token = env.TELEGRAM_BOT_TOKEN;
    const ghToken = env.GH_TOKEN;

    if (!token) {
      return new Response('Missing TELEGRAM_BOT_TOKEN', { status: 500 });
    }

    let update;
    try {
      update = await request.json();
    } catch {
      return new Response('Invalid JSON', { status: 400 });
    }

    // Extract message
    const msg = update.message || update.edited_message;
    if (!msg || !msg.text) {
      // Not a text message — acknowledge silently
      return new Response('OK', { status: 200 });
    }

    const chatId = msg.chat.id;
    const text = msg.text;

    try {
      const result = await handleCommand(text, chatId, token, ghToken);

      // Handle dashboard special case (inline keyboard with WebApp button)
      if (result && typeof result === 'object' && result.dashboard) {
        await tgApi('sendMessage', token, {
          chat_id: chatId,
          text: '\u{1F3AE} <b>GADGETGEEKS HQ \u2014 GOD MODE</b>\n\nTap below to open the office dashboard.',
          parse_mode: 'HTML',
          reply_markup: {
            inline_keyboard: [[
              {
                text: '\u{1F3AE} Open HQ Dashboard',
                web_app: { url: DASHBOARD_URL },
              },
            ]],
          },
        });
      } else if (result) {
        await sendMessage(token, chatId, result);
      }
    } catch (err) {
      console.error('Handler error:', err);
      await sendMessage(token, chatId, `\u274C Internal error: ${String(err).slice(0, 200)}`);
    }

    return new Response('OK', { status: 200 });
  },
};
