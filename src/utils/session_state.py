import pandas as pd
import streamlit as st


def init_session_state():
    """Initialize session state with default values"""
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'use_mock' not in st.session_state:
        st.session_state.use_mock = False
    if 'api_error' not in st.session_state:
        st.session_state.api_error = None
    if 'oi_subscription_data' not in st.session_state:
        st.session_state.oi_subscription_data = pd.DataFrame()
    if 'request_delay' not in st.session_state:
        st.session_state.request_delay = 2


def get_client():
    """Get current client from session state"""
    return st.session_state.get('client')


def is_connected():
    """Check if client is connected"""
    return st.session_state.get('connected', False)


def is_mock_mode():
    """Check if using mock mode"""
    return st.session_state.get('use_mock', False)


def update_client(client, connected=True, use_mock=False):
    """Update client in session state"""
    st.session_state.client = client
    st.session_state.connected = connected
    st.session_state.use_mock = use_mock
    st.session_state.api_error = None
