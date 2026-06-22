#!/usr/bin/env python3
"""
dashboard.py - Streamlit dashboard for Shock Absorber Durability Test Bench.

Features:
  - Live / on-demand CSV file loading with auto-refresh
  - Force degradation trend
  - FFT spectrum analysis
  - RMS vibration monitoring
  - Automatic fault detection panel

Launch:
    streamlit run python/dashboard.py
"""

import os
import time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.signal import welch, find_peaks

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Shock Absorber Bench",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ──────────────────────────────────────────────────────────────
FS           = 20.0       # Hz  (50 ms interval)
LSB_PER_G    = 16384.0
FORCE_LOSS   = 0.20
RMS_INCREASE = 0.30

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")
    csv_path = st.text_input("CSV File Path", value="data/sample_data.csv")
    auto_refresh = st.toggle("Auto-refresh (live mode)", value=False)
    refresh_sec  = st.slider("Refresh interval (s)", 1, 30, 5, disabled=not auto_refresh)
    rolling_win  = st.slider("Rolling window (rows)", 50, 2000, 500)
    baseline_pct = st.slider("Baseline % of data", 1, 20, 5) / 100
    st.divider()
    st.markdown("**Failure Thresholds**")
    force_thr = st.number_input("Force loss (%)",   value=20, min_value=1, max_value=50) / 100
    rms_thr   = st.number_input("RMS increase (%)", value=30, min_value=1, max_value=100) / 100

# ── Title ──────────────────────────────────────────────────────────────────
st.title("🔧 Truck Shock Absorber Durability Test Bench")
st.caption("Low-cost durability monitoring with Arduino Uno · MPU6050 · HX711")

# ── Load data ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def load_data(path):
    if not os.path.exists(path):
        return None, f"File not found: {path}"
    try:
        df = pd.read_csv(path)
        df["Az_g"] = df["Az"] / LSB_PER_G
        df["Ax_g"] = df["Ax"] / LSB_PER_G
        df["Ay_g"] = df["Ay"] / LSB_PER_G
        df["Vmag"] = np.sqrt(df["Ax_g"]**2 + df["Ay_g"]**2 + df["Az_g"]**2)
        return df, None
    except Exception as e:
        return None, str(e)

df, err = load_data(csv_path)

if err:
    st.error(f"❌ {err}")
    st.stop()

# ── KPI cards ──────────────────────────────────────────────────────────────
n_base = max(10, int(len(df) * baseline_pct))
base   = df.iloc[:n_base]
final  = df.iloc[-n_base:]

base_force   = base["Force_kg"].mean()
final_force  = final["Force_kg"].mean()
force_loss   = (base_force - final_force) / base_force if base_force > 0 else 0

base_rms     = float(np.sqrt(np.mean(base["Az_g"]**2)))
final_rms    = float(np.sqrt(np.mean(final["Az_g"]**2)))
rms_inc      = (final_rms - base_rms) / base_rms if base_rms > 0 else 0

total_cycles = int(df["Cycle"].max())
duration_min = df["Time_ms"].max() / 60000

fault_force = force_loss > force_thr
fault_rms   = rms_inc   > rms_thr

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Cycles",    f"{total_cycles:,}")
col2.metric("Duration",        f"{duration_min:.1f} min")
col3.metric("Force Reduction", f"{force_loss*100:.1f}%",
            delta_color="inverse", delta=f"{'⚠ FAULT' if fault_force else 'OK'}")
col4.metric("RMS Increase",    f"{rms_inc*100:.1f}%",
            delta_color="inverse", delta=f"{'⚠ FAULT' if fault_rms else 'OK'}")
col5.metric("Overall Status",  "⚠ FAULT" if (fault_force or fault_rms) else "✅ OK")

st.divider()

# ── Rolling metrics ────────────────────────────────────────────────────────
df["Force_roll"] = df["Force_kg"].rolling(rolling_win, min_periods=1).mean()
df["RMS_roll"]   = df["Az_g"].rolling(rolling_win, min_periods=1).apply(
    lambda x: float(np.sqrt(np.mean(x**2))), raw=True
)

# ── Row 1: Force & RMS trends ──────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Force & RMS Trend", "🌊 FFT Spectrum", "🔍 Raw Data"])

