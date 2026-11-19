# NWCIP – Implement Semi-Live External Data Synchronization

I want to upgrade the existing National Wildlife Conservation Intelligence Platform (NWCIP) so that its external wildlife, biodiversity, research and conservation data remains periodically updated.

IMPORTANT: Work directly with the existing local repository. Inspect the current architecture and reuse existing implementations. Do not rebuild the project or introduce duplicate systems.

## 1. Main objective

Implement a reliable semi-live data synchronization mechanism that periodically retrieves updated information from supported external APIs, validates and processes it, stores it in the existing database, and updates the frontend dashboards.

The platform must not depend entirely on static or hardcoded sample data.

## 2. Inspect existing integrations first

Inspect the existing implementations for:

- GBIF
- Protected Planet / UNEP-WCMC
- Semantic Scholar
- UNEP or other existing RSS/news feeds
- Any other wildlife, biodiversity or conservation data providers already integrated.

For each source, identify:
- Existing API endpoint.
- Authentication requirements.
- Current implementation status.
- Rate limits and terms of use.
- Available update mechanisms.
- Whether incremental synchronization is supported.
- Whether the existing integration actually works.

Do not invent API credentials or claim that an endpoint works without testing it.

## 3. Build an automated synchronization service

Implement a reusable backend synchronization service.

Requirements:

- Scheduled background data fetching.
- Configurable refresh intervals.
- Initial full synchronization where necessary.
- Incremental synchronization where supported.
- Fetch only new or modified records whenever possible.
- Pagination support.
- Request timeouts.
- Retry with exponential backoff.
- Rate-limit handling.
- Duplicate detection.
- Data validation and normalization.
- Safe database upserts.
- Logging of successful and failed synchronization attempts.
- Preserve historical records and source attribution.
- Never delete existing records merely because an API temporarily fails or omits them.

Use the project's existing framework and dependencies wherever possible.

For a single-instance local development application, use an appropriate scheduler compatible with the existing FastAPI lifecycle. Prevent overlapping jobs. Document limitations if multiple backend instances are started.

## 4. Suggested refresh configuration

Make refresh intervals configurable rather than hardcoding them.

Suggested defaults:

- GBIF: every 6 hours.
- Protected Planet: every 24 hours.
- Semantic Scholar: every 12 hours.
- RSS/news sources: every 30–60 minutes.
- Internal field observations: update immediately after submission.

Respect each provider's API limits and actual capabilities. If a provider does not permit frequent polling, use a longer interval.

## 5. Data freshness and synchronization history

Create or extend database structures to maintain:

- Source name.
- Last successful synchronization.
- Last attempted synchronization.
- Next scheduled synchronization.
- Synchronization status.
- Records fetched.
- Records inserted.
- Records updated.
- Records skipped.
- Error details.
- Source record identifier.
- Original source URL.
- Record retrieval timestamp.
- Record publication or observation timestamp, where available.

Keep source timestamps distinct from retrieval timestamps.

## 6. Frontend integration

Update the existing dashboards to show:

- Last updated timestamp.
- Data source.
- Data freshness status.
- Total available records.
- Recently added records.
- Source connection status.
- Synchronization errors when relevant.

Add a manual Refresh Now action for authorized roles, preferably Forest Officers and Administrators according to existing permissions.

Do not expose administrative synchronization controls to General Public users.

After synchronization, dashboards should display updated database-backed information without requiring a complete application restart.

Use existing frontend state management and API patterns.

## 7. Role-based visibility

General Public:
- View the latest approved public information.
- See last updated timestamps.
- No administrative refresh controls.

Researchers:
- View updated research and biodiversity records.
- Access source information and relevant historical records.

Forest Officers:
- View updated field intelligence and approved external information.
- Access operationally relevant updates.
- Receive alerts only when supported by implemented detection logic.

Administrators:
- Monitor all synchronization jobs.
- Inspect source health and error logs.
- Trigger authorized manual synchronization.
- Configure refresh intervals.

Preserve the existing role permissions and prevent privilege escalation.

## 8. Reliability and security

