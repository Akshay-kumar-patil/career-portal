"""
Patch: replace show_auth_page() in frontend/app.py to include
Google OAuth login button and OAuth error handling.
"""
import re

path = r'd:\aiml\career-platform\frontend\app.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

OLD = '''def show_auth_page():
    st.markdown('<h1 class="main-header">🚀 Career AI Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your AI-Powered Career Operating System</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                # FIX #4: Show explicit error when fields are empty
                if submitted:
                    if not email or not password:
                        st.warning("Please fill in both email and password.")
                    else:
                        result = api.login(email, password)
                        if result:
                            set_auth(result["access_token"], result["user"])
                            st.rerun()

        with tab2:
            with st.form("register_form"):
                full_name = st.text_input("Full Name", placeholder="John Doe")
                email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_pass")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                # FIX #4: Explicit validation
                if submitted:
                    if not full_name or not email or not password:
                        st.warning("Please fill in all fields.")
                    else:
                        result = api.register(email, password, full_name)
                        if result:
                            set_auth(result["access_token"], result["user"])
                            st.rerun()

    st.markdown("---")
    st.markdown("### ✨ Platform Features")'''

NEW = '''def show_auth_page():
    st.markdown('<h1 class="main-header">🚀 Career AI Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your AI-Powered Career Operating System</p>', unsafe_allow_html=True)

    # ── Handle OAuth errors / success redirects ──────────────────────────────
    params = st.query_params
    oauth_error = params.get("oauth_error")
    if oauth_error:
        st.error(f"🔴 Google login failed: `{oauth_error}`. Please try again or use email/password.")
        st.query_params.clear()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # ── Google OAuth button (shown only when backend has it configured) ──
        _google_status = None
        try:
            _google_status = api.google_oauth_status()
        except Exception:
            pass

        if _google_status and _google_status.get("configured"):
            google_url = api.get_google_login_url()
            st.markdown(
                f"""
                <div style="margin-bottom:1rem;">
                    <a href="{google_url}" target="_self" style="
                        display:flex; align-items:center; justify-content:center; gap:12px;
                        padding:0.65rem 1.2rem; border-radius:10px; text-decoration:none;
                        background:#fff; color:#3c4043; font-weight:600; font-size:0.95rem;
                        border:1px solid #dadce0; box-shadow:0 2px 8px rgba(0,0,0,0.12);
                        transition:box-shadow .2s;
                    " onmouseover="this.style.boxShadow='0 4px 16px rgba(0,0,0,0.2)'"
                       onmouseout="this.style.boxShadow='0 2px 8px rgba(0,0,0,0.12)'">
                        <svg width="20" height="20" viewBox="0 0 48 48">
                            <path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.2l6.8-6.8C35.8 2.5 30.2 0 24 0 14.6 0 6.6 5.4 2.7 13.3l7.9 6.1C12.5 13 17.8 9.5 24 9.5z"/>
                            <path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.6 3-2.3 5.5-4.8 7.2l7.5 5.8c4.4-4.1 7.1-10.1 7.1-17z"/>
                            <path fill="#FBBC05" d="M10.6 28.6A14.6 14.6 0 0 1 9.5 24c0-1.6.3-3.2.8-4.6l-7.9-6.1A23.9 23.9 0 0 0 0 24c0 3.9.9 7.5 2.7 10.7l7.9-6.1z"/>
                            <path fill="#34A853" d="M24 48c6.2 0 11.4-2 15.2-5.5l-7.5-5.8c-2 1.4-4.6 2.2-7.7 2.2-6.2 0-11.5-4.2-13.4-9.8l-7.9 6.1C6.6 42.6 14.6 48 24 48z"/>
                        </svg>
                        Continue with Google
                    </a>
                </div>
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:1rem;">
                    <div style="flex:1;height:1px;background:rgba(108,99,255,0.2);"></div>
                    <span style="color:#8892B0;font-size:0.85rem;">or</span>
                    <div style="flex:1;height:1px;background:rgba(108,99,255,0.2);"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    if not email or not password:
                        st.warning("Please fill in both email and password.")
                    else:
                        result = api.login(email, password)
                        if result:
                            set_auth(result["access_token"], result["user"])
                            st.rerun()

        with tab2:
            with st.form("register_form"):
                full_name = st.text_input("Full Name", placeholder="John Doe")
                email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_pass")
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                if submitted:
                    if not full_name or not email or not password:
                        st.warning("Please fill in all fields.")
                    elif password != confirm_password:
                        st.error("❌ Passwords do not match.")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters.")
                    else:
                        result = api.register(email, password, full_name)
                        if result:
                            set_auth(result["access_token"], result["user"])
                            st.rerun()

    st.markdown("---")
    st.markdown("### ✨ Platform Features")'''

# Normalise line endings before matching (the file may have CRLF)
content_lf = content.replace('\r\n', '\n')
old_lf = OLD.replace('\r\n', '\n')
new_lf = NEW.replace('\r\n', '\n')

if old_lf in content_lf:
    content_lf = content_lf.replace(old_lf, new_lf, 1)
    with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(content_lf)
    print('SUCCESS: show_auth_page() updated with Google OAuth button and improved register form.')
else:
    print('ERROR: target block not found.')
    import sys; sys.exit(1)
