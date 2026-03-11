"""
CrewAI content pipeline orchestration for Gadget Geeks Pro.

Runs a sequential 4-agent pipeline:
    Research -> Write -> SEO Optimize -> QA

Reads context from departments/intel/ and departments/seo/.
Outputs structured JSON to departments/content/drafts/.

Usage:
    # As a module
    from scripts.crewai_content.crew import run_content_pipeline
    result = run_content_pipeline(topic="refurbished iPhone 15 buying guide")

    # From CLI
    python -m scripts.crewai_content.crew "refurbished iPhone 15 buying guide"
    python -m scripts.crewai_content.crew "best phone cases 2026" --type product_description
    python -m scripts.crewai_content.crew "iPhone vs Samsung refurbished" --model claude-opus-4-20250514
"""

import json
import sys
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path

from crewai import Crew, Process

from .agents import (
    create_researcher,
    create_writer,
    create_seo_optimizer,
    create_qa_agent,
    get_llm,
)
from .tasks import (
    create_research_task,
    create_write_task,
    create_seo_task,
    create_qa_task,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DRAFTS_DIR = REPO_ROOT / "departments" / "content" / "drafts"


def _slugify(text: str) -> str:
    """Convert topic string to a filename-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


def _extract_json_from_output(raw_output: str) -> dict | None:
    """
    Try to parse JSON from the QA agent's output.

    The agent might return pure JSON, JSON in a code block, or
    JSON embedded in prose. Try all strategies.
    """
    # Strategy 1: raw output is valid JSON
    try:
        return json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 2: JSON in a code block
    json_blocks = re.findall(r"```(?:json)?\s*\n(.*?)```", raw_output, re.DOTALL)
    for block in json_blocks:
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            continue

    # Strategy 3: find the largest {...} block
    brace_matches = re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", raw_output, re.DOTALL)
    for match in sorted(brace_matches, key=len, reverse=True):
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    return None


def _build_fallback_output(topic: str, raw_output: str) -> dict:
    """Build a structured output when JSON parsing fails."""
    return {
        "title": topic,
        "body": raw_output,
        "meta_description": "",
        "keywords": [],
        "qa_score": 0,
        "qa_rating": "NEEDS_WORK",
        "qa_checks": {},
        "qa_notes": ["QA agent did not return valid JSON. Raw output preserved in body."],
    }


def run_content_pipeline(
    topic: str,
    content_type: str = "blog_post",
    model: str = "claude-sonnet-4-20250514",
    verbose: bool = True,
    save_to_disk: bool = True,
) -> dict:
    """
    Run the full content pipeline for a given topic.

    Args:
        topic: The content topic (e.g., "refurbished iPhone 15 buying guide")
        content_type: One of "blog_post", "product_description", "buying_guide"
        model: Claude model ID to use for all agents
        verbose: Whether to print agent progress
        save_to_disk: Whether to save output to departments/content/drafts/

    Returns:
        dict with keys: title, body, meta_description, keywords,
        qa_score, qa_rating, qa_checks, qa_notes, pipeline_metadata
    """
    start_time = datetime.now(timezone.utc)

    print(f"{'=' * 60}")
    print(f"  CREWAI CONTENT PIPELINE")
    print(f"  Topic: {topic}")
    print(f"  Type: {content_type}")
    print(f"  Model: {model}")
    print(f"  Time: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'=' * 60}\n")

    # --- Create LLM instances ---
    # Research and QA get lower temperature (precision matters)
    # Writer gets higher temperature (creativity matters)
    # SEO gets lowest (consistency matters)
    research_llm = get_llm(model=model, temperature=0.5)
    writer_llm = get_llm(model=model, temperature=0.8)
    seo_llm = get_llm(model=model, temperature=0.4)
    qa_llm = get_llm(model=model, temperature=0.3)

    # --- Create agents ---
    researcher = create_researcher(llm=research_llm)
    writer = create_writer(llm=writer_llm)
    seo_optimizer = create_seo_optimizer(llm=seo_llm)
    qa_agent = create_qa_agent(llm=qa_llm)

    # --- Create tasks ---
    research_task = create_research_task(researcher, topic)
    write_task = create_write_task(writer, topic, content_type)
    seo_task = create_seo_task(seo_optimizer, topic)
    qa_task = create_qa_task(qa_agent, topic)

    # --- Build and run crew ---
    crew = Crew(
        agents=[researcher, writer, seo_optimizer, qa_agent],
        tasks=[research_task, write_task, seo_task, qa_task],
        process=Process.sequential,
        verbose=verbose,
    )

    print("[PIPELINE] Starting sequential execution...\n")
    raw_result = crew.kickoff()

    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    # --- Parse result ---
    raw_output = str(raw_result)
    parsed = _extract_json_from_output(raw_output)

    if parsed is None:
        print("\n[WARNING] QA agent did not return valid JSON. Building fallback output.")
        parsed = _build_fallback_output(topic, raw_output)

    # --- Add pipeline metadata ---
    parsed["pipeline_metadata"] = {
        "topic": topic,
        "content_type": content_type,
        "model": model,
        "pipeline_start": start_time.isoformat(),
        "pipeline_end": end_time.isoformat(),
        "duration_seconds": round(duration, 1),
        "agents": ["researcher", "writer", "seo_optimizer", "qa_agent"],
        "process": "sequential",
    }

    # --- Save to disk ---
    if save_to_disk:
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        slug = _slugify(topic)
        timestamp = start_time.strftime("%Y%m%d-%H%M")
        filename = f"{timestamp}_{slug}.json"
        output_path = DRAFTS_DIR / filename

        output_path.write_text(
            json.dumps(parsed, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\n[SAVED] {output_path}")
        parsed["_output_path"] = str(output_path)

    # --- Summary ---
    score = parsed.get("qa_score", "N/A")
    rating = parsed.get("qa_rating", "N/A")
    title = parsed.get("title", topic)

    print(f"\n{'=' * 60}")
    print(f"  PIPELINE COMPLETE")
    print(f"  Title: {title}")
    print(f"  QA Score: {score}/100 ({rating})")
    print(f"  Duration: {duration:.1f}s")
    print(f"{'=' * 60}")

    return parsed


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Run the CrewAI content pipeline for Gadget Geeks Pro"
    )
    parser.add_argument(
        "topic",
        help="Content topic (e.g., 'refurbished iPhone 15 buying guide')",
    )
    parser.add_argument(
        "--type",
        dest="content_type",
        default="blog_post",
        choices=["blog_post", "product_description", "buying_guide"],
        help="Type of content to produce (default: blog_post)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save output to departments/content/drafts/",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress agent verbose output",
    )

    args = parser.parse_args()

    result = run_content_pipeline(
        topic=args.topic,
        content_type=args.content_type,
        model=args.model,
        verbose=not args.quiet,
        save_to_disk=not args.no_save,
    )

    # Print the JSON result to stdout for piping
    print("\n--- JSON OUTPUT ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