with tab1:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=("Force Degradation", "Vibration RMS"),
        vertical_spacing=0.12,
    )

    # Force
    fig.add_trace(go.Scatter(
        x=df["Cycle"], y=df["Force_roll"],
        mode="lines", name="Rolling Force",
        line=dict(color="#1f77b4", width=1.5),
    ), row=1, col=1)
    fig.add_hline(y=base_force,           line_dash="dash", line_color="green",
                  annotation_text="Baseline", row=1, col=1)
    fig.add_hline(y=base_force*(1-force_thr), line_dash="dash", line_color="red",
                  annotation_text=f"−{force_thr*100:.0f}%", row=1, col=1)

    # RMS
    fig.add_trace(go.Scatter(
        x=df["Cycle"], y=df["RMS_roll"],
        mode="lines", name="Rolling RMS",
        line=dict(color="#ff7f0e", width=1.5),
    ), row=2, col=1)
    fig.add_hline(y=base_rms,             line_dash="dash", line_color="green",
                  annotation_text="Baseline", row=2, col=1)
    fig.add_hline(y=base_rms*(1+rms_thr), line_dash="dash", line_color="red",
                  annotation_text=f"+{rms_thr*100:.0f}%", row=2, col=1)

    fig.update_xaxes(title_text="Cycle #", row=2, col=1)
    fig.update_yaxes(title_text="Force (kg)", row=1, col=1)
    fig.update_yaxes(title_text="RMS Az (g)", row=2, col=1)
    fig.update_layout(height=500, showlegend=False, margin=dict(t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col_a, col_b = st.columns(2)
    n_fft   = min(4096, len(base))

    def do_fft(signal):
        sig = signal - signal.mean()
        sp  = np.abs(np.fft.rfft(sig)) / (len(sig)/2)
        fr  = np.fft.rfftfreq(len(sig), d=1.0/FS)
        return fr, sp

    fr_b, sp_b = do_fft(base["Az_g"].values[:n_fft])
    fr_f, sp_f = do_fft(final["Az_g"].values[-n_fft:])

    # detect new peaks
    pk_b, _ = find_peaks(sp_b, height=0.005, distance=3)
    pk_f, _ = find_peaks(sp_f, height=0.005, distance=3)
    base_hz  = {round(fr_b[i],1) for i in pk_b}
    final_hz = {round(fr_f[i],1) for i in pk_f}
    new_hz   = {f for f in final_hz if min((abs(f-b) for b in base_hz), default=99) > 0.5}

    with col_a:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=fr_b, y=sp_b, mode="lines",
                                  name="Initial", line=dict(color="#1f77b4")))
        fig2.update_layout(title="FFT – Initial Stage", height=350,
                           xaxis_title="Frequency (Hz)", yaxis_title="Amplitude (g)",
                           xaxis_range=[0, FS/2], margin=dict(t=40, b=20))
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=fr_f, y=sp_f, mode="lines",
                                  name="Final", line=dict(color="#ff7f0e")))
        for nf in new_hz:
            fig3.add_vline(x=nf, line_dash="dot", line_color="red",
                           annotation_text=f"{nf} Hz ⚠", annotation_position="top right")
        fig3.update_layout(title="FFT – Final Stage", height=350,
                           xaxis_title="Frequency (Hz)", yaxis_title="Amplitude (g)",
                           xaxis_range=[0, FS/2], margin=dict(t=40, b=20))
        st.plotly_chart(fig3, use_container_width=True)

    if new_hz:
        st.warning(f"⚠ New spectral peaks detected in final stage: **{sorted(new_hz)} Hz** — possible internal wear")
    else:
        st.success("✅ No new spectral peaks detected")

    # Welch PSD overlay
    nperseg = min(512, n_fft//4)
    fw_b, pw_b = welch(base["Az_g"].values[:n_fft],   fs=FS, nperseg=nperseg)
    fw_f, pw_f = welch(final["Az_g"].values[-n_fft:], fs=FS, nperseg=nperseg)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=fw_b, y=pw_b, mode="lines",
                              name="Initial", line=dict(color="#1f77b4")))
    fig4.add_trace(go.Scatter(x=fw_f, y=pw_f, mode="lines",
                              name="Final",   line=dict(color="#ff7f0e")))
    fig4.update_layout(
        title="Welch PSD Comparison (Initial vs Final)",
        height=300, yaxis_type="log",
        xaxis_title="Frequency (Hz)", yaxis_title="PSD (g²/Hz)",
        xaxis_range=[0, FS/2], margin=dict(t=40, b=20),
    )
    st.plotly_chart(fig4, use_container_width=True)

with tab3:
    n_show = st.slider("Rows to display", 100, 5000, 500)
    offset = st.slider("Start row", 0, max(0, len(df)-n_show), 0)
    st.dataframe(df.iloc[offset:offset+n_show], use_container_width=True, height=400)
    st.caption(f"Showing rows {offset}–{offset+n_show} of {len(df):,}")

# ── Fault summary ──────────────────────────────────────────────────────────
st.divider()
st.subheader("🔍 Fault Detection Summary")
cols = st.columns(3)
with cols[0]:
    if fault_force:
        st.error(f"⚠ Force loss {force_loss*100:.1f}% > {force_thr*100:.0f}% threshold")
    else:
        st.success(f"✅ Force loss {force_loss*100:.1f}% — within limit")
with cols[1]:
    if fault_rms:
        st.error(f"⚠ RMS increase {rms_inc*100:.1f}% > {rms_thr*100:.0f}% threshold")
    else:
        st.success(f"✅ RMS increase {rms_inc*100:.1f}% — within limit")
with cols[2]:
    if new_hz:
        st.error(f"⚠ New FFT peaks: {sorted(new_hz)} Hz")
    else:
        st.success("✅ No new spectral peaks")

# ── Auto-refresh ───────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_sec)
    st.cache_data.clear()
    st.rerun()
