"""Fallback response prompts for handling queries without sufficient context."""

FALLBACK_PROMPT = """
You are assisting with Missouri Department of Corrections policies. The user has asked a question, but the available policy documents do not contain sufficient information to provide a complete answer.

**User Query**: {{query}}

**Available Context** (limited or low relevance):
{{context}}

**Your task**: Provide a helpful response that:
1. Acknowledges that the specific information is not available in the current policy documents
2. Suggests what type of information the user might be looking for
3. Recommends alternative resources or contacts for getting the information
4. If there is any partially relevant information in the context, mention it while clarifying its limitations

**Response Guidelines**:
- Be honest about the limitations of available information
- Remain helpful and supportive
- Suggest logical next steps for the user
- Do not speculate or provide information not in the context
- Maintain the same friendly, conversational tone as regular responses

**Response**:
"""

NO_CONTEXT_FALLBACK = """
I apologize, but I couldn't find specific information about your question in the Missouri DOC policy documents that are currently available to me.

To get accurate information about "{{query}}", I recommend:

• **Contact the Missouri Department of Corrections directly** at their main office
• **Speak with facility staff** if this relates to a specific correctional facility
• **Consult the official DOC website** at doc.mo.gov for the most current policies
• **Contact an attorney** if this is a legal matter requiring professional advice

If you can rephrase your question using different terms or provide more specific details, I might be able to find related information in the available policy documents.

Is there a different way you'd like to ask about this topic?
"""

LOW_CONFIDENCE_RESPONSE = """
Based on the available policy documents, I found some information that might be related to your question about "{{query}}", but I want to be upfront that the information may not fully address what you're looking for.

{{partial_info}}

**Important Note**: The information above may not be complete or may not directly answer your specific question. For the most accurate and up-to-date information, I recommend:

• Contacting the Missouri DOC directly
• Speaking with facility staff if this involves a specific correctional facility  
• Checking the official DOC website at doc.mo.gov

Would you like me to try searching for related topics, or would you prefer to rephrase your question?
"""
