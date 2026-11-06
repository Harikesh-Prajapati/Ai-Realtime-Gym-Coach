# 🏋️ AI Real-Time GYM Coach

An AI-powered fitness assistant that helps users perform exercises, monitor workout progress, analyze body posture, and receive real-time coaching feedback.

🌐 **Live Demo:** [AI Real-Time GYM Coach](https://real-time-fitness-coach.streamlit.app/)

## 📌 About the Project

AI Real-Time GYM Coach is a smart fitness application developed using Python, Streamlit, Computer Vision, and OpenAI.

The application uses pose detection and exercise-specific logic to track repetitions, analyze exercise posture, and monitor workout performance. It also integrates an AI-powered voice coaching system to provide feedback during workouts.

The main goal is to make fitness training smarter, more interactive, and accessible.

## ✨ Key Features

- **Real-Time Pose Detection:** Detects human body landmarks using computer vision.
- **Exercise Recognition:** Supports multiple exercises and exercise-specific tracking.
- **Automatic Rep Counting:** Tracks exercise repetitions automatically.
- **Posture Analysis:** Monitors exercise form and identifies potential posture issues.
- **AI Voice Coach:** Provides AI-generated workout guidance and feedback.
- **Workout Tracking:** Tracks completed repetitions, sets, and workout duration.
- **Workout History:** Stores workout records for progress monitoring.
- **Interactive Dashboard:** Displays workout metrics through a Streamlit interface.

## 💪 Supported Exercises

1. Squats
2. Push-ups
3. Biceps Curls (Dumbbell)
4. Shoulder Press
5. Lunges

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming |
| Streamlit | Web application and dashboard |
| OpenCV | Image and video processing |
| MediaPipe | Human pose detection |
| OpenAI API | AI-powered coaching |
| SQLite | Workout history storage |
| NumPy | Numerical operations |
| Pandas | Data handling |
| Streamlit-WebRTC | Real-time camera streaming |
| Text-to-Speech | Voice feedback |

## ⚙️ Project Architecture

The project is organized into separate modules for authentication, exercise detection, workout tracking, coaching, and data storage.

```text
AI-Real-Time-GYM-Coach/
│
├── core/
│
├── services/
│   ├── auth/
│   ├── coaching/
│   ├── config/
│   ├── persistence/
│   ├── state/
│   ├── tracking/
│   ├── ui/
│   └── vision/
│
├── static/
│
├── tutorial-info/
│   └── main.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

## 🚀 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Harikesh-Prajapati/ai-realtime-gym-coaches.git
```

### 2. Navigate to the Project Directory

```bash
cd ai-realtime-gym-coaches
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

### 4. Activate the Virtual Environment

**Windows:**

```powershell
.venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure OpenAI API Key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

Never upload your `.env` file or API key to GitHub.

### 7. Run the Application

```bash
python -m streamlit run tutorial-info/main.py
```

The application will open in your browser.

## 🔐 Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | OpenAI model used by the application |

For Streamlit Cloud deployment, configure these values in the application's Secrets settings.

## 🎯 Project Objectives

- Build an AI-powered personal fitness assistant.
- Automate exercise repetition counting.
- Analyze body posture during workouts.
- Provide real-time fitness guidance.
- Maintain workout history and performance records.

## 🔮 Future Improvements

- Add more exercise detection models.
- Improve exercise classification accuracy.
- Introduce personalized workout recommendations.
- Add advanced fitness analytics.
- Improve posture correction and feedback.

## 👨‍💻 Developer

**Harikesh Prajapati**

B.Tech – Electronics and Communication Engineering

Interested in Artificial Intelligence, Machine Learning, Deep Learning, and Computer Vision.

---

⭐ If you find this project interesting, consider giving the repository a star!

**Live Application:** https://real-time-fitness-coach.streamlit.app/
