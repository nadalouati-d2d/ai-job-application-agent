from agent.analyzer import analyze_job_description
from agent.eligibility import EligibilityStatus, evaluate_eligibility

def test_experience_alternative_prevents_automatic_exclusion():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Candidates must have 2 years of cybersecurity experience required, "
            "or equivalent education and training."
        ),
    )

    result = evaluate_eligibility(
        analysis.requirements,
        max_professional_cybersecurity_years=1,
        candidate_clearance="Reliability",
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 2
    assert analysis.requirements.education_substitution is True
    assert analysis.requirements.experience_alternatives_explicit is True

    assert result.status == EligibilityStatus.NEEDS_REVIEW


def test_extracts_canadian_citizenship_requirement():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="Applicants must be Canadian citizens.",
    )

    assert analysis.requirements.citizenship_required is True

    assert any(
        item.field == "citizenship_required"
        for item in analysis.evidence
    )


def test_extracts_remote_within_canada():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="This position is remote within Canada.",
    )

    assert analysis.requirements.work_arrangement == "remote"
    assert analysis.requirements.remote_eligible_canada is True


def test_detects_senior_title():
    analysis = analyze_job_description(
        title="Senior Cybersecurity Analyst",
        description="Security operations position.",
    )

    assert analysis.requirements.senior_role is True


def test_junior_title_is_not_marked_senior():
    analysis = analyze_job_description(
        title="Junior Cybersecurity Analyst",
        description="Security operations position.",
    )

    assert analysis.requirements.senior_role is not True


def test_unknown_citizenship_remains_unknown():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="We are looking for a security professional.",
    )

    assert analysis.requirements.citizenship_required is None


def test_unknown_remote_eligibility_remains_unknown():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="The successful candidate will join our security team.",
    )

    assert analysis.requirements.remote_eligible_canada is None
    assert analysis.requirements.work_arrangement is None

def test_extracts_required_experience():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Candidates must have at least 2 years of "
            "cybersecurity experience."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 2
    assert analysis.requirements.preferred_cybersecurity_years is None


def test_extracts_preferred_experience():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "2 years of cybersecurity experience preferred."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years == 2


def test_required_and_preferred_are_not_confused():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "1 year of cybersecurity experience required. "
            "3 years of cybersecurity experience preferred."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 1
    assert analysis.requirements.preferred_cybersecurity_years == 3


def test_extracts_minimum_from_required_range():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Candidates must have 1-2 years of cybersecurity experience."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 1


def test_unknown_experience_remains_unknown():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Cybersecurity experience is an asset."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years is None

def test_extracts_plus_years_as_preferred():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="2+ years of cybersecurity experience preferred.",
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years == 2


def test_does_not_treat_asset_as_required():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="2 years of cybersecurity experience is an asset.",
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years is None


def test_does_not_extract_unrelated_experience():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="Candidates must have 5 years of customer service experience.",
    )

    assert analysis.requirements.mandatory_cybersecurity_years is None
    assert analysis.requirements.preferred_cybersecurity_years is None


def test_preserves_exact_experience_evidence():
    description = "Candidates must have at least 2 years of cybersecurity experience."

    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=description,
    )

    evidence = [
        item
        for item in analysis.evidence
        if item.field == "mandatory_cybersecurity_years"
    ]

    assert len(evidence) == 1
    assert evidence[0].quote == (
        "Candidates must have at least 2 years of cybersecurity experience"
    )

def test_detects_education_as_experience_alternative():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "2 years of cybersecurity experience required, "
            "or equivalent education and training."
        ),
    )

    assert analysis.requirements.mandatory_cybersecurity_years == 2
    assert analysis.requirements.education_substitution is True
    assert analysis.requirements.experience_alternatives_explicit is True


def test_detects_internship_as_accepted_experience():
    analysis = analyze_job_description(
        title="Junior Security Analyst",
        description=(
            "Professional experience, internships, or equivalent "
            "hands-on experience will be considered."
        ),
    )

    assert analysis.requirements.accepts_internships is True
    assert analysis.requirements.experience_alternatives_explicit is True


def test_detects_coursework_as_accepted_alternative():
    analysis = analyze_job_description(
        title="Junior SOC Analyst",
        description=(
            "Relevant coursework may be considered in lieu of "
            "professional experience."
        ),
    )

    assert analysis.requirements.accepts_coursework is True
    assert analysis.requirements.experience_alternatives_explicit is True


def test_detects_projects_as_accepted_alternative():
    analysis = analyze_job_description(
        title="Junior Cybersecurity Analyst",
        description=(
            "Relevant cybersecurity projects may substitute "
            "for professional experience."
        ),
    )

    assert analysis.requirements.accepts_projects is True
    assert analysis.requirements.experience_alternatives_explicit is True


def test_detects_recent_graduates():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="Recent graduates are encouraged to apply.",
    )

    assert analysis.requirements.accepts_recent_graduates is True


