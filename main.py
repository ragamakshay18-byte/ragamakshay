# ══════════════════════════════════════════════════════════════════
#  AI Code Review & Rewrite Agent — Backend (main.py)
#  Tech Stack : FastAPI + Groq (Llama 3.3 70B)
# ══════════════════════════════════════════════════════════════════

# ── Milestone 2 Activity 2.1 : Import necessary libraries ─────────
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from groq import Groq
from groq.types.chat import ChatCompletion
from dotenv import load_dotenv
from typing import Optional
from re import Match
import os
import re
import uvicorn

# ── Milestone 2 Activity 2.2 : Load GROQ API key from .env ────────
load_dotenv()

# ── Initialize FastAPI application ────────────────────────────────
app: FastAPI = FastAPI(
    title="AI Code Review & Rewrite Agent",
    description="Real-time AI-powered code review and rewriting using Groq + Llama 3.3 70B",
    version="1.0.0",
)

# ── CORS — allow frontend to communicate with backend ─────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Initialize Groq client with API key ───────────────────────────
groq_client: Groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── Milestone 2 Activity 2.3 : Define model & generation settings ─
MODEL_NAME:  str   = "llama-3.3-70b-versatile"
TEMPERATURE: float = 0.3
MAX_TOKENS:  int   = 2000
TOP_P:       float = 0.9


# ══════════════════════════════════════════════════════════════════
#  REQUEST & RESPONSE SCHEMAS  (Pydantic models with type hints)
# ══════════════════════════════════════════════════════════════════

class CodeReviewRequest(BaseModel):
    """Schema for incoming code review requests from the frontend."""
    code:        str       = Field(...,      description="Source code to be reviewed")
    language:    str       = Field("python", description="Programming language of the code")
    focus_areas: list[str] = Field(
        default=["bugs", "security", "performance", "best_practices"],
        description="Areas to focus on during the review",
    )


class CodeRewriteRequest(BaseModel):
    """Schema for incoming code rewrite requests from the frontend."""
    code:            str           = Field(...,      description="Source code to be rewritten")
    language:        str           = Field("python", description="Programming language of the code")
    review_feedback: Optional[str] = Field("",      description="Previous review feedback to address")


class CodeReviewResponse(BaseModel):
    """Schema for the structured review response sent back to the frontend."""
    review_text:    str = Field(..., description="Full markdown review text from the AI")
    critical_count: int = Field(..., description="Number of critical issues identified")
    high_count:     int = Field(..., description="Number of high priority issues identified")
    medium_count:   int = Field(..., description="Number of medium priority issues identified")
    low_count:      int = Field(..., description="Number of low priority suggestions")


class CodeRewriteResponse(BaseModel):
    """Schema for the structured rewrite response sent back to the frontend."""
    rewritten_code: str       = Field(..., description="Optimized, production-ready rewritten code")
    improvements:   list[str] = Field(..., description="List of key improvements made to the code")
    explanation:    str       = Field(..., description="Summary explaining what was changed and why")


class HealthResponse(BaseModel):
    """Schema for the health check response."""
    status: str = Field(..., description="Server status: healthy or degraded")
    groq:   str = Field(..., description="Groq API connection status")
    model:  str = Field(..., description="AI model currently in use")


# ══════════════════════════════════════════════════════════════════
#  MILESTONE 3 ACTIVITY 1 : parse_review_response function
#  Extracts and categorises feedback by priority level
# ══════════════════════════════════════════════════════════════════

def count_bullets(section_match: Optional[Match[str]]) -> int:
    """
    Count the number of bullet points inside a regex-matched section.

    Args:
        section_match: A regex Match object for a section of review text.

    Returns:
        Integer count of bullet points found in the section.
    """
    if not section_match:
        return 0
    section_text: str = section_match.group(0)
    return len(re.findall(r'^\s*[-*•]', section_text, re.MULTILINE))


