from common.auth import CurrentPrincipal


def test_current_principal_exposes_subject_and_id() -> None:
    principal = CurrentPrincipal(
        user_id=42,
        username="tester",
        is_active=True,
        token_version=3,
    )

    assert principal.id == 42
    assert principal.subject == "user:42"
