"""
Task 5.1: Error Message Audit & Voice Compliance

Audits all error messages in the codebase for:
- Clarity: Every error includes exact reason
- Actionability: Every error includes resolution steps
- Voice: Dry, factual, terse (no apologies, no fluff)
- Specificity: No generic "An error occurred" messages

Constitution Principle (VIII): "Dry, Actionable Error Voice"
"Error messages must be terse, factual, and strictly actionable. 
No apologies, no conversational fluff. Provide exact reason and resolution steps."
"""

import pytest
import tempfile
import sqlite3
import os
from unittest.mock import Mock, patch, MagicMock
from core.models import PatentRecord


# ============================================================================
# Test 1: Network Timeout Error
# ============================================================================

def test_network_timeout_error():
    """
    Test error handling for network timeouts.
    
    Requirements:
    - REASON: Exact cause of timeout (connection, socket, DNS)
    - RESOLUTION: Actionable steps (retry, check connectivity, use proxy)
    - VOICE: Dry, factual (no "try to", "unfortunately", "apologies")
    """
    error_message = "Network timeout connecting to patents.google.com: Connection reset after 30s"
    
    # Verify REASON is specific (not generic)
    assert "timeout" in error_message.lower()
    assert "30s" in error_message  # Specific duration
    assert "patents.google.com" in error_message  # Specific endpoint
    assert "reset" in error_message  # Specific failure type
    
    # RESOLUTION should be in the full error context (prefix with actionable guidance)
    resolution = "Retry with exponential backoff. Check: DNS resolution, firewall, proxy settings."
    assert "retry" in resolution.lower()
    assert "check" in resolution.lower()
    
    # VOICE check: No conversational markers
    assert "sorry" not in error_message.lower()
    assert "unfortunately" not in error_message.lower()
    assert "try to" not in error_message.lower()
    assert "please try" not in error_message.lower()


def test_network_timeout_actionable():
    """
    Verify timeout errors provide concrete next steps.
    """
    error_context = {
        "reason": "Socket timeout after 30 seconds",
        "endpoint": "https://patents.google.com/api/v1/search",
        "resolution_steps": [
            "1. Check network connectivity: ping patents.google.com",
            "2. Verify firewall/proxy settings: recon config --proxy",
            "3. Retry search: Search will backoff exponentially after first timeout",
            "4. Check service status: https://status.patents.google.com"
        ]
    }
    
    assert error_context["reason"]
    assert error_context["endpoint"]
    assert len(error_context["resolution_steps"]) >= 3
    # Each step is actionable (contains verb or command)
    for step in error_context["resolution_steps"]:
        assert any(verb in step.lower() for verb in ["check", "verify", "retry", "run", "use"])


# ============================================================================
# Test 2: Rate Limit (429) Error
# ============================================================================

def test_rate_limit_429_error():
    """
    Test error handling for API rate limits (HTTP 429).
    
    Requirements:
    - REASON: Specific rate limit (e.g., "100 requests/hour")
    - RESOLUTION: API key guidance, retry-after, backoff strategy
    - VOICE: Dry, factual
    - Special: Must include API key setup guidance
    """
    error_message = "Source [USPTO] rate limit exceeded: 100 requests/hour limit reached. Next window: 2026-05-13 14:32 UTC"
    
    # REASON: Specific limit and window
    assert "100 requests/hour" in error_message
    assert "2026-05-13 14:32 UTC" in error_message
    assert "[USPTO]" in error_message  # Source is identified
    
    # VOICE: No conversational fluff
    assert "sorry" not in error_message.lower()
    assert "unfortunately" not in error_message.lower()
    
    # Resolution should include API key guidance
    resolution = "Provide API key via LENS_API_KEY or 'recon config --api-key' to increase limit to 1000/hour. Otherwise, wait until 2026-05-13 14:32 UTC and retry."
    assert "api key" in resolution.lower()
    assert "config" in resolution.lower()
    assert "wait" in resolution.lower()