def parse_review_response(review_text: str) -> dict[str, int]:
    """
    Parse the LLM-generated review text to extract severity counts.

    The function searches for sections labelled as Critical Issues,
    High Priority, Medium Priority, and Low Priority using regular
    expression patterns, then counts the bullet points in each section.

    Args:
        review_text: Raw markdown string returned by the Groq LLM.

    Returns:
        Dictionary containing integer counts for each severity level:
        critical_count, high_count, medium_count, low_count.
    """
    # Search for each priority section using regex
    critical_section: Optional[Match[str]] = re.search(
        r'###\s*🔴\s*Critical Issues.*?(?=###|\Z)', review_text, re.DOTALL
    )
    high_section: Optional[Match[str]] = re.search(
        r'###\s*🟠\s*High Priority.*?(?=###|\Z)', review_text, re.DOTALL
    )
    medium_section: Optional[Match[str]] = re.search(
        r'###\s*🟡\s*Medium Priority.*?(?=###|\Z)', review_text, re.DOTALL
    )
    low_section: Optional[Match[str]] = re.search(
        r'###\s*🟢\s*Low Priority.*?(?=###|\Z)', review_text, re.DOTALL
    )

    # Initialize counters for each priority category
    critical_count: int = max(count_bullets(critical_section), 0)
    high_count:     int = max(count_bullets(high_section),     0)
    medium_count:   int = max(count_bullets(medium_section),   0)
    low_count:      int = max(count_bullets(low_section),      0)

    return {
        "critical_count": critical_count,
        "high_count":     high_count,
        "medium_count":   medium_count,
        "low_count":      low_count,
    }


def parse_rewrite_response(rewrite_text: str) -> dict[str, str | list[str]]:
    """
    Parse the LLM-generated rewrite text to extract code and improvements.

    Args:
        rewrite_text: Raw markdown string returned by the Groq LLM.

    Returns:
        Dictionary with rewritten_code (str), improvements (list[str]),
        and explanation (str).
    """
    # Extract fenced code block from the response
    code_match: Optional[Match[str]] = re.search(
        r'```(?:\w+)?\n(.*?)```', rewrite_text, re.DOTALL
    )
    rewritten_code: str = (
        code_match.group(1).strip() if code_match else rewrite_text
    )

    # Extract bold-labelled improvement lines
    raw_improvements: list[tuple[str, str]] = re.findall(
        r'\*\*(.*?)\*\*[:\s]+(.*?)(?=\n|$)', rewrite_text
    )
    improvement_list: list[str] = [
        f"{title}: {desc}" for title, desc in raw_improvements[:6]
    ]

    # Extract explanation paragraph
    explanation_match: Optional[Match[str]] = re.search(
        r'(?:Explanation|Summary)[:\s]+(.*?)(?=\n\n|\Z)',
        rewrite_text,
        re.DOTALL | re.IGNORECASE,
    )
    explanation: str = (
        explanation_match.group(1).strip()
        if explanation_match
        else "Code has been optimized and rewritten following best practices."
    )

    return {
        "rewritten_code": rewritten_code,
        "improvements": improvement_list or [
            "Code structure improved",
            "Best practices applied",
            "Security enhancements made",
        ],
        "explanation": explanation,
    }


# ══════════════════════════════════════════════════════════════════
#  PROMPT BUILDERS  (separate functions for clean, typed prompts)
# ══════════════════════════════════════════════════════════════════

def build_review_prompt(
    code: str,
    language: str,
    focus_areas: list[str],
) -> str:
    """
    Build the prompt string for a code review request.

    Args:
        code:         Source code to review.
        language:     Programming language of the code.
        focus_areas:  List of focus areas (bugs, security, etc.).

    Returns:
        Fully formatted prompt string ready to send to the LLM.
    """
    focus_str: str = ", ".join(focus_areas)

    return f"""You are an expert code reviewer with 15+ years of experience. \
Analyze this {language} code and focus on: {focus_str}.

CODE TO REVIEW:
```{language}
{code}
```

Respond EXACTLY in this format:

## 📊 Overall Assessment
[2-3 sentence summary of overall code quality]

### 🔴 Critical Issues (Must Fix)
- [Issue description with line reference if possible]

### 🟠 High Priority
- [Issue description]

### 🟡 Medium Priority
- [Issue description]

### 🟢 Low Priority
- [Suggestion]

## 💡 Quick Suggestions
[3-5 specific, actionable improvements as a numbered list]
"""


