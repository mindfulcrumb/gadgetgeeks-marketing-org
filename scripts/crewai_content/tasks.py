"""
Task definitions for the Gadget Geeks Pro content pipeline.

Four sequential tasks:
1. research_topic — Analyze trends, customer language, competitor gaps
2. write_content — Draft content using Schwartz awareness levels
3. optimize_seo — Add keywords, meta descriptions, internal links
4. quality_check — Run 23-check anti-AI scan, verify human tone
"""

import json
from pathlib import Path
from crewai import Task, Agent


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _read_file(rel_path: str) -> str:
    """Read a repo file and return its contents, or a placeholder if missing."""
    full = REPO_ROOT / rel_path
    if full.exists():
        content = full.read_text(encoding="utf-8")
        # Truncate very large files to keep token usage sane
        if len(content) > 8000:
            content = content[:8000] + "\n... [TRUNCATED]"
        return content
    return "[FILE NOT FOUND]"


def _load_intel_context() -> str:
    """Load all intel department files as formatted context."""
    files = [
        "departments/intel/customer-language.json",
        "departments/intel/trends.json",
        "departments/intel/competitors.json",
    ]
    parts = []
    for f in files:
        parts.append(f"=== {f} ===\n{_read_file(f)}")
    return "\n\n".join(parts)


def _load_seo_context() -> str:
    """Load SEO department files as formatted context."""
    files = [
        "departments/seo/keywords.json",
        "departments/seo/opportunities.json",
    ]
    parts = []
    for f in files:
        parts.append(f"=== {f} ===\n{_read_file(f)}")
    return "\n\n".join(parts)