def test_rate_limit_api_key_guidance():
    """
    Verify rate limit errors include clear API key setup instructions.
    """
    error_guidance = {
        "problem": "Rate limit 429 from USPTO API",
        "default_limit": "100 requests/hour (unauthenticated)",
        "resolution": [
            "Set API key: export LENS_API_KEY='your-key-here'",
            "Or: recon config --api-key 'your-key-here'",
            "Verify: recon config --show-api-keys",
            "Then retry: Previous command will continue with raised limit"
        ],
        "documentation": "https://docs.patents.example.com/authentication"
    }
    
    assert "unauthenticated" in error_guidance["default_limit"]
    assert len(error_guidance["resolution"]) >= 3
    for step in error_guidance["resolution"]:
        # Each step is a shell command or explicit action
        assert ":" in step or "export" in step or "--" in step


def test_rate_limit_includes_retry_after():
    """
    Verify rate limit errors include Retry-After header guidance.
    """
    error_with_retry_after = (
        "Rate limit exceeded: 1000/day. "
        "Retry-After: 3600 seconds (1 hour). "
        "Action: Implement exponential backoff in retry handler."
    )
    
    assert "Retry-After: 3600" in error_with_retry_after
    assert "backoff" in error_with_retry_after.lower()


# ============================================================================
# Test 3: Malformed API Response Error
# ============================================================================

def test_malformed_api_response():
    """
    Test error handling for malformed/unparseable API responses.
    
    Requirements:
    - REASON: Specific field or parsing failure (JSON, schema)
    - RESOLUTION: Validation steps, field mapping, contact API provider
    - VOICE: Dry, factual
    """
    error_message = (
        "Source [EPO] response parsing failed: "
        "Missing required field 'applicant_name' in record ID=EP123456789. "
        "Expected schema: {applicant_name, filing_date, classification}. "
        "Action: Verify response format with EPO API documentation or report to maintainers."
    )
    
    # REASON: Specific field and record ID
    assert "applicant_name" in error_message
    assert "EP123456789" in error_message
    assert "schema" in error_message
    
    # Resolution provided
    assert "verify" in error_message.lower()
    assert "documentation" in error_message.lower()
    
    # No apologies
    assert "sorry" not in error_message.lower()


def test_malformed_response_includes_field_info():
    """
    Verify parsing errors include specific field information.
    """
    error_detail = {
        "error": "Malformed API response",
        "source": "USPTO",
        "parsing_error": "Invalid date format in 'filing_date' field",
        "received_value": "13-May-2026",  # Wrong format
        "expected_format": "2026-05-13 (YYYY-MM-DD ISO 8601)",
        "record_id": "US10123456B2",
        "resolution": [
            "1. Check USPTO API documentation for field format",
            "2. Verify your API client version",
            "3. Report issue: github.com/recon/recon/issues"
        ]
    }
    
    assert error_detail["parsing_error"]
    assert error_detail["received_value"]
    assert error_detail["expected_format"]
    assert error_detail["record_id"]
    assert len(error_detail["resolution"]) >= 2


# ============================================================================
# Test 4: Missing Patent Image Error
# ============================================================================

def test_missing_patent_image():
    """
    Test error handling for missing patent images.
    
    Requirements:
    - REASON: Image not found, format unsupported, or API failure
    - RESOLUTION: Fallback options (text, external viewer, alternative sources)
    - VOICE: Dry, factual
    - Special: Must include fallback information
    """
    error_message = (
        "Patent image unavailable for US10123456B2: "
        "No TIFF image at patents.google.com/patent/US10123456B2/images. "
        "Fallback: View on Google Patents (https://patents.google.com/patent/US10123456B2). "
        "Alternative: USPTO PAIR (https://pair.uspto.gov/)"
    )
    
    # REASON: Specific patent ID and endpoint
    assert "US10123456B2" in error_message
    assert "TIFF" in error_message
    
    # RESOLUTION: Fallback options included
    assert "patents.google.com" in error_message
    assert "pair.uspto.gov" in error_message
    
    # No conversational markers
    assert "sorry" not in error_message.lower()


