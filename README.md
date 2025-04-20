# Signal Modulation App

A web-based signal modulation application built with Streamlit that demonstrates various modulation techniques for communication signals.

## Features

- Generate different types of input signals (Sine Wave, Square Wave, Binary Data)
- Support for multiple modulation types:
  - Amplitude Modulation (AM)
  - Frequency Modulation (FM)
  - Phase Modulation (PM)
  - Amplitude Shift Keying (ASK)
  - Phase Shift Keying (PSK)
  - Frequency Shift Keying (FSK)
- Interactive controls for signal parameters
- Real-time visualization of both message and modulated signals
- Mobile-responsive design

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Running the App Locally

To run the app locally, use the following command:
```bash
streamlit run app.py
```

## Deploying to Streamlit Cloud

1. Create a free account on [Streamlit Cloud](https://streamlit.io/cloud)
2. Connect your GitHub repository
3. Deploy the app with a single click

## Requirements

- Python 3.7+
- Streamlit
- NumPy
- Plotly
- SciPy

## Usage

1. Select the input signal type from the dropdown menu
2. Adjust the carrier frequency using the slider
3. Choose the desired modulation technique
4. Use the control buttons to modulate, demodulate, or reset the signals
5. Observe the real-time visualization of both the message and modulated signals 