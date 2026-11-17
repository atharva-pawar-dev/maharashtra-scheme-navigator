# Scheme Navigator — Executive Demonstration Script (4–6 Minutes)

**Demonstration Title:** One Connected Citizen Journey: Maharashtra Digital Public Infrastructure  
**Presenter:** Lead Solutions Architect / Government Engagement Lead  
**Audience:** Government Ministers, Department Secretaries, Public Sector IT Directors  
**Data Environment:** Synthetic Data Only • Local Deterministic Demo  
**Watermark Notice:** *"Scheme Navigator — Independent Technology Demonstration — Synthetic Data"*  

---

### [0:00 – 0:30] Scene 1: The Citizen Problem in Maharashtra

**Visual on Screen:**  
A visual slide showing multiple open browser tabs: MahaDBT, Aaple Sarkar, ladkibahin portal, and dense PDF Government Resolutions.

**Spoken Dialogue (Presenter):**  
> *"Namaskar and good morning, distinguished secretaries and officers.*  
> *Across Maharashtra, thousands of citizens walk into Gram Panchayat offices, Maha e-Seva Kendras, and government counters every single day looking for government assistance.*  
> *Yet, our welfare landscape is fragmented across more than 35 departments. A college student looking for an OBC scholarship, a smallholder farmer looking for solar pump subsidies, or an elderly widow looking for pension assistance faces multiple portals, complex Government Resolutions, and confusing document prerequisites.*  
> *Often, citizens are told they are 'Ineligible' simply because a portal doesn't know their landholding or category.*  
> *Today, we present Scheme Navigator — an independent digital public infrastructure platform built specifically for the people of Maharashtra to transform this fragmented journey into one clear, trustworthy, and connected experience."*

---

### [0:30 – 1:10] Scene 2: The Homepage & Three Citizen Entry Paths

**Action on Screen:**  
Switch to live browser running `http://127.0.0.1:8000`. Show the warm Maharashtra-inspired aesthetic: Sahyadri mountain horizon, Sinhagad fort silhouette, and Paithani woven borders. Switch language toggle smoothly between English (`en`) and Marathi (`मराठी`).

**Spoken Dialogue (Presenter):**  
> *"Here is the Scheme Navigator homepage. Notice the dignity of the visual identity — inspired by the Sahyadri ranges, Paithani geometry, and Warli heritage, fully responsive on mobile devices and accessible in Marathi, Hindi, and English.*  
> *We recognize that citizens arrive with different levels of administrative awareness. Therefore, we present three distinct, clear paths:*  
> *First, 'Find Schemes for Me' — for citizens who don't know what programs exist.*  
> *Second, 'Explore Schemes' — an independent library for citizens who know exactly what they are looking for.*  
> *And third, 'Prepare My Application' — allowing citizens to resume preparing documents for an existing scheme.*  
> *Let us walk through the primary guided journey."*

---

### [1:10 – 2:15] Scene 3: Guided AI Interview & Live Citizen Profile

**Action on Screen:**  
Click "Find schemes for me" (`माझ्यासाठी योजना शोधा`). Show the multi-turn conversational interview. Answer questions using single-tap quick-reply chips:
- Residence: Maharashtra (`महाराष्ट्र`)
- Age: 28 years
- Gender: Female (`स्त्री`)
- Income: ₹45,000 / year
- Bank Account: Aadhaar Linked (`होय`)  
Show the right-hand **Live Citizen Profile** bar dynamically increasing completeness from `०%` to `८५%`.

**Spoken Dialogue (Presenter):**  
> *"The assistant conducts a gentle, progressive conversation. Notice how questions adapt dynamically to avoid irrelevant inquiries.*  
> *As Sunita answers, the Live Citizen Profile bar on the right updates in real-time with Devanagari numerals. Her data is processed purely in ephemeral memory — zero personally identifiable information is stored on disk or shared.*  
> *Now, with basic attributes established, let us trigger the catalogue-wide evaluation."*

---

### [2:15 – 3:10] Scene 4: Explainable Eligibility & Four-Status Scoreboard

**Action on Screen:**  
Click "Evaluate Schemes" (`पात्रता तपासा`). Show the Results Scoreboard displaying four distinct status metric cards:
1. Preliminary Match (2 Schemes)
2. More Information Required (1 Scheme)
3. Not Currently Matching (0 Schemes)
4. Requires Review (0 Schemes)  
Expand the `Mukhyamantri Majhi Ladki Bahin Yojana` card to reveal the condition tree.

**Spoken Dialogue (Presenter):**  
> *"Within milliseconds, our deterministic three-valued rule engine evaluates Sunita's profile against every active scheme in the catalogue.*  
> *Look at the four-tier scoreboard. Crucially, schemes where information is still missing are classified under 'More Information Required' — NEVER falsely marked as rejections.*  
> *When we expand the Majhi Ladki Bahin card, the citizen sees complete transparency: every matched condition is shown in green, with the exact Government Resolution date — 28 June 2024 — and direct source links.*  
> *There is zero generative AI hallucination here. The rules are executed by an auditable, mathematical engine bound strictly to official Government Resolutions.*  
> *Let us now examine our ground-breaking multi-tier municipal isolation."*

---

### [3:10 – 3:55] Scene 4B: Municipal Corporation Scheme Intelligence & Strict Geographic Isolation (PMC vs. PCMC)