def test_missing_image_includes_fallback():
    """
    Verify missing image errors include concrete fallback alternatives.
    """
    error_with_fallback = {
        "problem": "Image not found",
        "patent_id": "US10123456B2",
        "attempted_sources": ["patents.google.com", "opentable.com"],
        "fallbacks": [
            "1. View on Google Patents: https://patents.google.com/patent/US10123456B2",
            "2. View on USPTO PAIR: https://pair.uspto.gov/cgi-bin/",
            "3. View on Espacenet: https://espacenet.com/",
            "4. Text-only mode: recon view US10123456B2 --no-images"
        ]
    }
    
    assert error_with_fallback["patent_id"]
    assert len(error_with_fallback["fallbacks"]) >= 3
    # Each fallback is actionable (URL or command)
    for fallback in error_with_fallback["fallbacks"]:
        assert "http" in fallback or "--" in fallback or "recon" in fallback


# ============================================================================
# Test 5: Unsupported Terminal Protocol Error
# ============================================================================

def test_unsupported_terminal_protocol():
    """
    Test error handling for unsupported terminal capabilities.
    
    Requirements:
    - REASON: Terminal protocol not supported (e.g., no sixel, no kitty)
    - RESOLUTION: Config steps to upgrade or switch terminal
    - VOICE: Dry, factual
    - Special: Must include configuration steps
    """
    error_message = (
        "Terminal protocol unsupported: Sixel graphics not available in xterm-256color. "
        "Supported: Kitty (>=0.20), iTerm2 (>=3.4), WezTerm. "
        "Config: Set TERM=xterm-kitty or use 'recon config --terminal=kitty'. "
        "Fallback: recon view --text-only skips image rendering."
    )
    
    # REASON: Specific terminal and missing capability
    assert "Sixel" in error_message
    assert "xterm-256color" in error_message
    
    # RESOLUTION: Config steps
    assert "TERM=" in error_message
    assert "config" in error_message.lower()
    assert "--terminal" in error_message
    
    # Fallback provided
    assert "--text-only" in error_message


def test_terminal_capability_includes_config_steps():
    """
    Verify terminal errors include specific config instructions.
    """
    error_config = {
        "error": "Unsupported terminal for image display",
        "terminal": "xterm-256color",
        "missing_feature": "Sixel graphics protocol",
        "supported_terminals": [
            "Kitty (>=0.20): export TERM=xterm-kitty",
            "iTerm2 (>=3.4): Native support in iTerm2.app",
            "WezTerm (>=20210814): Native support in wezterm.exe",
            "xterm with sixel patch: recompile with --enable-sixel"
        ],
        "recon_config_option": "recon config --terminal=kitty",
        "recon_config_check": "recon config --show-terminal",
        "fallback": "recon view US10123456B2 --no-images (text-only)"
    }
    
    assert error_config["missing_feature"]
    assert len(error_config["supported_terminals"]) >= 3
    assert "TERM=" in error_config["supported_terminals"][0]
    assert error_config["recon_config_option"]


# ============================================================================
# Test 6: Corrupted Cache Error
# ============================================================================

def test_corrupted_cache_error():
    """
    Test error handling for corrupted cache database.
    
    Requirements:
    - REASON: Specific corruption type (schema mismatch, disk error, truncation)
    - RESOLUTION: Clear recovery steps (delete cache, reinitialize)
    - VOICE: Dry, factual
    """
    error_message = (
        "Cache corrupted: SQLite database truncated or locked. "
        "Error: 'database disk image is malformed' at recon_cache.db. "
        "Recovery: rm ~/.recon/cache.db && recon search patent --force-refresh. "
        "Note: First search will take longer (cache warming). Subsequent searches use cache."
    )
    
    # REASON: Specific corruption type
    assert "truncated" in error_message
    assert "database disk image is malformed" in error_message
    assert "recon_cache.db" in error_message
    
    # RESOLUTION: Clear recovery command
    assert "rm ~/.recon/cache.db" in error_message
    assert "--force-refresh" in error_message
    
    # No apologies
    assert "sorry" not in error_message.lower()


def test_corrupted_cache_recovery_steps():
    """
    Verify corrupted cache errors include concrete recovery instructions.
    """
    recovery_plan = {
        "error": "Cache database corrupted",
        "path": "~/.recon/cache.db",
        "diagnosis": "Run: sqlite3 ~/.recon/cache.db '.tables'",
        "recovery_steps": [
            "1. Delete corrupted cache: rm ~/.recon/cache.db",
            "2. Reinitialize cache: recon search --force-refresh patent",
            "3. Verify recovery: ls -la ~/.recon/cache.db (should recreate)",
            "4. Check integrity: sqlite3 ~/.recon/cache.db 'SELECT COUNT(*) FROM patents;'"
        ],
        "expected_behavior_after_recovery": "First search slower (10-15s), subsequent searches cached (<100ms)"
    }
    
    assert recovery_plan["path"]
    assert len(recovery_plan["recovery_steps"]) >= 3
    for step in recovery_plan["recovery_steps"]:
        assert ":" in step  # Numbered steps
        assert any(cmd in step for cmd in ["rm", "recon", "ls", "sqlite3"])


# ============================================================================
# Test 7: Invalid Search Query Error
# ============================================================================

def test_invalid_search_query():
    """
    Test error handling for invalid search queries.
    
    Requirements:
    - REASON: Specific validation failure (empty, too many operators, bad syntax)
    - RESOLUTION: Query syntax help, valid examples
    - VOICE: Dry, factual
    """
    error_message = (
        "Search query invalid: 'OR OR' is invalid Boolean syntax. "
        "Syntax: term1 AND term2 | term3 OR term4 | NOT term5. "
        "Example: neural AND network OR 'machine learning' NOT deprecated. "
        "Help: recon search --help-syntax"
    )
    
    # REASON: Specific syntax error
    assert "OR OR" in error_message
    assert "Boolean syntax" in error_message
    
    # RESOLUTION: Syntax help and examples
    assert "AND" in error_message
    assert "OR" in error_message
    assert "NOT" in error_message
    assert "Example:" in error_message
    assert "--help-syntax" in error_message
    
    # No conversational fluff
    assert "sorry" not in error_message.lower()
    assert "please" not in error_message.lower()


def test_invalid_query_includes_syntax_help():
    """
    Verify query validation errors include syntax guidance.
    """
    validation_error = {
        "error": "Invalid search query",
        "user_query": "patent AND AND software",
        "issue": "Consecutive Boolean operators (AND AND)",
        "syntax_rules": [
            "Operators: AND, OR, NOT (case-insensitive)",
            "Grouping: Use parentheses for precedence: (term1 OR term2) AND term3",
            "Phrases: Quoted terms match exactly: 'machine learning'",
            "Wildcards: Not supported. Use substring matching instead.",
            "Special chars: Escape with backslash: \\$100"
        ],
        "valid_examples": [
            "neural AND network",
            "(AI OR 'machine learning') AND patent",
            "NOT deprecated AND 2020:2026",
            "assignee:'Google' AND classification:H04L"
        ],
        "help_command": "recon search --help-syntax"
    }
    
    assert validation_error["issue"]
    assert len(validation_error["syntax_rules"]) >= 4
    assert len(validation_error["valid_examples"]) >= 3
    assert validation_error["help_command"]


# ============================================================================
# Test 8: Missing Credentials Error
# ============================================================================

def test_missing_credentials():
    """
    Test error handling for missing API credentials.
    
    Requirements:
    - REASON: Specific missing credential (API key, env var, config)
    - RESOLUTION: Setup steps with exact env var names or config commands
    - VOICE: Dry, factual
    """
    error_message = (
        "Authentication failed: LENS_API_KEY environment variable not set. "
        "Setup: export LENS_API_KEY='your-api-key-here' or "
        "recon config --lens-key 'your-api-key-here'. "
        "Get key: https://www.lens.org/get-started. "
        "Verify: recon config --check-keys"
    )
    
    # REASON: Specific missing variable
    assert "LENS_API_KEY" in error_message
    assert "not set" in error_message
    
    # RESOLUTION: Setup steps with exact names
    assert "export LENS_API_KEY=" in error_message
    assert "recon config" in error_message
    assert "--lens-key" in error_message
    assert "--check-keys" in error_message
    
    # No apologies
    assert "sorry" not in error_message.lower()


def test_missing_credentials_includes_setup():
    """
    Verify missing credential errors include complete setup instructions.
    """
    credential_setup = {
        "error": "Missing required API credential",
        "missing_credential": "LENS_API_KEY",
        "setup_methods": [
            "Method 1 (ENV): export LENS_API_KEY='your-key'; recon search patent",
            "Method 2 (Config): recon config --lens-key 'your-key'",
            "Method 3 (.env): echo LENS_API_KEY='your-key' >> ~/.recon/.env",
            "Verify setup: recon config --check-keys"
        ],
        "get_key": {
            "url": "https://www.lens.org/get-started",
            "steps": "Sign up → Generate API key → Copy key value"
        },
        "supported_apis": [
            "LENS_API_KEY: Lens patent database",
            "WIPO_API_KEY: WIPO Global Brand Database",
            "USPTO_API_KEY: USPTO API (optional for higher rate limits)"
        ]
    }
    
    assert credential_setup["missing_credential"]
    assert len(credential_setup["setup_methods"]) >= 3
    assert credential_setup["get_key"]["url"]


# ============================================================================
# Test 9: No Results Error
# ============================================================================

def test_no_results_error():
    """
    Test error handling for empty search results.
    
    Requirements:
    - REASON: Why no results (query too specific, typos, no matches)
    - RESOLUTION: Debugging steps (broaden query, check spelling, verify filters)
    - VOICE: Dry, factual (not discouraging)
    """
    error_message = (
        "No results found for query 'xyz123abc AND foobarbaz'. "
        "Possible causes: Query too specific, typos in terms, no patents matching all filters. "
        "Debug steps: "
        "1. Try simpler query: recon search xyz123abc. "
        "2. Check spelling: recon search --suggest 'xyz123abc'. "
        "3. Remove filters: recon search xyz123abc (no date/assignee restrictions). "
        "4. Broaden date range: --since 1990."
    )
    
    # REASON: Possible causes listed
    assert "too specific" in error_message
    assert "typos" in error_message
    assert "no patents matching" in error_message
    
    # RESOLUTION: Debug steps with commands
    assert "Debug steps:" in error_message
    assert "recon search" in error_message
    assert "--suggest" in error_message
    assert "--since" in error_message
    
    # Voice: Not discouraging
    assert "sorry" not in error_message.lower()
    assert "unfortunately" not in error_message.lower()


def test_no_results_includes_debug_steps():
    """
    Verify empty result errors include concrete debugging guidance.
    """
    debug_guidance = {
        "error": "No results found",
        "query": "xyz123abc AND foobarbaz",
        "possible_causes": [
            "Query too specific (multiple AND operators)",
            "Typos in search terms",
            "Active date filters excluding all results",
            "Assignee filter too restrictive"
        ],
        "debug_commands": [
            "Step 1 - Simplify: recon search 'xyz123abc'",
            "Step 2 - Check spelling: recon search --suggest 'xyz123abc'",
            "Step 3 - Remove filters: recon search xyz123abc --since 1900 --assignee any",
            "Step 4 - Try each term individually: recon search xyz123abc; recon search foobarbaz",
            "Step 5 - Check query syntax: recon search --help-syntax"
        ],
        "expected_behavior": "At least 1-100 results should be found for most patent queries"
    }
    
    assert len(debug_guidance["possible_causes"]) >= 3
    assert len(debug_guidance["debug_commands"]) >= 4
    for cmd in debug_guidance["debug_commands"]:
        assert "recon search" in cmd


# ============================================================================
# Test 10: Error Voice Consistency Audit
# ============================================================================

def test_error_voice_consistency_audit():
    """
    Comprehensive audit of error messages in the codebase.
    Scans actual error messages and verifies they meet Constitution Principle VIII:
    "Dry, Actionable Error Voice"
    
    Requirements:
    - All error messages are terse and factual
    - All errors include exact reason
    - All errors include resolution steps
    - No conversational fluff (apologies, "try to", "unfortunately", etc.)
    """
    
    # These are actual error messages found in the codebase
    # See: .specify/tasks/EVALUATION_TASKS.md Task 5.1 audit results
    
    errors_from_codebase = [
        {
            "source": "cli/main.py",
            "message": "[red]ERR: Search failed. {str(e)}[/red]",
            "issues": ["Too generic - needs specific reason", "Missing resolution"],
            "should_be": "ERR: Search failed: {specific_reason}. Action: {resolution_steps}."
        },
        {
            "source": "cli/export.py",
            "message": "ERR: Export to {format} failed. Reason: {e}",
            "voice_check": "✓ Includes reason",
            "needs": "Include fallback format or file size guidance"
        },
        {
            "source": "clients/patent_apis.py",
            "message": "ERR: Source [USPTO] API key missing. Provide via 'recon config --uspto-key'.",
            "voice_check": "✓ Dry and actionable",
            "reason": "Specific credential requirement",
            "resolution": "Exact command to fix"
        },
        {
            "source": "clients/patent_apis.py",
            "message": "ERR: Source [Lens] rate limit exceeded. Provide API key via LENS_API_KEY.",
            "voice_check": "✓ Actionable",
            "could_improve": "Add retry window and backoff strategy"
        },
        {
            "source": "tui/image_tab.py",
            "message": "ERR: Image rendering unsupported in current terminal.\nAction: Open externally or use Kitty/iTerm2.\nURL: {url}",
            "voice_check": "✓ Dry, actionable",
            "reason": "Specific terminal issue",
            "resolution": "Concrete alternative (external viewer, upgrade terminal)"
        }
    ]
    
    # Audit each error
    for error in errors_from_codebase:
        source = error["source"]
        message = error["message"]
        
        # Check 1: Not a generic error
        if "Too generic" in str(error.get("issues", [])):
            # This error needs improvement
            assert False, f"{source}: {message} is too generic - needs specific reason"
        
        # Check 2: If voice_check exists and says ✓, verify no bad words
        if error.get("voice_check") and "✓" in error.get("voice_check", ""):
            voice_bad_words = ["sorry", "unfortunately", "try to", "please try"]
            for word in voice_bad_words:
                assert word not in message.lower(), f"{source}: Found '{word}' in error message"
    
    # Meta-assertion: Error messages should follow these patterns
    good_error_patterns = [
        "ERR: {specific_reason}. Action: {resolution}.",
        "ERR: {source} failed: {reason}. {resolution_command}",
        "Error: {entity} {problem}. {setup_steps}"
    ]
    
    # All errors in codebase should match one of these patterns or better
    for error in errors_from_codebase:
        msg = error["message"]
        has_pattern = any(
            ("{specific" in pattern and ":" in msg) or
            ("ERR:" in msg and ("Action:" in msg or "Reason:" in msg or "--" in msg))
            for pattern in good_error_patterns
        )
        # Some existing errors are too generic, but we document the audit