def build_rewrite_prompt(
    code: str,
    language: str,
    review_feedback: Optional[str],
) -> str:
    """
    Build the prompt string for a code rewrite request.

    Args:
        code:             Source code to rewrite.
        language:         Programming language of the code.
        review_feedback:  Optional previous review feedback to address.

    Returns:
        Fully formatted prompt string ready to send to the LLM.
    """
    feedback_section: str = (
        f"REVIEW FEEDBACK TO ADDRESS:\n{review_feedback}\n"
        if review_feedback
        else ""
    )

    return f"""You are an expert software engineer. \
Rewrite and optimize this {language} code to be clean and production-ready.

ORIGINAL CODE:
```{language}
{code}
```

{feedback_section}
Requirements:
1. Fix ALL bugs and security vulnerabilities
2. Optimize for performance
3. Follow {language} best practices and conventions
4. Add proper error handling
5. Add helpful docstrings and comments
6. Use clear, descriptive variable names

Respond in this EXACT format:

## ✨ Rewritten Code
```{language}
[YOUR COMPLETE REWRITTEN CODE HERE]
```

## 🚀 Key Improvements
**Type Hints**: Description
**Error Handling**: Description
**Security**: Description
**Performance**: Description

## Explanation
[2-3 sentences summarizing what was changed and why]
"""


# ══════════════════════════════════════════════════════════════════
#  MILESTONE 3 ACTIVITY 2 : Route functions
#  serve_tool, review_code, rewrite_code, health_check
# ══════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse, tags=["Pages"])
async def serve_login() -> HTMLResponse:
    """Serve the login page at the root URL."""
    try:
        with open("../frontend/login.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>❌ login.html not found</h1>",
            status_code=404,
        )


@app.get("/app", response_class=HTMLResponse, tags=["Pages"])
async def serve_tool() -> HTMLResponse:
    """
    Serve the main tool page (index.html) after user login.
    Returns the page content or an error message if the file is not found.
    """
    try:
        with open("../frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>❌ index.html not found</h1>",
            status_code=404,
        )


@app.post("/api/review", response_model=CodeReviewResponse, tags=["AI"])
async def review_code(request: CodeReviewRequest) -> CodeReviewResponse:
    """
    Handle code review requests from the frontend.

    Validates that the code input is not empty, builds a prompt for
    the AI reviewer, sends it to the Groq API, and returns the
    structured review response with severity counts.

    Args:
        request: CodeReviewRequest containing code, language, focus_areas.

    Returns:
        CodeReviewResponse with review_text and severity counts.

    Raises:
        HTTPException 400: If code input is empty.
        HTTPException 500: If the Groq API call fails.
    """
    # Validate — code input must not be empty
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    # Build the prompt and format focus areas
    prompt: str = build_review_prompt(
        code=request.code,
        language=request.language,
        focus_areas=request.focus_areas,
    )

    # Send request to Groq API
    try:
        response: ChatCompletion = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
        )

        review_text: str = response.choices[0].message.content
        counts: dict[str, int] = parse_review_response(review_text)

        # Return response in the specified model format
        return CodeReviewResponse(review_text=review_text, **counts)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")


@app.post("/api/rewrite", response_model=CodeRewriteResponse, tags=["AI"])
async def rewrite_code(request: CodeRewriteRequest) -> CodeRewriteResponse:
    """
    Handle code rewrite requests from the frontend.

    Validates the code input, builds a rewrite prompt, sends it to
    the Groq API, and returns clean production-ready rewritten code
    with improvement notes and an explanation.

    Args:
        request: CodeRewriteRequest containing code, language, review_feedback.

    Returns:
        CodeRewriteResponse with rewritten_code, improvements, explanation.

    Raises:
        HTTPException 400: If code input is empty.
        HTTPException 500: If the Groq API call fails.
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    prompt: str = build_rewrite_prompt(
        code=request.code,
        language=request.language,
        review_feedback=request.review_feedback,
    )

    try:
        response: ChatCompletion = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
        )

        rewrite_text: str = response.choices[0].message.content
        parsed: dict[str, str | list[str]] = parse_rewrite_response(rewrite_text)

        return CodeRewriteResponse(**parsed)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """
    Check if the server and Groq API connection are healthy.

    Returns:
        HealthResponse with status, groq connection state, and model name.
    """
    try:
        groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        return HealthResponse(
            status="healthy",
            groq="connected",
            model=MODEL_NAME,
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            groq=f"error: {str(e)}",
            model=MODEL_NAME,
        )


# ══════════════════════════════════════════════════════════════════
#  MILESTONE 4 ACTIVITY 2 : Run the web application
#  Command: python main.py
#  Then navigate to http://localhost:8000
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  🤖 AI Code Review & Rewrite Agent")
    print("=" * 60)
    print("  ✅ Login Page : http://localhost:8000")
    print("  ✅ Tool Page  : http://localhost:8000/app")
    print("  ✅ API Docs   : http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
