from agent.analyzer import analyze_job_description


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