"""
Agent definitions for the Gadget Geeks Pro content pipeline.

Four agents, each with a distinct role in the content creation chain:
- Researcher: Mines intel data for angles, customer language, competitor gaps
- Writer: Drafts content using Schwartz awareness levels and real customer voice
- SEOOptimizer: Injects keywords, meta tags, internal links without killing readability
- QAAgent: Runs the 23-check anti-AI scan and brand voice verification
"""

import json
from pathlib import Path
from crewai import Agent
from langchain_anthropic import ChatAnthropic


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = REPO_ROOT / "config"


def _load_json(path: Path) -> dict:
    """Load a JSON file, return empty dict if missing."""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _load_niche_context() -> str:
    """Load niche.json as formatted string for agent backstories."""
    niche = _load_json(CONFIG_DIR / "niche.json")
    if not niche:
        return "Store: Gadget Geeks Pro — refurbished phones and accessories."
    store = niche.get("store", {})
    audience = niche.get("target_audience", {})
    voice = niche.get("brand_voice", {})
    products = niche.get("products", {})
    return (
        f"Store: {store.get('name', 'Gadget Geeks Pro')} ({store.get('url', '')})\n"
        f"Niche: {niche.get('niche', '')}\n"
        f"Audience: {audience.get('primary', '')}\n"
        f"Pain points: {', '.join(audience.get('pain_points', []))}\n"
        f"Desires: {', '.join(audience.get('desires', []))}\n"
        f"Voice: {voice.get('tone', '')} | Avoid: {voice.get('avoid', '')}\n"
        f"Products: {', '.join(products.get('categories', []))} | "
        f"Price range: {products.get('price_range', '')} | USP: {products.get('usp', '')}"
    )


def _load_banned_words() -> str:
    """Load banned words/phrases from copy-rules.json for QA agent."""
    rules = _load_json(CONFIG_DIR / "copy-rules.json")
    words = rules.get("banned_words", [])
    phrases = rules.get("banned_phrases", [])
    return (
        f"BANNED WORDS ({len(words)}): {', '.join(words[:30])}... "
        f"(full list: {len(words)} words)\n"
        f"BANNED PHRASES ({len(phrases)}): {', '.join(phrases[:15])}... "
        f"(full list: {len(phrases)} phrases)"
    )


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------
def get_llm(model: str = "claude-sonnet-4-20250514", temperature: float = 0.7):
    """Create a ChatAnthropic LLM instance for CrewAI agents."""
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        max_tokens=4096,
    )