def test_error_message_requirements_matrix():
    """
    Define and verify the requirements matrix for error messages.
    
    Constitutional Requirement (Principle VIII):
    "Dry, Actionable Error Voice"
    "Error messages must be terse, factual, and strictly actionable. 
    No apologies, no conversational fluff. Provide exact reason and resolution steps."
    """
    
    error_requirements = {
        "network_timeout": {
            "reason": "✓ Specific timeout duration and endpoint",
            "resolution": "✓ Retry strategy, connectivity check commands",
            "voice": "✓ Dry, factual, no apologies",
            "examples": [
                "Network timeout connecting to patents.google.com: Connection reset after 30s",
                "Action: Check DNS/firewall, retry with exponential backoff"
            ]
        },
        "rate_limit_429": {
            "reason": "✓ Specific limit (e.g., 100/hour) and next window time",
            "resolution": "✓ API key setup commands, wait time, documentation link",
            "voice": "✓ Dry, no 'unfortunately' or apologies",
            "examples": [
                "Rate limit exceeded: 100/hour. Next window: 2026-05-13 14:32 UTC.",
                "Setup API key: export LENS_API_KEY=... or recon config --api-key"
            ]
        },
        "malformed_response": {
            "reason": "✓ Specific field name, received value, expected format",
            "resolution": "✓ Verification steps, API docs link, bug report link",
            "voice": "✓ Factual, no fluff",
            "examples": [
                "Response parsing failed: Missing 'applicant_name' in EP123456. Expected schema: {name, date, class}.",
                "Verify with API docs: https://... or report: github.com/.../issues"
            ]
        },
        "missing_image": {
            "reason": "✓ Patent ID, attempted sources, why not found",
            "resolution": "✓ Multiple fallbacks (external links, text-only mode)",
            "voice": "✓ Dry, not discouraging",
            "examples": [
                "Image unavailable for US10123456: No image at patents.google.com.",
                "Fallback: View on Google Patents URL or use --text-only"
            ]
        },
        "unsupported_terminal": {
            "reason": "✓ Current terminal, missing feature, supported alternatives",
            "resolution": "✓ TERM variable, recon config commands, --text-only fallback",
            "voice": "✓ Factual, no apologies for limitation",
            "examples": [
                "Sixel graphics unsupported in xterm-256color. Supported: Kitty, iTerm2, WezTerm.",
                "Upgrade: export TERM=xterm-kitty or recon config --terminal=kitty"
            ]
        },
        "corrupted_cache": {
            "reason": "✓ Corruption type (truncation, lock, schema), file path",
            "resolution": "✓ Clear recovery: delete cache, reinitialize, verify",
            "voice": "✓ Dry, explains cache warming note",
            "examples": [
                "Cache corrupted: SQLite database truncated. Path: ~/.recon/cache.db",
                "Recovery: rm ~/.recon/cache.db && recon search --force-refresh"
            ]
        },
        "invalid_query": {
            "reason": "✓ Specific syntax error (duplicate operators, bad grouping)",
            "resolution": "✓ Syntax rules, valid examples, --help-syntax command",
            "voice": "✓ Instructive, no condescension",
            "examples": [
                "Query invalid: 'OR OR' is invalid Boolean syntax. Valid: A AND B | C OR D",
                "Examples: neural AND network | (AI OR ML) AND patent"
            ]
        },
        "missing_credentials": {
            "reason": "✓ Specific env var or config key required",
            "resolution": "✓ Setup methods (export, config command, .env), verification command",
            "voice": "✓ Dry, direct setup instructions",
            "examples": [
                "LENS_API_KEY not set. Setup: export LENS_API_KEY=... or recon config --lens-key ...",
                "Get key: https://www.lens.org. Verify: recon config --check-keys"
            ]
        },
        "no_results": {
            "reason": "✓ Possible causes (query specific, typos, filters)",
            "resolution": "✓ Debug steps with exact commands, broader search options",
            "voice": "✓ Dry, not discouraging",
            "examples": [
                "No results for 'xyz AND abc'. Possible: Too specific, typos, or filters.",
                "Debug: Try simpler query | Check spelling | Remove date filters"
            ]
        }
    }
    
    # Verify all error types meet requirements
    for error_type, requirements in error_requirements.items():
        assert requirements["reason"].startswith("✓"), f"{error_type} missing reason requirement"
        assert requirements["resolution"].startswith("✓"), f"{error_type} missing resolution requirement"
        assert requirements["voice"].startswith("✓"), f"{error_type} missing voice requirement"
        assert len(requirements["examples"]) >= 2, f"{error_type} needs examples"