def test_does_not_infer_alternative_from_education_requirement():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description=(
            "Bachelor's degree in Computer Science required. "
            "2 years of cybersecurity experience required."
        ),
    )

    assert analysis.requirements.education_substitution is not True
    assert analysis.requirements.experience_alternatives_explicit is not True

def test_extracts_required_secret_clearance():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "Candidates must currently hold a valid Secret security clearance."
        ),
    )

    assert analysis.requirements.required_clearance == "Secret"


def test_extracts_required_reliability_clearance():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "Applicants must hold a valid Reliability Status."
        ),
    )

    assert analysis.requirements.required_clearance == "Reliability"


def test_does_not_treat_eligibility_to_obtain_secret_as_current_clearance():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "Candidates must be eligible to obtain a Secret security clearance."
        ),
    )

    assert analysis.requirements.required_clearance is None


def test_does_not_treat_ability_to_obtain_secret_as_current_clearance():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "Must be able to obtain and maintain Secret clearance."
        ),
    )

    assert analysis.requirements.required_clearance is None


def test_unknown_clearance_remains_unknown():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="Join our cybersecurity operations team.",
    )

    assert analysis.requirements.required_clearance is None


def test_preserves_clearance_evidence():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="Candidates must currently hold a valid Secret security clearance.",
    )

    evidence = [
        item
        for item in analysis.evidence
        if item.field == "required_clearance"
    ]

    assert len(evidence) == 1
    assert "Secret security clearance" in evidence[0].quote

def test_does_not_treat_preferred_secret_clearance_as_required():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="Secret security clearance is preferred.",
    )

    assert analysis.requirements.required_clearance is None


def test_does_not_treat_clearance_mention_as_requirement():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "The successful candidate may be processed for "
            "Secret security clearance."
        ),
    )

    assert analysis.requirements.required_clearance is None


def test_does_not_treat_obtain_and_maintain_reliability_as_current_status():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "Candidates must be able to obtain and maintain "
            "Reliability Status."
        ),
    )

    assert analysis.requirements.required_clearance is None


def test_required_secret_clearance_reaches_eligibility_engine():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "Candidates must currently hold a valid "
            "Secret security clearance."
        ),
    )

    result = evaluate_eligibility(
        analysis.requirements,
        max_professional_cybersecurity_years=1,
        candidate_clearance="Reliability",
    )

    assert analysis.requirements.required_clearance == "Secret"
    assert result.status == EligibilityStatus.NEEDS_REVIEW

def test_detects_current_student_only_requirement():
    analysis = analyze_job_description(
        title="Cybersecurity Intern",
        description=(
            "Applicants must be currently enrolled in a "
            "college or university program."
        ),
    )

    assert analysis.requirements.student_only is True


def test_detects_returning_to_school_requirement():
    analysis = analyze_job_description(
        title="Security Intern",
        description=(
            "Candidates must be returning to school "
            "after completion of the internship."
        ),
    )

    assert analysis.requirements.student_only is True


def test_does_not_treat_recent_graduate_language_as_student_only():
    analysis = analyze_job_description(
        title="Junior Security Analyst",
        description=(
            "Students and recent graduates are encouraged to apply."
        ),
    )

    assert analysis.requirements.student_only is not True


def test_does_not_infer_student_only_from_intern_title():
    analysis = analyze_job_description(
        title="Cybersecurity Intern",
        description=(
            "We welcome candidates interested in beginning "
            "a career in cybersecurity."
        ),
    )

    assert analysis.requirements.student_only is not True


def test_preserves_student_only_evidence():
    analysis = analyze_job_description(
        title="Cybersecurity Intern",
        description=(
            "Applicants must be currently enrolled in a "
            "college or university program."
        ),
    )

    evidence = [
        item
        for item in analysis.evidence
        if item.field == "student_only"
    ]

    assert len(evidence) == 1
    assert "currently enrolled" in evidence[0].quote.lower()

def test_detects_enrolled_in_postsecondary_program():
    analysis = analyze_job_description(
        title="Cybersecurity Co-op",
        description=(
            "Candidates must be currently enrolled in a "
            "post-secondary program."
        ),
    )

    assert analysis.requirements.student_only is True


def test_detects_return_to_studies_requirement():
    analysis = analyze_job_description(
        title="Security Intern",
        description=(
            "Applicants must return to studies following "
            "the work term."
        ),
    )

    assert analysis.requirements.student_only is True


def test_does_not_treat_degree_requirement_as_student_only():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "A bachelor's degree in Computer Science or "
            "Cybersecurity is required."
        ),
    )

    assert analysis.requirements.student_only is not True


def test_does_not_treat_completed_education_as_student_only():
    analysis = analyze_job_description(
        title="Junior Security Analyst",
        description=(
            "Candidates must have completed a college or "
            "university cybersecurity program."
        ),
    )

    assert analysis.requirements.student_only is not True

