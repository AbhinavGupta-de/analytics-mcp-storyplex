"""LLM Service for intelligent analytics powered by Claude."""

import json
import sys
from typing import Any, Optional

from anthropic import Anthropic

from src.config import settings


def log_llm(message: str):
    """Log LLM operations to stderr."""
    print(f"[LLM] {message}", file=sys.stderr)


class LLMService:
    """Service for LLM-powered analytics and insights."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM service.

        Args:
            api_key: Anthropic API key. If not provided, uses settings.
        """
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not configured. "
                "Set ANTHROPIC_API_KEY environment variable."
            )
        self.client = Anthropic(api_key=self.api_key)
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        """Make a call to Claude API.

        Args:
            system_prompt: System instructions
            user_prompt: User query

        Returns:
            Claude's response text
        """
        log_llm(f"Calling Claude with prompt length: {len(user_prompt)} chars")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        result = response.content[0].text
        log_llm(f"Got response: {len(result)} chars")
        return result

    def estimate_fandom_time(self, fandom_name: str) -> dict[str, Any]:
        """Estimate time to consume source material for a fandom.

        Uses LLM knowledge to provide intelligent estimates for any fandom.
        """
        system_prompt = """You are a fandom and media expert. Your task is to estimate
the time needed to consume the source material for a given fandom.

IMPORTANT: You must respond with ONLY valid JSON, no markdown, no explanation.

The JSON must have this structure:
{
    "fandom": "Name of the fandom",
    "source_type": "Type of source material (e.g., 'Books + Movies', 'Anime + Manga', 'TV Show', 'Video Game', 'Music + Variety')",
    "components": [
        {
            "type": "books/movies/anime/manga/tv_show/game/music",
            "name": "Component name",
            "count": number,
            "unit": "episodes/volumes/chapters/hours/songs",
            "estimated_hours": number
        }
    ],
    "total_hours": number,
    "minimum_hours": number (for essential content only),
    "recommendation": "Brief recommendation for new fans",
    "entry_points": ["List of good starting points for newcomers"]
}

Be accurate with episode counts, book counts, movie runtimes, etc.
For ongoing series, note the current state.
For large fandoms, distinguish between essential and completionist content."""

        user_prompt = f"""Estimate the time needed to get into the fandom: "{fandom_name}"

Consider all major source materials (books, movies, anime, manga, TV shows, games, etc.)
Provide accurate counts and reasonable time estimates.
Include both minimum time (essentials) and total time (everything)."""

        try:
            response = self._call(system_prompt, user_prompt)
            # Parse JSON response
            # Handle potential markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            log_llm(f"JSON parse error: {e}")
            return {
                "fandom": fandom_name,
                "error": f"Failed to parse LLM response: {e}",
                "raw_response": response[:500] if response else None,
            }
        except Exception as e:
            log_llm(f"LLM error: {e}")
            return {"fandom": fandom_name, "error": str(e)}

    def analyze_fandom_genres(
        self,
        fandom_name: str,
        genre_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Provide intelligent analysis of fandom genre data.

        Takes scraped data from AO3 and provides insights.
        """
        system_prompt = """You are a fanfiction and fandom analytics expert.
Analyze the provided genre/tag data and provide insights.

IMPORTANT: You must respond with ONLY valid JSON, no markdown, no explanation.

The JSON must have this structure:
{
    "fandom": "Name",
    "summary": "2-3 sentence summary of the fandom's fanfiction landscape",
    "dominant_themes": ["list", "of", "top", "themes"],
    "popular_tropes": ["list", "of", "popular", "tropes", "from", "tags"],
    "shipping_culture": "Analysis of relationship dynamics in fandom",
    "content_warnings": "Summary of common content warnings",
    "audience_profile": "Likely audience based on content patterns",
    "writing_opportunities": ["Underserved niches or opportunities for writers"],
    "market_insights": "Brief market analysis for content creators"
}"""

        user_prompt = f"""Analyze this genre/tag data for the fandom "{fandom_name}":

Total Works: {genre_data.get('total_works', 'Unknown')}

Top Genres/Tags:
{json.dumps(genre_data.get('genres', [])[:20], indent=2)}

Top Relationships:
{json.dumps(genre_data.get('relationships', [])[:15], indent=2)}

Top Characters:
{json.dumps(genre_data.get('characters', [])[:15], indent=2)}

Ratings Distribution:
{json.dumps(genre_data.get('ratings', []), indent=2)}

Categories:
{json.dumps(genre_data.get('categories', []), indent=2)}

Provide insights about this fandom's fanfiction landscape."""

        try:
            response = self._call(system_prompt, user_prompt)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            log_llm(f"JSON parse error: {e}")
            return {
                "fandom": fandom_name,
                "error": f"Failed to parse LLM response: {e}",
            }
        except Exception as e:
            log_llm(f"LLM error: {e}")
            return {"fandom": fandom_name, "error": str(e)}

    def analyze_market_trends(
        self,
        top_fandoms: list[dict],
        question: Optional[str] = None,
    ) -> dict[str, Any]:
        """Analyze market trends from fandom data.

        Args:
            top_fandoms: List of top fandoms with work counts
            question: Optional specific question to answer
        """
        system_prompt = """You are a market analyst specializing in fanfiction and
web fiction markets. Analyze the provided fandom data and provide strategic insights.

IMPORTANT: You must respond with ONLY valid JSON, no markdown, no explanation.

The JSON must have this structure:
{
    "market_summary": "Overview of the current market state",
    "top_categories": [
        {"category": "name", "analysis": "brief analysis"}
    ],
    "growth_opportunities": ["list of opportunities"],
    "saturation_warnings": ["oversaturated areas to avoid"],
    "recommendations": ["strategic recommendations"],
    "answer": "If a specific question was asked, answer it here"
}"""

        fandom_summary = "\n".join(
            [
                f"- {f['name']}: {f.get('work_count', f.get('ao3_work_count', 0)):,} works ({f.get('category', 'Unknown')})"
                for f in top_fandoms[:30]
            ]
        )

        user_prompt = f"""Analyze these top fandoms by work count:

{fandom_summary}

{"Question: " + question if question else "Provide general market analysis."}"""

        try:
            response = self._call(system_prompt, user_prompt)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            log_llm(f"JSON parse error: {e}")
            return {"error": f"Failed to parse LLM response: {e}"}
        except Exception as e:
            log_llm(f"LLM error: {e}")
            return {"error": str(e)}

    def answer_analytics_question(
        self,
        question: str,
        context: dict[str, Any],
    ) -> str:
        """Answer a natural language question about the data.

        Args:
            question: User's question
            context: Relevant data context (stats, fandoms, etc.)
        """
        system_prompt = """You are an analytics assistant for a fanfiction and web novel
market research platform. Answer questions using the provided data context.

Be concise, data-driven, and actionable in your responses.
If you don't have enough data, say so and suggest what data would help.
Format numbers with commas for readability."""

        user_prompt = f"""Question: {question}

Available Data Context:
{json.dumps(context, indent=2, default=str)}

Answer the question based on this data. Be specific and cite numbers when possible."""

        try:
            return self._call(system_prompt, user_prompt)
        except Exception as e:
            log_llm(f"LLM error: {e}")
            return f"Error answering question: {e}"

    def find_ao3_fandom_name(self, user_query: str) -> str:
        """Find the correct AO3 fandom name from a user query.

        AO3 uses specific fandom tag formats. This uses LLM to map
        user queries to the correct AO3 format.
        """
        system_prompt = """You are an expert on Archive of Our Own (AO3) fandom tags.
Given a user's fandom query, return the EXACT tag name as it appears on AO3.

IMPORTANT: Respond with ONLY the fandom tag name, nothing else.
No quotes, no explanation, just the tag.

Examples:
- "Genshin Impact" -> 原神 | Genshin Impact (Video Game)
- "My Hero Academia" -> 僕のヒーローアカデミア | Boku no Hero Academia | My Hero Academia
- "Harry Potter" -> Harry Potter - J. K. Rowling
- "Marvel" -> Marvel Cinematic Universe
- "BTS" -> 방탄소년단 | Bangtan Boys | BTS
- "Attack on Titan" -> 進撃の巨人 | Shingeki no Kyojin | Attack on Titan
- "One Piece" -> One Piece
- "Naruto" -> Naruto
- "Final Fantasy" -> Final Fantasy Series
- "Demon Slayer" -> 鬼滅の刃 | Demon Slayer: Kimetsu no Yaiba (Anime)
- "Jujutsu Kaisen" -> 呪術廻戦 | Jujutsu Kaisen (Anime & Manga)
- "Haikyuu" -> ハイキュー!! | Haikyuu!!"""

        user_prompt = f"What is the exact AO3 fandom tag for: {user_query}"

        try:
            result = self._call(system_prompt, user_prompt)
            return result.strip().strip('"').strip("'")
        except Exception as e:
            log_llm(f"Error finding fandom name: {e}")
            return user_query  # Return original as fallback

    def generate_fandom_analysis(
        self,
        fandom_name: str,
        available_data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Generate a comprehensive fandom analysis using LLM knowledge.

        This is a fallback when we can't scrape data - uses LLM's
        knowledge about the fandom.
        """
        system_prompt = """You are a fanfiction and fandom expert with extensive knowledge
of AO3, fanfiction trends, and fandom communities.

IMPORTANT: Respond with ONLY valid JSON, no markdown, no explanation.

Generate a comprehensive analysis for the requested fandom with this structure:
{
    "fandom": "Fandom name",
    "category": "Anime & Manga / TV Shows / Movies / Books / Video Games / Music / etc",
    "estimated_works": "Approximate number of works on AO3 (use your knowledge)",
    "popularity_tier": "S/A/B/C tier based on fanfic volume",
    "summary": "2-3 sentence overview of the fandom's fanfiction landscape",
    "dominant_genres": ["Top genres like Romance, Angst, Fluff, AU, etc"],
    "popular_ships": ["Top pairings in this fandom"],
    "top_characters": ["Most written about characters"],
    "common_tropes": ["Popular tropes and themes"],
    "audience_profile": "Typical reader demographics and preferences",
    "content_rating_breakdown": "Typical rating distribution (Gen/Teen/Mature/Explicit)",
    "unique_aspects": "What makes this fandom's fanfic community unique",
    "writing_opportunities": ["Underserved niches for new writers"],
    "crossover_potential": ["Fandoms it commonly crosses over with"]
}"""

        context = ""
        if available_data:
            context = f"\n\nAvailable scraped data to incorporate:\n{json.dumps(available_data, indent=2)}"

        user_prompt = f"""Generate a comprehensive fanfiction analysis for: {fandom_name}
{context}

Use your knowledge of this fandom's fanfiction community on AO3."""

        try:
            response = self._call(system_prompt, user_prompt)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            log_llm(f"JSON parse error: {e}")
            return {"fandom": fandom_name, "error": f"Failed to parse response: {e}"}
        except Exception as e:
            log_llm(f"LLM error: {e}")
            return {"fandom": fandom_name, "error": str(e)}

    def answer_any_question(
        self,
        question: str,
        scraped_data: Optional[dict] = None,
        db_data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Answer ANY analytics question using LLM intelligence.

        This is the ultimate fallback - uses LLM knowledge to answer
        questions even without complete data.
        """
        system_prompt = """You are the AI brain of Storyplex Analytics, a fanfiction and
web novel market research platform. You have extensive knowledge about:

- AO3, FanFiction.net, Wattpad, Royal Road, and other fiction platforms
- Fandom sizes, popularity, and trends
- Fanfiction genres, tropes, and shipping culture
- Creator monetization (Patreon, Ko-fi, etc.)
- Web novel and light novel markets
- Anime, manga, and media franchise popularity

Answer the user's question comprehensively. If you have data provided, use it.
If not, use your knowledge to provide the best possible answer.

IMPORTANT: Respond with ONLY valid JSON in this format:
{
    "answer": "Your comprehensive answer to the question",
    "data": [optional array of relevant data points/rankings],
    "insights": ["Key insights or takeaways"],
    "recommendations": ["Actionable recommendations if applicable"],
    "confidence": "high/medium/low based on data availability",
    "data_sources": "What data this answer is based on"
}"""

        context_parts = []
        if scraped_data:
            context_parts.append(f"Live scraped data:\n{json.dumps(scraped_data, indent=2)}")
        if db_data:
            context_parts.append(f"Database data:\n{json.dumps(db_data, indent=2)}")

        context = "\n\n".join(context_parts) if context_parts else "No specific data provided - use your knowledge."

        user_prompt = f"""Question: {question}

{context}

Provide a comprehensive answer. If specific data isn't available, use your
knowledge of fanfiction platforms and fandoms to give the best possible answer."""

        try:
            response = self._call(system_prompt, user_prompt)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            log_llm(f"JSON parse error: {e}")
            # Return the raw response if JSON parsing fails
            return {
                "answer": response if response else "Failed to generate response",
                "confidence": "low",
                "data_sources": "LLM knowledge"
            }
        except Exception as e:
            log_llm(f"LLM error: {e}")
            return {"error": str(e)}
