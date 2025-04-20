import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy import signal, integrate

# Set page config
st.set_page_config(
    page_title="Signal Modulation Oscilloscope",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stPlotlyChart {
        background-color: #000000;
        border: 1px solid #333;
        border-radius: 5px;
    }
    .channel-controls {
        border: 1px solid #444;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Signal generation

def generate_signal(signal_type, t, amplitude=1.0, frequency=1.0, offset=0.0):
    if signal_type == "Sine Wave":
        return amplitude * np.sin(2 * np.pi * frequency * t) + offset
    elif signal_type == "Square Wave":
        return amplitude * signal.square(2 * np.pi * frequency * t) + offset
    elif signal_type == "Triangle Wave":
        return amplitude * signal.sawtooth(2 * np.pi * frequency * t, 0.5) + offset
    elif signal_type == "Binary Data":
        return amplitude * np.array([1 if np.random.random() > 0.5 else 0 for _ in range(len(t))]) + offset
    elif signal_type == "Carrier Wave":
        return amplitude * np.sin(2 * np.pi * frequency * t) + offset
    return np.zeros_like(t)

# Modulation

def modulate_signal(carrier_freq, message_signal, t, mod_type, mod_index=1.0):
    if mod_type == "AM":
        return (1 + mod_index * message_signal) * np.cos(2 * np.pi * carrier_freq * t)
    elif mod_type == "FM":
        integrated = np.cumsum(message_signal) * (t[1] - t[0])
        return np.cos(2 * np.pi * carrier_freq * t + 2 * np.pi * mod_index * integrated)
    elif mod_type == "PM":
        return np.cos(2 * np.pi * carrier_freq * t + mod_index * message_signal)
    elif mod_type == "ASK":
        return ((message_signal > 0) * np.cos(2 * np.pi * carrier_freq * t)).astype(float)
    elif mod_type == "FSK":
        return np.where(message_signal > 0,
                        np.cos(2 * np.pi * carrier_freq * 1.5 * t),
                        np.cos(2 * np.pi * carrier_freq * t))
    elif mod_type == "PSK":
        return np.cos(2 * np.pi * carrier_freq * t + np.pi * (message_signal > 0))
    return np.zeros_like(t)

# Demodulation (basic)

def demodulate_signal(mod_signal, t, mod_type, carrier_freq):
    if mod_type == "AM":
        envelope = np.abs(mod_signal)
        return envelope - np.mean(envelope)
    elif mod_type == "FM":
        phase = np.unwrap(np.angle(signal.hilbert(mod_signal)))
        return np.diff(phase) / (2 * np.pi * (t[1] - t[0]))
    elif mod_type == "PM":
        return np.unwrap(np.angle(mod_signal))
    return mod_signal

# Plotting

def plot_signals(t, signals, colors, names, visible):
    fig = go.Figure()
    for sig, color, name, show in zip(signals, colors, names, visible):
        if show:
            fig.add_trace(go.Scatter(x=t, y=sig, name=name, line=dict(color=color, width=2)))
    fig.update_layout(
        title="Signal Visualization",
        xaxis_title="Time (s)",
        yaxis_title="Amplitude (V)",
        height=600,
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white'),
        xaxis=dict(gridcolor='#333', zerolinecolor='#666'),
        yaxis=dict(gridcolor='#333', zerolinecolor='#666', range=[-2, 2])
    )
    return fig

# UI for each channel

def channel_controls(channel_num, key_prefix, mod_enabled=False):
    with st.expander(f"Channel {channel_num} Controls", expanded=True):
        enabled = st.checkbox("Enable", value=True, key=f"{key_prefix}_enabled")
        signal_type = st.selectbox("Signal Type", [
            "Sine Wave", "Square Wave", "Triangle Wave", "Binary Data", "Carrier Wave"
        ], key=f"{key_prefix}_type")
        amplitude = st.slider("Amplitude (V)", 0.0, 2.0, 1.0, 0.1, key=f"{key_prefix}_amp")
        frequency = st.slider("Frequency (Hz)", 0.1, 10.0, 1.0, 0.1, key=f"{key_prefix}_freq")
        offset = st.slider("Offset (V)", -2.0, 2.0, 0.0, 0.1, key=f"{key_prefix}_offset")
        mod_type = mod_index = demod = None
        if mod_enabled:
            mod_type = st.selectbox("Modulation Type", ["AM", "FM", "PM", "ASK", "PSK", "FSK"], key=f"{key_prefix}_mod_type")
            mod_index = st.slider("Mod Index", 0.0, 5.0, 1.0, 0.1, key=f"{key_prefix}_mod_index")
            demod = st.checkbox("Show Demodulated Signal", key=f"{key_prefix}_demod")
        return enabled, signal_type, amplitude, frequency, offset, mod_type, mod_index, demod

# Main app

def main():
    st.title("Signal Modulation & Demodulation Trainer (Scientech-style)")
    t = np.linspace(0, 1, 1000)

    with st.sidebar:
        st.header("Global Settings")
        carrier_freq = st.slider("Carrier Frequency (Hz)", 1, 50, 10)

        st.subheader("Channel 1: Message")
        ch1 = channel_controls(1, "ch1")

        st.subheader("Channel 2: Carrier")
        ch2 = channel_controls(2, "ch2")

        st.subheader("Channel 3: Modulated Output")
        ch3 = channel_controls(3, "ch3", mod_enabled=True)

    msg_signal = generate_signal(ch1[1], t, ch1[2], ch1[3], ch1[4]) if ch1[0] else np.zeros_like(t)
    carrier_signal = generate_signal("Carrier Wave", t, ch2[2], carrier_freq, ch2[4]) if ch2[0] else np.zeros_like(t)

    mod_signal = modulate_signal(carrier_freq, msg_signal, t, ch3[5], ch3[6]) if ch3[0] else np.zeros_like(t)
    output_signal = ch3[2] * mod_signal + ch3[4]

    if ch3[8]:
        output_signal = demodulate_signal(output_signal, t, ch3[5], carrier_freq)

    signals = [msg_signal, carrier_signal, output_signal]
    names = ["Message Signal (CH1)", "Carrier (CH2)", f"CH3: {ch3[5]} Modulated"]
    visible = [ch1[0], ch2[0], ch3[0]]
    colors = ["yellow", "cyan", "magenta"]

    fig = plot_signals(t, signals, colors, names, visible)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
