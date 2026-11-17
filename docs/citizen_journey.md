# Citizen Journey Architecture & User Experience Specification

**Document Version:** 1.0.0 (Master UX Blueprint)  
**Date:** November 12, 2026  
**Target Territory:** Maharashtra, India  
**Visual & Cultural Ethos:** "Sahyadri soul. Paithani elegance. Warli artistry. Modern digital craftsmanship."  

---

## 1. The Three Primary Citizen Entry Paths

Citizens arrive at Scheme Navigator with vastly different levels of administrative awareness. The platform presents three distinct, dignified entry points on the homepage:

```
+----------------------------------------------------------------------------------------------------+
|                                    HOMEPAGE HERO SECTION                                           |
|   "Discover Government Opportunities Meant for You" (Sahyadri Skyline & Sinhagad Silhouette)       |
+----------------------------------------------------------------------------------------------------+
                                                 |
             +-----------------------------------+-----------------------------------+
             |                                   |                                   |
             v                                   v                                   v
   +--------------------+              +--------------------+              +--------------------+
   |   JOURNEY A:       |              |   JOURNEY B:       |              |   JOURNEY C:       |
   |   FIND SCHEMES     |              |   EXPLORE SCHEMES  |              |   PREPARE MY       |
   |   FOR ME           |              |   (INDEPENDENT)    |              |   APPLICATION      |
   +--------------------+              +--------------------+              +--------------------+
```

---

## 2. Journey A: "Find Schemes for Me" (Guided AI Discovery)

**Target Persona:** A citizen who does not know which government schemes exist or what they might be entitled to (e.g., a rural woman, an unemployed youth, or an aging farmer).

### Detailed Step-by-Step Flow:
1. **Entry & Consent:** Citizen clicks the primary golden hero card "Find schemes for me" (`माझ्यासाठी योजना शोधा`). A clean consent notice explains that information is processed anonymously to check preliminary eligibility.
2. **Minimal Initial Profile:** Citizen can optionally enter age, gender, district, and approximate income, or immediately click "Start Conversation".
3. **Conversational Multi-Turn Interview:**
   - The assistant asks progressive, contextual questions (e.g. *Are you a resident of Maharashtra? What is your caste category? Do you own agricultural land?*).
   - Quick-reply chips provide single-tap responses.
   - Voice input (`btn-mic`) is available for hands-free audio interaction in Marathi, Hindi, or English.
4. **Live Profile Completeness Meter:** The right-hand column dynamically tracks profile completeness (`०%` to `१००%`), showing green checkmarks as attributes are clarified.
5. **Catalogue-Wide Evaluation:** Once core attributes are gathered, the engine evaluates all active schemes simultaneously.
6. **Results Scoreboard:** Displays schemes organized into 4 distinct groups:
   - *Preliminary Match* (Eligible)
   - *More Information Required* (Needs Info — clearly explained as NOT a rejection)
   - *Not Currently Matching* (Ineligible)
   - *Requires Review* (Needs Review)
7. **Condition Tree Transparency:** Expanding any card reveals exactly which conditions matched (`✓`), which failed (`✗`), and what remains unknown (`?`), along with official Government Resolution citations.
8. **Selection for Preparation:** Clicking "Prepare Application" transitions the citizen seamlessly to Journey C.

---

## 3. Journey B: "Explore Schemes" (Independent Discovery)

**Target Persona:** A citizen, student, social worker, or Village Level Entrepreneur (VLE) who already knows what they are looking for or wants to browse the library freely without undergoing an interview.

### Detailed Step-by-Step Flow:
1. **Instant Access:** Accessible directly from the top navigation bar or the homepage library card.
2. **Dynamic Search & Department Filters:**
   - Real-time instant search across scheme names, departments, and benefit keywords.
   - Department filter pills derived dynamically from active backend records (e.g. Women & Child, Social Justice, Higher Education, Agriculture).
3. **Scheme Cards & Trust Indicators:**
   - Each card displays scheme objective, target beneficiaries, benefit amount (e.g. ₹1,500/month), and verified source tag.
   - Demo fixtures clearly carry the `(demo fixture)` trust badge.
4. **Scheme Detail Modal (`modal-scheme-detail`):**
   - Detailed scheme background and statutory objective.
   - Mandatory and optional document requirements.
   - Authoritative source citations with external links (`gr.maharashtra.gov.in`).
5. **"Check How This Applies to Me" Action:** Citizen can launch a single-scheme focused interview to check their personal eligibility without wading through unrelated scheme questions.

---

## 4. Journey C: "Prepare My Application" (Application Resume & Roadmap)

**Target Persona:** A citizen who has selected an eligible scheme and needs to assemble required certificates, understand prerequisite timelines, and proceed to the official application portal.

### Detailed Step-by-Step Flow:
1. **Session-Bound Resume:**
   - Checks the authenticated citizen session (`threadId`) against `GET /interview/{thread_id}`.
   - If a valid session exists, immediately displays the active scheme, uploaded certificates, and current status.
2. **Reassuring Empty State:**
   - If no session exists (or the previous session expired), the view presents an honest, welcoming empty state:
     > *"You haven't started preparing an application yet. Discover eligible schemes first or browse the catalogue to begin."*
   - Offers dual primary buttons routing to Journey A or Journey B.
3. **Document Workspace:**
   - Scheme-specific document checklist (e.g. Domicile Certificate, Tahsildar Income Certificate, Bank Passbook).
   - Drag-and-drop file uploader (`/documents/audit-upload`) supporting PDF, PNG, and JPEG.
   - Machine extraction preview displaying extracted names, income figures, and review IDs alongside an explicit statutory disclaimer.
4. **Prerequisite Dependency Roadmap:**
   - Renders a topological dependency graph (e.g. Domicile must be obtained before applying for Income Certificate).
   - Displays statutory upper-bound days under Maharashtra Right to Services (RTS) Act 2015.
5. **Safe Portal Hand-Off & Progress Tracking:**
   - Displays verified official portal name and link.
   - Prominently displays the warning: *"Leaving Scheme Navigator: Independent citizen guidance platform. Not an official Government of Maharashtra portal."*
   - Citizen can record progress ("Official Portal Opened", "Submitted on Official Portal (Citizen Reported)").