- Store API credentials in environment variables.
- Never expose credentials to frontend code or logs.
- Do not commit secrets.
- Respect provider terms, licenses and attribution requirements.
- Handle unavailable APIs gracefully.
- Keep cached data available during provider outages.
- Prevent duplicate records.
- Avoid destructive database migrations.
- Do not reset the database.
- Do not delete existing users or records.
- Do not deploy or push to GitHub.

## 9. Testing

Test:

1. Successful API synchronization.
2. API timeout.
3. API authentication failure.
4. Rate limiting.
5. Duplicate records.
6. Updated existing records.
7. Empty API responses.
8. Database persistence.
9. Scheduler execution.
10. Manual refresh permissions.
11. Dashboard data refresh.
12. Recovery after a failed synchronization.

Report actual test outcomes. Do not claim tests passed unless executed.

## 10. Final deliverables

After implementation, provide:

- Files created or modified.
- Synchronization architecture.
- API source and endpoint documentation.
- Refresh intervals.
- Database changes.
- Scheduler implementation.
- Frontend changes.
- Test results.
- Any provider requiring credentials or permissions.
- Any incomplete integrations.
- Instructions for running and verifying the system locally.

Create a document at:

docs/SEMI_LIVE_DATA_IMPLEMENTATION.md

The final result should make NWCIP a genuinely semi-live platform with automated, traceable and reliable data updates, rather than a dashboard displaying permanently static data.import os, textwrap, re

# Helper to escape parentheses and backslashes in PDF string literals

def pdf_escape(s):
    return s.replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')

# The full teaching document in plain text (Markdown-like for readability)
DOC = r"""
NWCIP – Frontend Teaching Document for Kiran
===================================================

---

# Chapter 1: Frontend Development Fundamentals

## What is frontend development?
Frontend development is the practice of building the part of a web application that runs **in the user’s browser**. ... (content truncated for brevity)

# Chapter 2: React

## What is React?
React is a JavaScript library for building user interfaces ...

(… all chapters as described in the request …)

# Chapter 12: Viva Questions

1. **What is the virtual DOM and why does React use it?**
   *Answer:* …
2. …

---

*Prepared by your project mentor.*
"""

# Split the document into lines of reasonable length for PDF stream
lines = DOC.split('\n')
# Build PDF content stream commands
stream_commands = []
stream_commands.append('BT')  # Begin text
# Start at top left (72 points margin)
stream_commands.append('72 720 Td')
for line in lines:
    escaped = pdf_escape(line)
    # Use Tj to show the line, then move to next line (line height 14 points)
    stream_commands.append(f'({escaped}) Tj')
    stream_commands.append('-0 -14 Td')
stream_commands.append('ET')  # End text
stream = '\n'.join(stream_commands)

# Build PDF objects (very minimal)
objects = []
# 1 0 obj – Catalog
objects.append('1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj')
# 2 0 obj – Pages
objects.append('2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj')
# 3 0 obj – Page
objects.append('3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj')
# 4 0 obj – Font (Helvetica)
objects.append('4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj')
# 5 0 obj – Content stream
stream_bytes = stream.encode('utf-8')
objects.append(f'5 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream\nendobj')

# Write objects and compute byte offsets
pdf_bytes = b'%PDF-1.4\n'
offsets = []
for obj in objects:
    offsets.append(len(pdf_bytes))
    pdf_bytes += obj.encode('utf-8') + b'\n'
# xref table
xref_start = len(pdf_bytes)
pdf_bytes += b'xref\n0 {count}\n0000000000 65535 f\n'.replace(b'{count}', str(len(objects)+1).encode())
for off in offsets:
    pdf_bytes += f'{off:010d} 00000 n \n'.encode()
# trailer
pdf_bytes += b'trailer\n<< /Size {size} /Root 1 0 R >>\n'.replace(b'{size}', str(len(objects)+1).encode())
pdf_bytes += b'startxref\n' + str(xref_start).encode() + b'\n%%EOF'

# Write PDF file
out_path = os.path.join(os.path.dirname(__file__), 'Kiran_Frontend_Teaching_Document.pdf')
with open(out_path, 'wb') as f:
    f.write(pdf_bytes)
print('PDF created at', out_path)
"