def test_detects_hybrid_work_arrangement():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "This is a hybrid position requiring three days "
            "per week in the office."
        ),
    )

    assert analysis.requirements.work_arrangement == "hybrid"


def test_detects_onsite_work_arrangement():
    analysis = analyze_job_description(
        title="SOC Analyst",
        description="This position is fully onsite in Ottawa.",
    )

    assert analysis.requirements.work_arrangement == "onsite"


def test_detects_on_site_spelling():
    analysis = analyze_job_description(
        title="SOC Analyst",
        description="Employees are required to work on-site five days per week.",
    )

    assert analysis.requirements.work_arrangement == "onsite"


def test_remote_canada_remains_remote():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="This position is remote within Canada.",
    )

    assert analysis.requirements.work_arrangement == "remote"
    assert analysis.requirements.remote_eligible_canada is True


def test_does_not_assume_remote_canada_from_generic_remote():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="This is a fully remote position.",
    )

    assert analysis.requirements.work_arrangement == "remote"
    assert analysis.requirements.remote_eligible_canada is None


def test_preserves_hybrid_evidence():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="This is a hybrid position requiring three days in the office.",
    )

    evidence = [
        item
        for item in analysis.evidence
        if item.field == "work_arrangement"
    ]

    assert len(evidence) == 1
    assert "hybrid" in evidence[0].quote.lower()

def test_detects_hybrid_work_model():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="We operate under a hybrid work model.",
    )

    assert analysis.requirements.work_arrangement == "hybrid"


def test_detects_onsite_required_wording():
    analysis = analyze_job_description(
        title="SOC Analyst",
        description="On-site work is required for this position.",
    )

    assert analysis.requirements.work_arrangement == "onsite"


def test_does_not_treat_remote_option_as_fully_remote():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "Employees may occasionally have the option "
            "to work remotely."
        ),
    )

    assert analysis.requirements.work_arrangement is None
    assert analysis.requirements.remote_eligible_canada is None


def test_does_not_assume_canada_eligibility_from_100_percent_remote():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="This position is 100% remote.",
    )

    assert analysis.requirements.work_arrangement == "remote"
    assert analysis.requirements.remote_eligible_canada is None

def test_extracts_ottawa_location():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="Location: Ottawa, ON.",
    )

    assert analysis.requirements.location == "Ottawa, ON"
    assert analysis.requirements.location_country == "Canada"


def test_extracts_toronto_location():
    analysis = analyze_job_description(
        title="SOC Analyst",
        description="Location: Toronto, ON.",
    )

    assert analysis.requirements.location == "Toronto, ON"
    assert analysis.requirements.location_country == "Canada"


def test_extracts_calgary_location():
    analysis = analyze_job_description(
        title="Cybersecurity Analyst",
        description="Work location: Calgary, AB.",
    )

    assert analysis.requirements.location == "Calgary, AB"
    assert analysis.requirements.location_country == "Canada"


def test_extracts_full_province_name():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="This position is based in Vancouver, British Columbia.",
    )

    assert analysis.requirements.location == "Vancouver, British Columbia"
    assert analysis.requirements.location_country == "Canada"


def test_does_not_infer_location_from_company_background():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "Our company was founded in Ottawa and provides "
            "cybersecurity services across Canada."
        ),
    )

    assert analysis.requirements.location is None
    assert analysis.requirements.location_country is None


def test_city_location_does_not_verify_exact_worksite():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="Location: Toronto, ON.",
    )

    assert analysis.requirements.location == "Toronto, ON"
    assert analysis.requirements.worksite_verified is not True


def test_preserves_location_evidence():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="Work location: Calgary, AB.",
    )

    evidence = [
        item
        for item in analysis.evidence
        if item.field == "location"
    ]

    assert len(evidence) == 1
    assert "Calgary, AB" in evidence[0].quote

def test_location_does_not_capture_following_sentence():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "Location: Toronto, ON. "
            "The successful candidate will join our SOC team."
        ),
    )

    assert analysis.requirements.location == "Toronto, ON"


def test_does_not_infer_location_from_service_area():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "We provide services to customers in Calgary, AB "
            "and across Western Canada."
        ),
    )

    assert analysis.requirements.location is None


def test_does_not_infer_location_from_office_mention():
    analysis = analyze_job_description(
        title="Security Analyst",
        description=(
            "The company maintains offices in Toronto, ON "
            "and Vancouver, BC."
        ),
    )

    assert analysis.requirements.location is None


def test_remote_canada_does_not_invent_city_location():
    analysis = analyze_job_description(
        title="Security Analyst",
        description="This position is remote within Canada.",
    )

    assert analysis.requirements.work_arrangement == "remote"
    assert analysis.requirements.remote_eligible_canada is True
    assert analysis.requirements.location is None