# ---------------------------------------------------------------------------
# Agent definitions
# ---------------------------------------------------------------------------
def create_researcher(llm=None) -> Agent:
    """
    Researcher agent — the intel engine.

    Reads competitor data, customer language, and trend files to find
    the best angles for content. Identifies gaps competitors aren't covering
    and surfaces the exact phrases real buyers use.
    """
    niche_ctx = _load_niche_context()
    if llm is None:
        llm = get_llm(temperature=0.5)

    return Agent(
        role="Market Research Analyst",
        goal=(
            "Analyze market intel, customer language, and competitor gaps to identify "
            "the strongest content angle for a given topic. Surface exact phrases from "
            "real customer reviews, Reddit threads, and forum posts. Find what competitors "
            "are NOT covering."
        ),
        backstory=(
            f"You are the Market Intelligence brain for Gadget Geeks Pro. "
            f"You've spent years tracking the refurbished electronics market — every "
            f"competitor move, every customer complaint on Reddit, every Amazon review "
            f"that reveals what people actually care about.\n\n"
            f"Your research feeds every piece of content the company creates. "
            f"When you say 'customers use this exact phrase,' the writers listen.\n\n"
            f"--- STORE CONTEXT ---\n{niche_ctx}"
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )


def create_writer(llm=None) -> Agent:
    """
    Writer agent — the content creator.

    Takes research output and produces blog posts, product descriptions,
    and landing page copy. Follows Schwartz awareness levels, uses real
    customer language, and writes in the brand's no-BS voice.
    """
    niche_ctx = _load_niche_context()
    if llm is None:
        llm = get_llm(temperature=0.8)

    return Agent(
        role="Senior Copywriter",
        goal=(
            "Write content that sounds like a knowledgeable human wrote it — not AI. "
            "Use the Schwartz awareness framework to match the reader's mindset. "
            "Every feature gets a benefit chain. One CTA per piece. "
            "Specific numbers beat vague claims. Always use customer language from research."
        ),
        backstory=(
            f"You are the Content department lead for Gadget Geeks Pro. "
            f"Your copy has a voice — confident, direct, like a tech-savvy friend who "
            f"genuinely knows refurbished electronics and wants to help people stop "
            f"overpaying for phones.\n\n"
            f"Before writing anything, you always run the Pre-Write Protocol:\n"
            f"1. Identify Schwartz Awareness Level (Unaware / Problem-Aware / "
            f"Solution-Aware / Product-Aware / Most-Aware)\n"
            f"2. Identify the emotional core driving the purchase\n"
            f"3. Identify the biggest objection stopping the buyer\n"
            f"4. Pull exact phrases from customer language research\n"
            f"5. Choose framework: PAS, AIDA, or Before-After-Bridge\n\n"
            f"You never use corporate speak. You use contractions, sentence fragments, "
            f"and varied rhythm. Short punches. Then a longer sentence that builds "
            f"the argument with specifics.\n\n"
            f"--- STORE CONTEXT ---\n{niche_ctx}"
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )


def create_seo_optimizer(llm=None) -> Agent:
    """
    SEO Optimizer agent — keyword and structure specialist.

    Takes written content and weaves in target keywords, adds meta
    descriptions, suggests internal links, and ensures the content
    is structured for search engines without sacrificing readability.
    """
    niche_ctx = _load_niche_context()
    if llm is None:
        llm = get_llm(temperature=0.4)

    return Agent(
        role="SEO Specialist",
        goal=(
            "Optimize content for target keywords while preserving the human voice. "
            "Add meta title (under 60 chars), meta description (under 160 chars), "
            "header structure (H1/H2/H3), internal link suggestions, and keyword "
            "placement (title, first 100 words, H2s, naturally in body). "
            "Never keyword-stuff — readability comes first."
        ),
        backstory=(
            f"You are the SEO department for Gadget Geeks Pro at "
            f"gadgetgeekspro.myshopify.com. You know Shopify SEO inside out — "
            f"from collection page titles to blog post schema markup.\n\n"
            f"Your job is to take good content and make it findable. You work with "
            f"the keyword data from departments/seo/keywords.json and opportunities "
            f"from departments/seo/opportunities.json.\n\n"
            f"Key rules:\n"
            f"- Keyword in title, first 100 words, at least one H2, and naturally "
            f"in body (2-3% density max)\n"
            f"- Meta title under 60 chars with primary keyword\n"
            f"- Meta description under 160 chars with keyword + CTA\n"
            f"- Suggest 2-3 internal links to relevant product/collection pages\n"
            f"- Add FAQ schema suggestions where appropriate\n"
            f"- Never sacrifice readability for SEO — if it reads awkward, rewrite\n\n"
            f"--- STORE CONTEXT ---\n{niche_ctx}"
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )


def create_qa_agent(llm=None) -> Agent:
    """
    QA Agent — quality gatekeeper.

    Runs the 23-check anti-AI scan on content, verifies brand voice
    compliance, checks factual accuracy, and scores the piece.
    Content must pass QA before shipping.
    """
    niche_ctx = _load_niche_context()
    banned_ctx = _load_banned_words()
    if llm is None:
        llm = get_llm(temperature=0.3)

    return Agent(
        role="Content QA Analyst",
        goal=(
            "Run a thorough quality check on content before it ships. Execute all 23 "
            "anti-AI checks from copy-rules.json: banned words, banned phrases, "
            "negation dance, triple patterns, definition openers, uniform bullets, "
            "transition starters, summary endings, hedging, vague superlatives, "
            "sentence length variation, strategic imperfection, rhetorical questions, "
            "contractions, features-without-benefits, loss aversion, offer engineering, "
            "review uniformity, bucket brigade, mechanism explanation, active voice, "
            "lazy patterns, period-conjunction fragments, and staccato fragments. "
            "Score each check pass/fail. Return a QA score out of 100 with specific "
            "line-level feedback for any failures."
        ),
        backstory=(
            f"You are the quality gate for Gadget Geeks Pro content. Nothing ships "
            f"without your approval. You've been trained on the Copy Police system — "
            f"a 23-check scanner that catches AI-generated copy patterns.\n\n"
            f"Your job:\n"
            f"1. Run every check against the content\n"
            f"2. Flag violations with exact quotes and line references\n"
            f"3. Suggest specific rewrites for each violation\n"
            f"4. Score: EXCELLENT (90-100, ships as-is), GOOD (70-89, minor fixes), "
            f"NEEDS WORK (below 70, rewrite required)\n"
            f"5. Verify brand voice matches: confident, direct, no-BS tech friend\n"
            f"6. Check factual claims about refurbished electronics\n\n"
            f"--- BANNED CONTENT ---\n{banned_ctx}\n\n"
            f"--- STORE CONTEXT ---\n{niche_ctx}"
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )
