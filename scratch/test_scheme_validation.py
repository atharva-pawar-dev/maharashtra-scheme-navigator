import hashlib
from datetime import datetime
from scheme_navigator.domain.models import Scheme, RuleNode, SourceReference, Language

def test():
    excerpt = "Applicant must be a woman residing in Maharashtra aged between 21 and 65 years with family income not exceeding Rs 2,50,000."
    sha = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    
    src = SourceReference(
        source_name="Maharashtra GR 28-06-2024",
        source_url="https://gr.maharashtra.gov.in/1145/Government-Resolutions",
        source_kind="government_resolution",
        retrieved_at=datetime.now(),
        page_or_section="Para 3.1",
        evidence_excerpt=excerpt,
        evidence_sha256=sha
    )
    
    rule = RuleNode(
        op="all",
        children=[
            RuleNode(op="eq", field="gender", value="female"),
            RuleNode(op="gte", field="age", value=21),
            RuleNode(op="lte", field="age", value=65),
            RuleNode(op="lte", field="annual_family_income", value=250000)
        ]
    )
    
    s = Scheme(
        scheme_id="test-ladki-bahin-001",
        name="Test Scheme",
        department="Women and Child Development Department",
        summary="A test summary of at least ten characters.",
        benefits=["Rs 1500 monthly"],
        required_documents=["Aadhaar", "Income Certificate"],
        eligibility_rule=rule,
        sources=[src],
        rule_version="1.0.0",
        rule_status="draft",
        publication_authorized=False,
        languages=[Language.EN, Language.MR, Language.HI]
    )
    print("Scheme created successfully:", s.scheme_id)

if __name__ == "__main__":
    test()
