# Tara Voice Assistant - Android Application

This repository contains the source code for the Tara Voice Assistant, an Android application built with Python and the Kivy framework. The application provides a graphical user interface for interacting with the Tara voice assistant, which includes listening for voice commands, processing them, and playing back audio responses.

## Features

-   **Voice-activated:** The assistant is activated by speaking a trigger phrase (e.g., "Hello Tara").
-   **Graphical User Interface:** A simple and intuitive UI displays the assistant's status (listening, processing, speaking).
-   **Backend Integration:** The application communicates with a backend service to process voice queries and receive audio responses.
-   **Android Ready:** The project is configured with Buildozer to facilitate the creation of an Android APK.

## Project Structure

-   `tara_app/`: This directory contains the main source code for the application.
    -   `main.py`: The Kivy application that defines the user interface.
    -   `backend.py`: The core logic for audio recording, voice activity detection, and communication with the backend API.
    -   `config.py`: A configuration file for storing your API key. **(This file is not tracked by git)**
    -   `images/`: Contains the images used in the application.
-   `buildozer.spec`: The configuration file for building the Android APK with Buildozer.
-   `.gitignore`: Specifies the files and directories that should be ignored by git.

## Setup and Installation

### Prerequisites

-   Python 3.6+
-   A Linux environment is recommended for building the APK with Buildozer.

### Configuration

1.  **API Key:** Before running the application, you need to add your API key.
    -   Open the `tara_app/config.py` file.
    -   Replace `"YOUR_API_KEY"` with your actual API key.

### Building the Android APK

To build the Android application, you will need to have **Buildozer** installed.

1.  **Install Buildozer:**
    ```bash
    pip install buildozer
    ```

2.  **Install Buildozer Dependencies:**
    Buildozer requires several dependencies, such as a Java Development Kit (JDK), the Android SDK, and NDK. The first time you run Buildozer, it will attempt to download and set these up for you.

3.  **Build the APK:**
    Navigate to the root of the project directory (where `buildozer.spec` is located) and run the following command:
    ```bash
    buildozer android debug
    ```
    The first build may take a while as it downloads all the necessary components.

4.  **Locate the APK:**
    Once the build is complete, you will find the generated APK file in the `bin/` directory.

## How to Run (for desktop testing)

You can run the application on your desktop for testing purposes.

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You will need to create a `requirements.txt` file based on the dependencies listed in `buildozer.spec`)*

2.  **Run the application:**
    ```bash
    python tara_app/main.py
    ```