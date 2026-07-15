from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGIN = ROOT / "frontend" / "src" / "app" / "login" / "page.tsx"
README = ROOT / "frontend" / "README.md"


def test_email_login_sends_and_verifies_otp() -> None:
    source = LOGIN.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    assert ".auth.signInWithOtp" in source
    assert ".auth.verifyOtp" in source
    assert 'type: "email"' in source
    assert "emailRedirectTo" not in source
    assert "发送验证码" in source
    assert "{{ .Token }}" in readme


def test_admin_pages_are_guarded_server_side() -> None:
    layout = (ROOT / "frontend" / "src" / "app" / "admin" / "layout.tsx").read_text(encoding="utf-8")

    assert "createServerSupabaseClient" in layout
    assert "isAdminEmail(user.email)" in layout
    assert 'redirect("/login")' in layout
    assert 'redirect("/")' in layout