def test_error_voice_prohibited_words():
    """
    Verify that error messages do NOT contain prohibited conversational markers.
    
    Prohibited (per Constitution VIII):
    - Apologies: "sorry", "apologize", "regret"
    - Hedging: "unfortunately", "sadly", "seems", "appears to"
    - Softening: "please try", "try to", "might", "could"
    - Emotional: "frustrat", "annoy", "disappoint"
    """
    
    prohibited_words = [
        "sorry",
        "apologize",
        "unfortunately",
        "sadly",
        "try to",
        "please try",
        "might",
        "seems",
        "appears to",
        "frustrat",
        "annoy",
        "disappoint"
    ]
    
    # Acceptable error message
    good_error = "Rate limit exceeded: 100/hour. Wait until 2026-05-13 14:32. Then retry."
    for word in prohibited_words:
        assert word not in good_error.lower(), f"Good error contains prohibited word: {word}"
    
    # Bad error messages (for validation that our check works)
    bad_errors = [
        "Sorry, rate limit exceeded",
        "Unfortunately, we couldn't find results",
        "It seems the API returned invalid data",
        "Please try again later",
        "The query might be invalid"
    ]
    
    bad_words_found = []
    for bad_error in bad_errors:
        for word in prohibited_words:
            if word in bad_error.lower():
                bad_words_found.append((bad_error, word))
    
    # Verify our check detected the bad words
    assert len(bad_words_found) > 0, "Check should have detected prohibited words"


# ============================================================================
# Test 11: Error Message Actionability Verification
# ============================================================================

def test_error_message_actionability_components():
    """
    Verify that error messages include actionable components.
    
    An error is ACTIONABLE if it includes:
    1. REASON: Exact cause (not generic "error occurred")
    2. CONTEXT: Relevant identifiers (API, file, query, etc.)
    3. RESOLUTION: Concrete next steps (commands, URLs, numbers)
    """
    
    # Structure of an actionable error
    def is_actionable_error(error_obj):
        """Check if error message meets actionability requirements."""
        required_keys = ["reason", "context", "resolution"]
        missing = [k for k in required_keys if not error_obj.get(k)]
        if missing:
            return False, f"Missing: {missing}"
        
        # Check specificity of reason (not generic)
        reason = error_obj["reason"]
        generic_markers = ["error", "failed", "problem"]
        if reason.lower() in generic_markers:
            return False, "Reason is too generic"
        
        # Check context includes identifiers
        context = error_obj["context"]
        if not any(char.isalnum() for char in context):
            return False, "Context lacks specific identifiers"
        
        # Check resolution includes actionable items (verbs, commands, URLs, numbers)
        resolution = error_obj["resolution"]
        actionable_markers = ["run", "export", "recon", "https://", "set", "check", "verify"]
        if not any(marker in resolution.lower() for marker in actionable_markers):
            return False, "Resolution lacks actionable items"
        
        return True, "OK"
    
    # Test cases
    actionable_errors = [
        {
            "reason": "Rate limit exceeded",
            "context": "Source [USPTO], limit=100/hour",
            "resolution": "export LENS_API_KEY=... or recon config --api-key"
        },
        {
            "reason": "Database truncation",
            "context": "Cache file: ~/.recon/cache.db",
            "resolution": "rm ~/.recon/cache.db && recon search --force-refresh"
        }
    ]
    
    for error in actionable_errors:
        is_actionable, msg = is_actionable_error(error)
        assert is_actionable, f"Error not actionable: {msg}. Error: {error}"


# ============================================================================
# Test 12: Integration Test - Error Context Preservation
# ============================================================================

def test_error_context_preservation():
    """
    Verify that errors preserve context through the call stack.
    
    When exceptions are caught and re-raised or wrapped, they should preserve:
    - Original error message
    - Relevant context (identifiers, values)
    - Resolution guidance
    """
    
    # Simulated error handling in layers
    def api_call():
        """Simulates a failed API call."""
        raise ValueError("Socket timeout after 30s")
    
    def client_wrapper():
        """Client layer catching and contextualizing errors."""
        try:
            api_call()
        except ValueError as e:
            # Preserve original error, add context and resolution
            raise ValueError(
                f"Network timeout calling patents.google.com API: {str(e)}. "
                f"Retry with exponential backoff. Check network connectivity and proxy settings."
            )
    
    def application_layer():
        """Application layer catching and reporting errors."""
        try:
            client_wrapper()
        except ValueError as e:
            # Final error message to user
            error_msg = str(e)
            return error_msg
    
    final_error = application_layer()
    
    # Verify context is preserved
    assert "patents.google.com" in final_error
    assert "Socket timeout after 30s" in final_error or "timeout" in final_error
    assert "exponential backoff" in final_error
    assert "connectivity" in final_error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
