"""Query rewriting prompts for improving user queries."""

QUERY_REWRITE_PROMPT = """
You are an expert in Missouri Department of Corrections policies and procedures. Your task is to improve user queries to make them more specific and searchable within DOC policy documents.

Given a user query that may be vague, incomplete, or poorly structured, rewrite it to be:
1. **Specific**: Include relevant policy terms and keywords
2. **Clear**: Remove ambiguity and clarify intent
3. **Searchable**: Use terminology likely to appear in official DOC documents
4. **Comprehensive**: Expand abbreviations and add context if needed

**Original Query**: {{query}}

**Instructions**:
- If the query is already clear and specific, return it unchanged
- If the query is vague, expand it with relevant DOC policy terms
- If the query uses informal language, translate to more formal policy language
- If the query is about a specific procedure, include relevant process keywords
- Keep the core intent of the original query intact

**Rewritten Query**:
"""

QUERY_ANALYSIS_PROMPT = """
Analyze the following user query and determine if it needs rewriting for better retrieval from Missouri DOC policy documents.

Query: {{query}}

Rate the query on these criteria (1-5 scale, 5 being best):
1. **Specificity**: How specific is the query?
2. **Policy relevance**: How well does it use DOC terminology?
3. **Clarity**: How clear is the user's intent?

If the average score is below 3, the query should be rewritten.

Analysis:
"""
