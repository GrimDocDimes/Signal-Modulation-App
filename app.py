import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy import signal

# Set page config
st.set_page_config(
    page_title="Signal Modulation App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve mobile responsiveness
st.markdown("""
    <style>
    .stPlotlyChart {
        width: 100%;
        height: 100%;
    }
    </style>
""", unsafe_allow_html=True)

def generate_signal(signal_type, t):
    if signal_type == "Sine Wave":
        return np.sin(2 * np.pi * t)
    elif signal_type == "Square Wave":
        return signal.square(2 * np.pi * t)
    elif signal_type == "Binary Data":
        return np.array([1 if np.random.random() > 0.5 else 0 for _ in range(len(t))])
    return np.zeros_like(t)

def modulate_signal(carrier_freq, message_signal, t, mod_type):
    carrier = np.sin(2 * np.pi * carrier_freq * t)
    
    if mod_type == "AM":
        modulation_index = 0.5
        return (1 + modulation_index * message_signal) * carrier
    elif mod_type == "FM":
        modulation_index = 2
        integrated_signal = np.cumsum(message_signal) * (t[1] - t[0])
        return np.sin(2 * np.pi * carrier_freq * t + modulation_index * integrated_signal)
    elif mod_type == "PM":
        modulation_index = np.pi/4
        return np.sin(2 * np.pi * carrier_freq * t + modulation_index * message_signal)
    elif mod_type == "ASK":
        return carrier * ((message_signal > 0) * 0.5 + 0.5)
    elif mod_type == "FSK":
        return np.where(message_signal > 0,
                       np.sin(2 * np.pi * carrier_freq * 1.5 * t),
                       np.sin(2 * np.pi * carrier_freq * t))
    elif mod_type == "PSK":
        return carrier * np.sign(message_signal)
    
    return np.zeros_like(t)

def plot_signals(t, message_signal, modulated_signal):
    fig = go.Figure()
    
    # Message Signal
    fig.add_trace(go.Scatter(
        x=t,
        y=message_signal,
        name="Message Signal",
        line=dict(color='blue')
    ))
    
    # Modulated Signal
    fig.add_trace(go.Scatter(
        x=t,
        y=modulated_signal,
        name="Modulated Signal",
        line=dict(color='red')
    ))
    
    fig.update_layout(
        title="Signal Visualization",
        xaxis_title="Time",
        yaxis_title="Amplitude",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def main():
    st.title("Signal Modulation App")
    
    # Create two columns for controls
    col1, col2 = st.columns(2)
    
    with col1:
        signal_type = st.selectbox(
            "Input Signal Type",
            ["Sine Wave", "Square Wave", "Binary Data"]
        )
        
        carrier_freq = st.slider(
            "Carrier Frequency (Hz)",
            min_value=1,
            max_value=20,
            value=10
        )
    
    with col2:
        modulation_type = st.selectbox(
            "Modulation Type",
            ["AM", "FM", "PM", "ASK", "PSK", "FSK"]
        )
    
    # Time vector
    t = np.linspace(0, 1, 1000)
    
    # Generate message signal
    message_signal = generate_signal(signal_type, t)
    
    # Generate modulated signal
    modulated_signal = modulate_signal(carrier_freq, message_signal, t, modulation_type)
    
    # Plot the signals
    fig = plot_signals(t, message_signal, modulated_signal)
    st.plotly_chart(fig, use_container_width=True)
    
    # Control buttons in a single row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Modulate", use_container_width=True):
            st.experimental_rerun()
    
    with col2:
        if st.button("Demodulate", use_container_width=True):
            st.warning("Demodulation feature coming soon!")
    
    with col3:
        if st.button("Reset", use_container_width=True):
            st.experimental_rerun()

if __name__ == "__main__":
    main() 