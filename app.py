import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy import signal

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
    .control-panel {
        background-color: #2b2b2b;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
    }
    .stSelectbox, .stSlider {
        margin-bottom: 0.5rem;
    }
    .channel-controls {
        border: 1px solid #444;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Signal generators
def generate_signal(signal_type, t, amplitude=1.0, frequency=1.0, offset=0.0, duty=0.5):
    if signal_type == "Sine Wave":
        return amplitude * np.sin(2 * np.pi * frequency * t) + offset
    elif signal_type == "Square Wave":
        return amplitude * signal.square(2 * np.pi * frequency * t) + offset
    elif signal_type == "Triangle Wave":
        return amplitude * signal.sawtooth(2 * np.pi * frequency * t, 0.5) + offset
    elif signal_type == "Clock Pulse":
        return amplitude * signal.square(2 * np.pi * frequency * t, duty=duty) + offset
    elif signal_type == "Binary Data":
        return amplitude * np.array([1 if np.random.random() > 0.5 else 0 for _ in range(len(t))]) + offset
    elif signal_type == "Carrier Wave":
        return amplitude * np.sin(2 * np.pi * frequency * t) + offset
    return np.zeros_like(t)

# Modulation
def modulate_signal(carrier_freq, message_signal, t, mod_type, mod_index=1.0):
    carrier = np.sin(2 * np.pi * carrier_freq * t)
    if mod_type == "AM":
        return (1 + mod_index * message_signal) * carrier
    elif mod_type == "FM":
        integrated_signal = np.cumsum(message_signal) * (t[1] - t[0])
        return np.sin(2 * np.pi * carrier_freq * t + mod_index * integrated_signal)
    elif mod_type == "PM":
        return np.sin(2 * np.pi * carrier_freq * t + mod_index * message_signal)
    elif mod_type == "ASK":
        return carrier * ((message_signal > 0) * 0.5 + 0.5)
    elif mod_type == "FSK":
        return np.where(message_signal > 0,
                        np.sin(2 * np.pi * carrier_freq * 1.5 * t),
                        np.sin(2 * np.pi * carrier_freq * t))
    elif mod_type == "PSK":
        return carrier * np.sign(message_signal)
    return np.zeros_like(t)

# Simple demodulation (envelope and threshold based)
def demodulate_signal(signal, mod_type):
    if mod_type == "AM":
        return np.abs(signal)
    elif mod_type == "FM" or mod_type == "PM":
        return np.gradient(np.unwrap(np.angle(signal + 1j*signal)))
    elif mod_type == "ASK":
        return signal > 0.1
    elif mod_type == "PSK" or mod_type == "FSK":
        return (signal > 0).astype(float)
    return np.zeros_like(signal)

# Plot
def plot_signals(t, signals, colors, names, visible):
    fig = go.Figure()
    for signal, color, name, is_visible in zip(signals, colors, names, visible):
        if is_visible:
            fig.add_trace(go.Scatter(x=t, y=signal, name=name, line=dict(color=color, width=2)))
    fig.update_layout(
        title="Signal Visualization",
        xaxis_title="Time (s)",
        yaxis_title="Amplitude (V)",
        height=600,
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white'),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor='rgba(0,0,0,0.5)'),
        xaxis=dict(gridcolor='#333', zerolinecolor='#666'),
        yaxis=dict(gridcolor='#333', zerolinecolor='#666', range=[-2, 2])
    )
    return fig

# Controls UI
def channel_controls(channel_num, key_prefix):
    with st.expander(f"Channel {channel_num} Controls", expanded=True):
        enabled = st.checkbox("Enable", value=True, key=f"{key_prefix}_enabled")
        tabs = st.tabs(["Basic Signals", "Modulation", "Demodulation"])
        
        with tabs[0]:  # Basic Signals tab
            basic_signal_options = ["None", "Message Signal", "Clock Pulse", "Carrier Wave"]
            basic_signal = st.selectbox("Select Basic Signal", basic_signal_options, key=f"{key_prefix}_basic_signal")
            
            if basic_signal != "None":
                col1, col2 = st.columns(2)
                with col1:
                    amplitude = st.slider("Amplitude (V)", 0.0, 2.0, 1.0, 0.1, key=f"{key_prefix}_amp")
                    if basic_signal == "Clock Pulse":
                        duty = st.slider("Duty Cycle", 0.1, 0.9, 0.5, 0.1, key=f"{key_prefix}_duty")
                    else:
                        duty = 0.5
                with col2:
                    frequency = st.slider("Frequency (Hz)", 0.1, 10.0, 1.0, 0.1, key=f"{key_prefix}_freq")
                    offset = st.slider("Offset (V)", -2.0, 2.0, 0.0, 0.1, key=f"{key_prefix}_offset")
                
                return enabled, basic_signal, amplitude, frequency, offset, duty, None, None
        
        with tabs[1]:  # Modulation tab
            mod_signal_options = ["None", "AM Modulated", "FM Modulated", "PM Modulated", "ASK Modulated", "PSK Modulated", "FSK Modulated"]
            signal_type = st.selectbox("Select Modulation Signal", mod_signal_options, key=f"{key_prefix}_mod_signal")
            
            if signal_type != "None":
                mod_type = signal_type.split()[0]
                col1, col2 = st.columns(2)
                with col1:
                    amplitude = st.slider("Amplitude (V)", 0.0, 2.0, 1.0, 0.1, key=f"{key_prefix}_amp")
                    if mod_type in ["AM", "FM", "PM"]:
                        mod_index = st.slider("Modulation Index", 0.0, 5.0, 1.0, 0.1, key=f"{key_prefix}_mod")
                    else:
                        mod_index = 1.0
                with col2:
                    offset = st.slider("Offset (V)", -2.0, 2.0, 0.0, 0.1, key=f"{key_prefix}_offset")
                
                return enabled, signal_type, amplitude, None, offset, None, mod_type, mod_index
        
        with tabs[2]:  # Demodulation tab
            demod_signal_options = ["None", "AM Demodulated", "FM Demodulated", "PM Demodulated", "ASK Demodulated", "PSK Demodulated", "FSK Demodulated"]
            demod_selected = st.selectbox("Select Demodulation Signal", demod_signal_options, key=f"{key_prefix}_demod_signal")
            
            if demod_selected != "None":
                col1, col2 = st.columns(2)
                with col1:
                    amplitude = st.slider("Amplitude (V)", 0.0, 2.0, 1.0, 0.1, key=f"{key_prefix}_amp")
                with col2:
                    offset = st.slider("Offset (V)", -2.0, 2.0, 0.0, 0.1, key=f"{key_prefix}_offset")
                
                return enabled, demod_selected, amplitude, None, offset, None, None, None
        
        return enabled, "None", 1.0, 1.0, 0.0, 0.5, None, None

# Main App
def main():
    st.title("3-Channel Signal Modulation Oscilloscope")
    t = np.linspace(0, 10, 10000)

    with st.sidebar:
        st.header("Global Settings")
        carrier_freq = st.slider("Carrier Frequency (Hz)", 1, 50, 10, key="global_carrier_freq")
        message_freq = st.slider("Message Frequency (Hz)", 0.1, 5.0, 1.0, 0.1, key="global_message_freq")
        
        # Generate global signals
        message_signal = generate_signal("Sine Wave", t, 1.0, message_freq, 0.0)
        carrier_signal = generate_signal("Carrier Wave", t, 1.0, carrier_freq, 0.0)
        clock_signal = generate_signal("Clock Pulse", t, 1.0, message_freq, 0.0, duty=0.5)
        
        channels = []
        for i in range(3):
            st.markdown(f"<div class='channel-controls'>", unsafe_allow_html=True)
            channels.append(channel_controls(i+1, f"ch{i+1}"))
            st.markdown("</div>", unsafe_allow_html=True)

    signals, colors, names, visible = [], ['yellow', 'cyan', 'magenta'], [], []

    for i, channel_params in enumerate(channels):
        enabled = channel_params[0]
        signal_type = channel_params[1]
        
        if not enabled:
            signals.append(np.zeros_like(t))
            names.append(f"CH{i+1}: Disabled")
            visible.append(False)
            continue
        
        if "Basic" in str(channel_params):  # Handle basic signals
            if signal_type == "Message Signal":
                signal = message_signal * channel_params[2] + channel_params[4]
            elif signal_type == "Clock Pulse":
                signal = generate_signal("Clock Pulse", t, channel_params[2], channel_params[3], channel_params[4], channel_params[5])
            elif signal_type == "Carrier Wave":
                signal = carrier_signal * channel_params[2] + channel_params[4]
            else:
                signal = np.zeros_like(t)
        elif "Modulated" in signal_type:
            mod_type = channel_params[6]
            mod_index = channel_params[7]
            signal = modulate_signal(carrier_freq, message_signal, t, mod_type, mod_index)
            signal = channel_params[2] * signal + channel_params[4]
        elif "Demodulated" in signal_type:
            mod_type = signal_type.split()[0]
            modulated = modulate_signal(carrier_freq, message_signal, t, mod_type, 1.0)
            signal = demodulate_signal(modulated, mod_type)
            signal = channel_params[2] * signal + channel_params[4]
        else:
            signal = np.zeros_like(t)

        signals.append(signal)
        names.append(f"CH{i+1}: {signal_type}")
        visible.append(True)

    col1, col2, col3 = st.columns([1, 10, 1])
    with col2:
        live_plot = st.empty()
        if 'frozen' not in st.session_state:
            st.session_state['frozen'] = False
        while not st.session_state['frozen']:
            fig = plot_signals(t, signals, colors, names, visible)
            live_plot.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Freeze", use_container_width=True):
            st.session_state['frozen'] = True
    with col2:
        if st.button("Run", use_container_width=True):
            st.session_state['frozen'] = False
    with col3:
        if st.button("Reset", use_container_width=True):
            st.experimental_rerun()

if __name__ == "__main__":
    main()