def _load_copy_rules() -> str:
    """Load copy-rules.json checks as formatted string."""
    path = REPO_ROOT / "config" / "copy-rules.json"
    if not path.exists():
        return "[copy-rules.json not found]"
    rules = json.loads(path.read_text(encoding="utf-8"))
    checks = rules.get("checks", [])
    lines = []
    for c in checks:
        severity = c.get("severity", "info").upper()
        lines.append(f"  [{severity}] Check #{c['id']} — {c['name']}: {c['rule']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Task: Research
# ---------------------------------------------------------------------------
def create_research_task(agent: Agent, topic: str) -> Task:
    """
    Research a topic by analyzing intel data, customer language,
    competitor positioning, and market trends.
    """
    intel_context = _load_intel_context()

    return Task(
        description=(
            f"Research the following topic for a Gadget Geeks Pro content piece:\n\n"
            f"TOPIC: {topic}\n\n"
            f"Using the intel data below, produce a research brief that includes:\n\n"
            f"1. **Customer Language** — Pull 5-10 exact phrases real customers use "
            f"about this topic (from reviews, Reddit, forums). These are the words "
            f"the writer MUST weave into the content.\n\n"
            f"2. **Pain Points** — What are the top 3 fears/frustrations buyers have "
            f"about this topic? Be specific — not 'worried about quality' but "
            f"'worried the battery only lasts 4 hours after a year.'\n\n"
            f"3. **Competitor Gaps** — What are competitors NOT saying about this topic? "
            f"Where can we position differently?\n\n"
            f"4. **Content Angle** — Recommend the single strongest angle for this piece. "
            f"State the Schwartz awareness level of the target reader and why.\n\n"
            f"5. **Key Stats** — Any specific numbers, percentages, or data points "
            f"that should appear in the content.\n\n"
            f"--- INTEL DATA ---\n{intel_context}"
        ),
        expected_output=(
            "A structured research brief in markdown format with sections: "
            "Customer Language (exact quotes), Pain Points (specific fears), "
            "Competitor Gaps, Recommended Angle + Schwartz Level, and Key Stats. "
            "The brief should give the writer everything they need to start drafting."
        ),
        agent=agent,
    )


# ---------------------------------------------------------------------------
# Task: Write Content
# ---------------------------------------------------------------------------
def create_write_task(agent: Agent, topic: str, content_type: str = "blog_post") -> Task:
    """
    Write content based on the research brief from the previous task.
    """
    niche_data = _read_file("config/niche.json")

    content_type_instructions = {
        "blog_post": (
            "Write a blog post (800-1200 words). Include:\n"
            "- H1 title that hooks and includes primary keyword\n"
            "- Opening that addresses the reader's pain point directly\n"
            "- 3-5 H2 sections with substantive content\n"
            "- Specific numbers and customer language throughout\n"
            "- One clear CTA at the end with specific action verb\n"
            "- Short paragraphs, varied sentence lengths, conversational tone"
        ),
        "product_description": (
            "Write a product description (200-400 words). Include:\n"
            "- Headline that sells the benefit, not the feature\n"
            "- Feature -> Benefit -> So What chain for top 4-5 features\n"
            "- Social proof reference point\n"
            "- Objection handler (warranty, quality, returns)\n"
            "- One CTA with urgency element"
        ),
        "buying_guide": (
            "Write a buying guide (1000-1500 words). Include:\n"
            "- H1 that matches search intent exactly\n"
            "- Quick-answer summary in first 100 words (for featured snippets)\n"
            "- Comparison criteria with specific recommendations\n"
            "- 'Who should buy what' section\n"
            "- Budget recommendations with real price points\n"
            "- Internal links to product pages"
        ),
    }

    type_instruction = content_type_instructions.get(
        content_type, content_type_instructions["blog_post"]
    )

    return Task(
        description=(
            f"Using the research brief from the previous task, write a {content_type} "
            f"about: {topic}\n\n"
            f"--- CONTENT REQUIREMENTS ---\n{type_instruction}\n\n"
            f"--- PRE-WRITE PROTOCOL (MANDATORY) ---\n"
            f"Before writing, explicitly state:\n"
            f"1. Schwartz Awareness Level of target reader\n"
            f"2. Emotional core driving the purchase\n"
            f"3. Biggest objection to overcome\n"
            f"4. Framework chosen: PAS, AIDA, or Before-After-Bridge\n"
            f"5. 3+ exact customer phrases you'll weave in\n\n"
            f"--- WRITING RULES ---\n"
            f"- Use contractions everywhere (don't, won't, it's, you're)\n"
            f"- Mix sentence lengths: include 2+ sentences under 6 words\n"
            f"- Include at least one sentence fragment or em-dash\n"
            f"- Specific numbers: '$347 saved' not 'save money'\n"
            f"- NO banned words: delve, tapestry, foster, plethora, seamless, "
            f"cutting-edge, game-changer, leverage, utilize, craft, curate, elevate, "
            f"empower, streamline, harness, comprehensive, journey, revolutionary\n"
            f"- NO banned phrases: 'in today's world', 'without breaking the bank', "
            f"'look no further', 'say goodbye to'\n"
            f"- No triple parallel patterns (three sentences starting the same way)\n"
            f"- No definition openers ('X is the art of...')\n"
            f"- Max 2 exclamation marks in the entire piece\n\n"
            f"--- STORE CONTEXT ---\n{niche_data}"
        ),
        expected_output=(
            f"A complete {content_type} draft with:\n"
            f"- Pre-Write Protocol answers at the top\n"
            f"- The full content piece ready for SEO optimization\n"
            f"- Content uses real customer language from the research brief\n"
            f"- Follows all writing rules (no banned words, varied rhythm, "
            f"contractions, specific numbers)"
        ),
        agent=agent,
    )


# ---------------------------------------------------------------------------
# Task: SEO Optimization
# ---------------------------------------------------------------------------
def create_seo_task(agent: Agent, topic: str) -> Task:
    """
    Optimize written content for search engines without killing readability.
    """
    seo_context = _load_seo_context()

    return Task(
        description=(
            f"Optimize the content draft from the previous task for SEO.\n\n"
            f"TOPIC: {topic}\n\n"
            f"Using the SEO data below, perform these optimizations:\n\n"
            f"1. **Primary Keyword** — Identify or confirm the primary keyword. "
            f"Place it in: title, first 100 words, at least one H2, and 2-3 times "
            f"naturally in the body (2-3% density max).\n\n"
            f"2. **Meta Title** — Write a meta title under 60 characters that includes "
            f"the primary keyword and compels clicks.\n\n"
            f"3. **Meta Description** — Write a meta description under 160 characters "
            f"with keyword + a specific CTA.\n\n"
            f"4. **Header Structure** — Verify H1/H2/H3 hierarchy is correct. "
            f"Each H2 should target a related keyword or question.\n\n"
            f"5. **Internal Links** — Suggest 2-3 internal links to relevant "
            f"product pages, collection pages, or other blog posts on "
            f"gadgetgeekspro.myshopify.com.\n\n"
            f"6. **Schema Markup** — Recommend applicable structured data "
            f"(FAQ, Product, HowTo, Article).\n\n"
            f"7. **Secondary Keywords** — Identify 3-5 LSI/secondary keywords "
            f"and verify they appear naturally in the content.\n\n"
            f"IMPORTANT: Do NOT sacrifice readability for keyword placement. "
            f"If a keyword insertion reads awkwardly, find a natural spot or skip it.\n\n"
            f"--- SEO DATA ---\n{seo_context}"
        ),
        expected_output=(
            "The fully SEO-optimized content with:\n"
            "- meta_title (under 60 chars)\n"
            "- meta_description (under 160 chars)\n"
            "- primary_keyword identified\n"
            "- secondary_keywords listed\n"
            "- internal_links (2-3 suggestions with anchor text)\n"
            "- schema_recommendations\n"
            "- The complete optimized body text with keywords woven in naturally\n"
            "- A brief note on any changes made to the original draft"
        ),
        agent=agent,
    )


# ---------------------------------------------------------------------------
# Task: Quality Check
# ---------------------------------------------------------------------------
def create_qa_task(agent: Agent, topic: str) -> Task:
    """
    Run the full 23-check quality gate on the optimized content.
    """
    copy_rules = _load_copy_rules()

    return Task(
        description=(
            f"Run a complete quality check on the SEO-optimized content for: {topic}\n\n"
            f"Execute ALL 23 checks from the Copy Police scanner. For each check, "
            f"state PASS or FAIL with specific evidence.\n\n"
            f"--- THE 23 CHECKS ---\n{copy_rules}\n\n"
            f"--- QA PROCESS ---\n"
            f"1. Read the entire piece carefully\n"
            f"2. Run each check, quoting the exact text that passes or fails\n"
            f"3. For failures: provide the specific rewrite that fixes it\n"
            f"4. Calculate final score:\n"
            f"   - Each critical check: 5 points (13 critical = 65 points)\n"
            f"   - Each warning check: 3 points (12 warnings = 36 points, "
            f"capped to fill remaining 35)\n"
            f"   - Total: 100 points possible\n"
            f"5. Apply fixes to produce the final version\n"
            f"6. Re-verify the fixed version passes all checks\n\n"
            f"--- RATING ---\n"
            f"EXCELLENT (90-100): Ships as-is. Human-quality content.\n"
            f"GOOD (70-89): Minor fixes applied, ships with notes.\n"
            f"NEEDS WORK (below 70): Major rewrite needed. Flag for human review.\n\n"
            f"--- BRAND VOICE CHECK ---\n"
            f"Verify the content sounds like: 'Confident, knowledgeable, no-BS. "
            f"Like a tech-savvy friend who knows the deals.'\n"
            f"NOT like: Corporate speak, overly formal, AI-generated.\n\n"
            f"--- FINAL OUTPUT ---\n"
            f"You MUST return the final result as a valid JSON object with these keys:\n"
            f"- title: the H1/title of the content\n"
            f"- body: the complete final content (with all fixes applied)\n"
            f"- meta_description: under 160 chars\n"
            f"- keywords: list of primary + secondary keywords\n"
            f"- qa_score: integer 0-100\n"
            f"- qa_rating: EXCELLENT, GOOD, or NEEDS_WORK\n"
            f"- qa_checks: object with check names as keys, pass/fail as values\n"
            f"- qa_notes: list of strings with any flagged issues or applied fixes"
        ),
        expected_output=(
            'A JSON object with keys: "title", "body", "meta_description", '
            '"keywords" (list), "qa_score" (int), "qa_rating" (string), '
            '"qa_checks" (object of check_name: pass/fail), and "qa_notes" (list). '
            "The body should be the final, fully fixed content ready to publish."
        ),
        agent=agent,
    )