**Action on Screen:**  
In the live profile sidebar, select Local Authority: Pune Municipal Corporation (`mc-pune`).
Show that the results immediately surface PMC municipal schemes such as *Shahari Garib Arogya Yojana* and *Maulana Azad Scholarship*.
Highlight that neighboring Pimpri Chinchwad (PCMC) schemes (such as *Free Bicycle Distribution for Girls* and *Sewing Machine Subsidy*) are **strictly excluded** with the explicit reason: *"Geographically inapplicable: Programme belongs to PCMC and does not apply to residents of mc-pune."*
Now change the local body from `mc-pune` to `mc-pimpri-chinchwad`.
Show how results instantly recalculate: PMC schemes flip to ineligible, and PCMC schemes become active.
Finally, demonstrate entering border PIN `411027` (Aundh/Sangvi boundary) without a selected body: show that the platform refuses to guess, returning `LOCATION_REQUIRES_CONFIRMATION` with candidate corporations.

**Spoken Dialogue (Presenter):**  
> *"One of our greatest engineering breakthroughs is multi-tier geographic isolation across all 29 Municipal Corporations and 424 Urban Local Bodies in Maharashtra.*  
> *Notice: when Sunita resides in Pune Municipal Corporation, she receives PMC's Shahari Garib Arogya Yojana.*  
> *At the exact same time, schemes from neighboring Pimpri Chinchwad are strictly quarantined. She will never be misled into applying for a PCMC bicycle or sewing machine grant that she cannot legally receive.*  
> *And if she moves to Pimpri Chinchwad, the engine recalculates dynamically without stale artifacts.*  
> *Furthermore, for border postal codes like 411027 traversing the PMC-PCMC boundary, the platform never guesses. It transparently asks the citizen to confirm their exact corporation limits.*  
> *Let us now click 'Prepare Application'."*

---

### [3:55 – 4:45] Scene 5: Document Preparation & Pre-Audit Workspace

**Action on Screen:**  
Navigate to the Document Workspace (`view-documents`). Show the scheme-specific checklist for Majhi Ladki Bahin: Domicile, Tahsildar Income Certificate, and Bank Passbook.  
Drag and drop the synthetic test file `demo_income_certificate.png` into the uploader. Show the machine extraction table rendering:
- Document Type: `income_certificate`
- Extracted Name: `Sunita Ramesh Patil`
- Annual Income: `₹45,000`
- Review ID: `REV-xxxx`  
Point out the statutory machine extraction disclaimer banner.

**Spoken Dialogue (Presenter):**  
> *"Here, the citizen sees the exact documents required before applying.*  
> *Sunita uploads her Tahsildar Income Certificate. The platform performs an instant pre-audit, extracting the family income and financial year.*  
> *Notice our explicit trust banner: the platform informs the citizen that this machine extraction is for preparation only and does not constitute official government sanction.*  
> *If a document has skewed text or low confidence below 75%, it is automatically flagged for human reviewer audit rather than making assumptions."*

---

### [4:00 – 4:45] Scene 6: Prerequisite Roadmap & Safe Portal Hand-Off

**Action on Screen:**  
Click "View Prerequisite Roadmap" (`पूर्वतयारी रोडमॅप पहा`). Show the DAG dependency graph showing RTS timelines:
- Domicile Certificate: 15 Working Days (Aaple Sarkar)
- Income Certificate: 15 Working Days (Aaple Sarkar)  
Show the `roadmap-portal-container` displaying the verified official portal destination (`https://ladkibahin.maharashtra.gov.in/`), pre-submission checklist, and the citizen progress reporting buttons.

**Spoken Dialogue (Presenter):**  
> *"Before a citizen wastes time at a counter, our Prerequisite Roadmap calculates the critical path of statutory certificates under the Maharashtra Right to Services Act.*  
> *And when preparation is complete, look at our Safe Portal Hand-Off.*  
> *Because neither MahaDBT nor Aaple Sarkar provides open submission APIs, Scheme Navigator does NOT use fragile web scraping or CAPTCHA bypasses. It provides verified official links, pre-submission checklists, and clear hand-off disclaimers.*  
> *When Sunita clicks 'Open Official Portal', she is safely transferred to the official government portal to submit personally, and can report her submission status upon return."*

---

### [4:45 – 5:30] Scene 7: Governance, Security & The Path to Government Partnership

**Action on Screen:**  
Show architecture slide displaying DPDP Act 2023 compliance, 24-hour retention purge, and the transition from Release Path A to Release Path B.

**Spoken Dialogue (Presenter):**  
> *"Under the hood, Scheme Navigator is engineered for enterprise public service:*  
> *It adheres strictly to the Digital Personal Data Protection Act 2023: all sessions automatically purge after 24 hours; full Aadhaar numbers and passwords are never stored.*  
> *Every candidate scheme remains in a quarantined draft state until cryptographically signed.*  
> *Today, Scheme Navigator is ready as an Independent Public Platform — Release Path A.*  
> *However, our architecture is already built for formal Government of Maharashtra Partnership — Release Path B: with bilateral authorization, Scheme Navigator can connect to MahaSarathi, authenticate via MahaONE Single Sign-On, pull verified certificates from DigiLocker, and submit applications directly to departmental gateways."*

---

### [5:30 – 6:00] Scene 8: Closing & Call to Action

**Visual on Screen:**  
Return to the homepage hero with the tagline:  
**"One connected citizen journey. Better discovery. Clearer eligibility. Safer application preparation."**

**Spoken Dialogue (Presenter):**  
> *"One connected citizen journey.*  
> *Better discovery.*  
> *Clearer, evidence-backed eligibility.*  
> *Safer application preparation.*  
> *Scheme Navigator demonstrates how modern digital craftsmanship can bridge the gap between complex government policy and the citizens of Maharashtra.*  
> *We invite leadership from the Directorate of Information Technology and state departments to explore a collaborative pilot.*  
> *Thank you very much. Jai Hind, Jai Maharashtra."*
