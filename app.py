import streamlit as st
import numpy as np
import plotly.graph_objs as go
from scipy import signal
import time

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        .main {
            background-color: #0e1117;
        }
        .stSlider > div > div > div > div {
            background: #1f77b4;
        }
        .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("3-Channel Signal Modulation Oscilloscope")


def generate_signal(signal_type, t, amplitude=1.0, frequency=1.0, offset=0.0, custom_binary=None, bit_duration=0.1):
    if signal_type == "Sine Wave":
        return amplitude * np.sin(2 * np.pi * frequency * t) + offset
    elif signal_type == "Clock Pulse":
        return amplitude * signal.square(2 * np.pi * frequency * t) + offset
    elif signal_type == "Custom Binary Clock Pulse":
        if custom_binary is None:
            return np.zeros_like(t)

        samples_per_bit = int(bit_duration * len(t) / (t[-1] - t[0]))
        waveform = []
        for bit in custom_binary:
            val = amplitude if bit == '1' else 0
            waveform.extend([val] * samples_per_bit)
        waveform = np.array(waveform[:len(t)])
        if len(waveform) < len(t):
            waveform = np.pad(waveform, (0, len(t) - len(waveform)), 'constant')
        return waveform + offset
    elif signal_type == "Carrier Wave":
        return amplitude * np.sin(2 * np.pi * frequency * t) + offset
    return np.zeros_like(t)


def modulate_signal(fc, message, t, mod_type="AM", modulation_index=1.0):
    if mod_type == "AM":
        return (1 + modulation_index * message) * np.cos(2 * np.pi * fc * t)
    elif mod_type == "FM":
        return np.cos(2 * np.pi * fc * t + modulation_index * np.cumsum(message))
    elif mod_type == "PM":
        return np.cos(2 * np.pi * fc * t + modulation_index * message)
    elif mod_type == "ASK":
        return (1 + message) * np.cos(2 * np.pi * fc * t)
    elif mod_type == "PSK":
        return np.cos(2 * np.pi * fc * t + np.pi * message)
    elif mod_type == "FSK":
        f1 = fc
        f2 = fc * (1 + modulation_index)
        return np.where(message > 0, np.cos(2 * np.pi * f2 * t), np.cos(2 * np.pi * f1 * t))
    return message


def channel_controls(channel_num, key_prefix):
    with st.expander(f"Channel {channel_num} Controls", expanded=True):
        enabled = st.checkbox("Enable", value=True, key=f"{key_prefix}_enabled")

        signal_options = [
            "Message Signal",
            "Carrier Wave",
            "AM Modulated",
            "FM Modulated",
            "PM Modulated",
            "ASK Modulated",
            "PSK Modulated",
            "FSK Modulated"
        ]
        signal_type = st.selectbox("Signal Type", signal_options, key=f"{key_prefix}_type")

        msg_subtype = st.selectbox(
            "Message Signal Type",
            ["Sine Wave", "Clock Pulse", "Custom Binary Clock Pulse"],
            key=f"{key_prefix}_msgtype") if "Message" in signal_type else None

        custom_binary = None
        bit_duration = 0.1

        if msg_subtype == "Custom Binary Clock Pulse":
            custom_binary = st.text_input("Enter binary string (e.g. 10110011):", "10110011", key=f"{key_prefix}_bin")
            bit_duration = st.slider("Bit Duration (s)", 0.01, 1.0, 0.1, 0.01, key=f"{key_prefix}_bitdur")

        col1, col2 = st.columns(2)
        with col1:
            amplitude = st.slider("Amplitude (V)", 0.0, 2.0, 1.0, 0.1, key=f"{key_prefix}_amp")
            frequency = st.slider("Frequency (Hz)", 0.1, 10.0, 1.0, 0.1, key=f"{key_prefix}_freq")
        with col2:
            offset = st.slider("Offset (V)", -2.0, 2.0, 0.0, 0.1, key=f"{key_prefix}_offset")
            if "Modulated" in signal_type and "AM" in signal_type:
                mod_index = st.slider("Modulation Index", 0.0, 5.0, 1.0, 0.1, key=f"{key_prefix}_mod")
            else:
                mod_index = 1.0

        return enabled, signal_type, amplitude, frequency, offset, mod_index, msg_subtype, custom_binary, bit_duration


def main():
    st.subheader("Signal Visualization")
    run_state = st.radio("Operation Mode", ["Freeze", "Run", "Reset"], horizontal=True, index=1)

    t_end = 5  # seconds
    fs = 1000  # samples per second
    t = np.linspace(0, t_end, t_end * fs)

    channels = [
        channel_controls(1, "ch1"),
        channel_controls(2, "ch2"),
        channel_controls(3, "ch3")
    ]

    if run_state == "Reset":
        st.rerun()

    placeholder = st.empty()
    start_time = time.time()

    while run_state == "Run":
        elapsed = time.time() - start_time
        t_live = np.linspace(elapsed, elapsed + 1, fs)
        signals, names, visible = [], [], []

        for i, (enabled, signal_type, amp, freq, offset, mod_idx, msg_subtype, custom_binary, bit_dur) in enumerate(channels):
            if "Message" in signal_type:
                msg_signal = generate_signal(msg_subtype, t_live, amp, freq, offset, custom_binary, bit_dur)
                signal_data = msg_signal
            elif "Carrier" in signal_type:
                signal_data = generate_signal("Carrier Wave", t_live, amp, freq, offset)
            else:
                msg_signal = generate_signal("Sine Wave", t_live, 1.0, 1.0, 0.0)
                signal_data = modulate_signal(freq, msg_signal, t_live, signal_type.split()[0], mod_idx)
                signal_data = amp * signal_data + offset

            signals.append(signal_data)
            names.append(f"CH{i+1}: {signal_type}")
            visible.append(enabled)

        fig = go.Figure()
        for i, (sig, name, vis) in enumerate(zip(signals, names, visible)):
            if vis:
                fig.add_trace(go.Scatter(x=t_live, y=sig, mode='lines', name=name))

        fig.update_layout(
            xaxis_title="Time (s)",
            yaxis_title="Amplitude (V)",
            template="plotly_dark",
            height=500,
            margin=dict(l=40, r=40, t=40, b=40)
        )

        placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(0.05)

        run_state = st.session_state.get("__streamlit__radio__Operation Mode")
        if run_state != "Run":
            break

if __name__ == "__main__":
    main()
