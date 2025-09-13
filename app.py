from flask import Flask, request, render_template_string, session, jsonify, send_from_directory
import requests
import os
import json

# ---------------- CONFIG ----------------
OPENROUTER_API_KEY = "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"  
MODEL = "mistralai/mistral-7b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
You are a highly interactive and friendly medical assistant.
Respond concisely in JSON with keys:
{
  "reply_text": "...",        # human-friendly short response
  "possible_diagnoses": ["..."],
  "severity": "low|medium|high",
  "recommendations": ["..."]
}
Always make the conversation engaging and approachable.
"""

# ---------------- FLASK APP ----------------
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # Cache static files for 5 minutes

# ---------------- TRANSLATION SUPPORT ----------------
translations = {
    "english": {
        "app_name": "MediConnect India",
        "tagline": "Your Personal Health Assistant",
        "health_assistant": "Health Assistant",
        "nearby_doctors": "Nearby Doctors",
        "pharmacy_medicines": "Pharmacy Medicines",
        "nearby_hospitals": "Nearby Hospitals",
        "emergency_services": "Emergency Services",
        "video_consultation": "Video Consultation",
        "describe_symptoms": "Describe your symptoms...",
        "send": "Send",
        "reset_conversation": "Reset Conversation",
        "recommended_doctors": "Recommended Doctors Near You",
        "refresh": "Refresh",
        "medicines_available": "Medicines Available Nearby",
        "nearby_hospitals_clinics": "Nearby Hospitals & Clinics",
        "emergency_help": "Emergency Help",
        "quick_admit": "Quick Admit",
        "call_ambulance": "Call Ambulance",
        "book_appointment": "Book Appointment",
        "video_call": "Video Call",
        "voice_call": "Voice Call",
        "chat": "Chat",
        "get_directions": "Get Directions",
        "specialty": "Specialty",
        "availability": "Availability",
        "languages": "Languages",
        "consultation_fee": "Consultation Fee",
        "pharmacy": "Pharmacy",
        "price": "Price",
        "emergency": "Emergency",
        "wait_time": "Wait Time",
        "beds_available": "Beds Available",
        "distance": "Distance",
        "eta": "ETA",
        "contact": "Contact",
        "current_location": "Current Location",
        "detect_location": "Detect My Location",
        "change_language": "Change Language",
        "select_language": "Select Language",
        "hindi": "Hindi",
        "tamil": "Tamil",
        "english": "English"
    },
    "hindi": {
        "app_name": "मेडीकनेक्ट इंडिया",
        "tagline": "आपका व्यक्तिगत स्वास्थ्य सहायक",
        "health_assistant": "स्वास्थ्य सहायक",
        "nearby_doctors": "आस-पास के डॉक्टर",
        "pharmacy_medicines": "फार्मेसी दवाएं",
        "nearby_hospitals": "आस-पास के अस्पताल",
        "emergency_services": "आपातकालीन सेवाएं",
        "video_consultation": "वीडियो परामर्श",
        "describe_symptoms": "अपने लक्षणों का वर्णन करें...",
        "send": "भेजें",
        "reset_conversation": "वार्तालाप रीसेट करें",
        "recommended_doctors": "आपके निकट अनुशंसित डॉक्टर",
        "refresh": "ताज़ा करें",
        "medicines_available": "आस-पास उपलब्ध दवाएं",
        "nearby_hospitals_clinics": "आस-पास के अस्पताल और क्लीनिक",
        "emergency_help": "आपातकालीन सहायता",
        "quick_admit": "त्वरित भर्ती",
        "call_ambulance": "एम्बुलेंस बुलाएं",
        "book_appointment": "अपॉइंटमेंट बुक करें",
        "video_call": "वीडियो कॉल",
        "voice_call": "वॉइस कॉल",
        "chat": "चैट",
        "get_directions": "दिशा-निर्देश प्राप्त करें",
        "specialty": "विशेषज्ञता",
        "availability": "उपलब्धता",
        "languages": "भाषाएं",
        "consultation_fee": "परामर्श शुल्क",
        "pharmacy": "फार्मेसी",
        "price": "मूल्य",
        "emergency": "आपातकाल",
        "wait_time": "प्रतीक्षा समय",
        "beds_available": "उपलब्ध बिस्तर",
        "distance": "दूरी",
        "eta": "अनुमानित समय",
        "contact": "संपर्क",
        "current_location": "वर्तमान स्थान",
        "detect_location": "मेरा स्थान खोजें",
        "change_language": "भाषा बदलें",
        "select_language": "भाषा चुनें",
        "hindi": "हिंदी",
        "tamil": "तमिल",
        "english": "अंग्रेजी"
    },
    "tamil": {
        "app_name": "மெடிகனெக்ட் இந்தியா",
        "tagline": "உங்கள் தனிப்பட்ட சுகாதார உதவியாளர்",
        "health_assistant": "சுகாதார உதவியாளர்",
        "nearby_doctors": "அருகிலுள்ள மருத்துவர்கள்",
        "pharmacy_medicines": "மருந்தக மருந்துகள்",
        "nearby_hospitals": "அருகிலுள்ள மருத்துவமனைகள்",
        "emergency_services": "அவசர சேவைகள்",
        "video_consultation": "வீடியோ ஆலோசனை",
        "describe_symptoms": "உங்கள் அறிகுறிகளை விவரிக்கவும்...",
        "send": "அனுப்பு",
        "reset_conversation": "உரையாடலை மீட்டமைக்க",
        "recommended_doctors": "உங்களுக்கு அருகிலுள்ள பரிந்துரைக்கப்பட்ட மருத்துவர்கள்",
        "refresh": "புதுப்பிக்க",
        "medicines_available": "அருகிலுள்ள மருந்துகள்",
        "nearby_hospitals_clinics": "அருகிலுள்ள மருத்துவமனைகள் & கிளினிக்குகள்",
        "emergency_help": "அவசர உதவி",
        "quick_admit": "விரைவான சேர்க்கை",
        "call_ambulance": "ஆம்புலன்ஸ் அழைக்க",
        "book_appointment": "பதிவு செய்ய",
        "video_call": "வீடியோ அழைப்பு",
        "voice_call": "குரல் அழைப்பு",
        "chat": "அரட்டை",
        "get_directions": "வழிகாட்டுதல்களைப் பெறுக",
        "specialty": "சிறப்பு",
        "availability": "கிடைக்கும் தன்மை",
        "languages": "மொழிகள்",
        "consultation_fee": "ஆலோசனை கட்டணம்",
        "pharmacy": "மருந்தகம்",
        "price": "விலை",
        "emergency": "அவசர",
        "wait_time": "காத்திருக்கும் நேரம்",
        "beds_available": "கிடைக்கும் படுக்கைகள்",
        "distance": "தூரம்",
        "eta": "மதிப்பிடப்பட்ட நேரம்",
        "contact": "தொடர்பு",
        "current_location": "தற்போதைய இடம்",
        "detect_location": "எனது இடத்தை கண்டறிய",
        "change_language": "மொழியை மாற்று",
        "select_language": "மொழியை தேர்ந்தெடுக்கவும்",
        "hindi": "இந்தி",
        "tamil": "தமிழ்",
        "english": "ஆங்கிலம்"
    }
}

# ---------------- HELPER FUNCTION ----------------
def call_openrouter(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 400
    }
    
    try:
        # Set a timeout to prevent hanging
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # Try to parse JSON
        try:
            import json as js
            parsed = js.loads(content)
            return parsed
        except:
            return {"reply_text": content, "possible_diagnoses": [], "severity": "medium", "recommendations": []}
    except requests.exceptions.Timeout:
        return {"reply_text": "Sorry, the request timed out. Please try again.", "possible_diagnoses": [], "severity": "medium", "recommendations": []}
    except Exception as e:
        return {"reply_text": f"Error: {str(e)}", "possible_diagnoses": [], "severity": "medium", "recommendations": []}

# ---------------- MOCK DATA FOR DEMONSTRATION ----------------
def get_nearby_doctors():
    return [
        {"name": "Dr. Rajesh Kumar", "specialty": "General Physician", "rating": 4.8, "availability": "Today 2 PM", "distance": "0.8 km", "languages": ["Hindi", "English"], "video_consult": True, "fees": "₹500"},
        {"name": "Dr. Priya Sharma", "specialty": "Gynecologist", "rating": 4.9, "availability": "Tomorrow 10 AM", "distance": "1.2 km", "languages": ["Hindi", "Tamil", "English"], "video_consult": True, "fees": "₹800"},
        {"name": "Dr. Amit Patel", "specialty": "Cardiologist", "rating": 4.7, "availability": "Today 4 PM", "distance": "0.5 km", "languages": ["Hindi", "Gujarati", "English"], "video_consult": False, "fees": "₹1200"},
        {"name": "Dr. Lakshmi Venkatesh", "specialty": "Pediatrician", "rating": 4.6, "availability": "Tomorrow 11 AM", "distance": "1.5 km", "languages": ["Tamil", "English"], "video_consult": True, "fees": "₹600"}
    ]

def get_pharmacy_medicines():
    return [
        {"name": "Paracetamol", "price": "₹25", "availability": "In Stock", "pharmacy": "Apollo Pharmacy", "distance": "0.3 km"},
        {"name": "Amoxicillin", "price": "₹120", "availability": "In Stock", "pharmacy": "MedPlus", "distance": "0.7 km"},
        {"name": "Metformin", "price": "₹85", "availability": "Limited Stock", "pharmacy": "Netmeds", "distance": "1.1 km"},
        {"name": "Azithromycin", "price": "₹150", "availability": "In Stock", "pharmacy": "Trust Pharmacy", "distance": "0.9 km"}
    ]

def get_nearby_hospitals():
    return [
        {"name": "Apollo Hospital", "rating": 4.6, "distance": "1.5 km", "emergency": "Available", "wait_time": "15 min", "beds_available": 12},
        {"name": "Fortis Hospital", "rating": 4.4, "distance": "2.3 km", "emergency": "Available", "wait_time": "25 min", "beds_available": 5},
        {"name": "AIIMS Hospital", "rating": 4.9, "distance": "3.1 km", "emergency": "Available", "wait_time": "35 min", "beds_available": 8},
        {"name": "Max Super Specialty Hospital", "rating": 4.7, "distance": "2.8 km", "emergency": "Available", "wait_time": "20 min", "beds_available": 3}
    ]

def get_ambulance_services():
    return [
        {"name": "Central Ambulance Service", "distance": "1.2 km", "eta": "8 min", "contact": "102"},
        {"name": "Quick Response Ambulance", "distance": "0.8 km", "eta": "5 min", "contact": "+91-9876543210"},
        {"name": "LifeCare Ambulance", "distance": "1.5 km", "eta": "10 min", "contact": "+91-9123456789"},
        {"name": "Emergency Response Team", "distance": "2.1 km", "eta": "12 min", "contact": "108"}
    ]

# ---------------- HTML TEMPLATE ----------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MediConnect India - Your Health Assistant</title>
<link rel="stylesheet" href="/static/style.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
<div class="header">
  <div class="container">
    <div class="header-content">
      <div class="logo">
        <i class="fas fa-heartbeat"></i>
        <span id="app-name">MediConnect India</span>
      </div>
      <div class="header-right">
        <div class="tagline" id="tagline">Your Personal Health Assistant</div>
        <div class="language-selector">
          <select id="language-select" onchange="changeLanguage(this.value)">
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
            <option value="tamil">Tamil</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="container">
  <div class="location-section">
    <button class="location-btn" onclick="getLocation()">
      <i class="fas fa-location-arrow"></i> <span id="detect-location-text">Detect My Location</span>
    </button>
    <span id="location-display"></span>
  </div>

  <div class="tabs">
    <div class="tab active" data-tab="chat"><i class="fas fa-comment-medical"></i> <span id="health-assistant-tab">Health Assistant</span></div>
    <div class="tab" data-tab="doctors"><i class="fas fa-user-md"></i> <span id="nearby-doctors-tab">Nearby Doctors</span></div>
    <div class="tab" data-tab="medicines"><i class="fas fa-pills"></i> <span id="pharmacy-medicines-tab">Pharmacy Medicines</span></div>
    <div class="tab" data-tab="hospitals"><i class="fas fa-hospital"></i> <span id="nearby-hospitals-tab">Nearby Hospitals</span></div>
    <div class="tab" data-tab="emergency"><i class="fas fa-ambulance"></i> <span id="emergency-services-tab">Emergency Services</span></div>
    <div class="tab" data-tab="video"><i class="fas fa-video"></i> <span id="video-consultation-tab">Video Consultation</span></div>
  </div>

  <div class="tab-content active" id="chat-tab">
    <div class="chat-container">
      <div id="messages"></div>
      <div class="chat-input">
        <input type="text" id="user-input" placeholder="Describe your symptoms..." autocomplete="off"/>
        <button id="send-btn"><i class="fas fa-paper-plane"></i> <span id="send-text">Send</span></button>
      </div>
    </div>
    <button class="reset-btn" onclick="resetChat()"><i class="fas fa-redo"></i> <span id="reset-conversation-text">Reset Conversation</span></button>
  </div>

  <div class="tab-content" id="doctors-tab">
    <div class="tab-header">
      <h2 id="recommended-doctors-text">Recommended Doctors Near You</h2>
      <button class="refresh-btn" onclick="loadDoctors()"><i class="fas fa-sync-alt"></i> <span id="refresh-text">Refresh</span></button>
    </div>
    <div class="card-grid" id="doctors-list">
      <!-- Doctors will be loaded here -->
    </div>
  </div>

  <div class="tab-content" id="medicines-tab">
    <div class="tab-header">
      <h2 id="medicines-available-text">Medicines Available Nearby</h2>
      <button class="refresh-btn" onclick="loadMedicines()"><i class="fas fa-sync-alt"></i> <span id="refresh-text2">Refresh</span></button>
    </div>
    <div class="card-grid" id="medicines-list">
      <!-- Medicines will be loaded here -->
    </div>
  </div>

  <div class="tab-content" id="hospitals-tab">
    <div class="tab-header">
      <h2 id="nearby-hospitals-text">Nearby Hospitals & Clinics</h2>
      <button class="refresh-btn" onclick="loadHospitals()"><i class="fas fa-sync-alt"></i> <span id="refresh-text3">Refresh</span></button>
    </div>
    <div class="emergency-buttons">
      <button class="emergency-btn ambulance" onclick="callAmbulance()">
        <i class="fas fa-ambulance"></i> <span id="call-ambulance-text">Call Ambulance</span>
      </button>
      <button class="emergency-btn admit" onclick="quickAdmit()">
        <i class="fas fa-procedures"></i> <span id="quick-admit-text">Quick Admit</span>
      </button>
    </div>
    <div class="card-grid" id="hospitals-list">
      <!-- Hospitals will be loaded here -->
    </div>
  </div>

  <div class="tab-content" id="emergency-tab">
    <div class="tab-header">
      <h2 id="emergency-help-text">Emergency Help</h2>
    </div>
    <div class="emergency-buttons">
      <button class="emergency-btn ambulance" onclick="callAmbulance()">
        <i class="fas fa-ambulance"></i> <span id="call-ambulance-text2">Call Ambulance</span>
      </button>
      <button class="emergency-btn admit" onclick="quickAdmit()">
        <i class="fas fa-procedures"></i> <span id="quick-admit-text2">Quick Admit</span>
      </button>
    </div>
    <div class="card-grid" id="ambulance-list">
      <!-- Ambulance services will be loaded here -->
    </div>
  </div>

  <div class="tab-content" id="video-tab">
    <div class="tab-header">
      <h2 id="video-consultation-text">Video Consultation</h2>
      <button class="refresh-btn" onclick="loadDoctors()"><i class="fas fa-sync-alt"></i> <span id="refresh-text4">Refresh</span></button>
    </div>
    <div class="card-grid" id="video-doctors-list">
      <!-- Doctors with video consultation will be loaded here -->
    </div>
  </div>
</div>

<script src="/static/script.js"></script>
</body>
</html>
"""

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    # Initialize session variables if they don't exist
    if 'history' not in session:
        session['history'] = []
    if 'language' not in session:
        session['language'] = 'english'
        
    return render_template_string(HTML_TEMPLATE)

@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory('static', path)

@app.route("/chat", methods=["POST"])
def chat():
    if "history" not in session:
        session["history"] = []
    user_input = request.json.get("message")
    session["history"].append({"role":"user","content":user_input})
    messages = [{"role":"system","content":SYSTEM_PROMPT}] + session["history"]
    
    try:
        reply = call_openrouter(messages)
    except Exception as e:
        reply = {"reply_text": f"Error: {e}", "possible_diagnoses":[], "severity":"medium", "recommendations":[]}
    
    session["history"].append({"role":"assistant","content":reply.get("reply_text","")})
    session.modified = True
    
    return jsonify({"reply": reply})

@app.route("/reset")
def reset():
    session.pop("history", None)
    return "OK"

@app.route("/history")
def history():
    if "history" not in session:
        session["history"] = []
    return jsonify({"history": session.get("history", [])})

@app.route("/doctors")
def doctors():
    return jsonify(get_nearby_doctors())

@app.route("/medicines")
def medicines():
    return jsonify(get_pharmacy_medicines())

@app.route("/hospitals")
def hospitals():
    return jsonify(get_nearby_hospitals())

@app.route("/ambulance")
def ambulance():
    return jsonify(get_ambulance_services())

@app.route("/set_language/<language>")
def set_language(language):
    if language in translations:
        session['language'] = language
    return "OK"

@app.route("/get_translations")
def get_translations():
    lang = session.get('language', 'english')
    return jsonify(translations.get(lang, translations['english']))

# ---------------- CREATE STATIC FILES DIRECTORY ----------------
if not os.path.exists('static'):
    os.makedirs('static')

# Create CSS file with proper encoding
with open('static/style.css', 'w', encoding='utf-8') as f:
    f.write("""
:root {
  --primary: #2a7de1;
  --secondary: #3bb7a4;
  --accent: #ff6b6b;
  --light: #f8f9fa;
  --dark: #343a40;
  --gray: #6c757d;
  --light-gray: #e9ecef;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: #f5f7fa;
  color: var(--dark);
  line-height: 1.6;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

.header {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  padding: 1rem 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.5rem;
  font-weight: bold;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.tagline {
  font-style: italic;
}

.language-selector select {
  padding: 8px 12px;
  border-radius: 20px;
  border: none;
  background: white;
  color: var(--dark);
}

.location-section {
  margin: 20px 0;
  display: flex;
  align-items: center;
  gap: 15px;
}

.location-btn {
  background: var(--primary);
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 600;
}

.location-btn:hover {
  background: #1c68d3;
}

#location-display {
  color: var(--gray);
  font-size: 0.9rem;
}

.tabs {
  display: flex;
  background: white;
  border-radius: 12px 12px 0 0;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  margin-top: 20px;
  flex-wrap: wrap;
}

.tab {
  flex: 1;
  text-align: center;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
  font-weight: 600;
  color: var(--gray);
  min-width: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.tab.active {
  color: var(--primary);
  border-bottom: 3px solid var(--primary);
  background: rgba(42, 125, 225, 0.05);
}

.tab:hover:not(.active) {
  background: var(--light-gray);
}

.tab-content {
  display: none;
  background: white;
  padding: 20px;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  margin-bottom: 20px;
}

.tab-content.active {
  display: block;
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.chat-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 400px;
}

#messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message {
  padding: 12px 16px;
  border-radius: 18px;
  max-width: 80%;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.3s ease;
  line-height: 1.4;
}

.message.show {
  opacity: 1;
  transform: translateY(0);
}

.user {
  background: #e3f2fd;
  align-self: flex-end;
  border-bottom-right-radius: 5px;
}

.assistant {
  background: #e8f5e9;
  align-self: flex-start;
  border-bottom-left-radius: 5px;
}

.chat-input {
  display: flex;
  padding: 15px;
  border-top: 1px solid var(--light-gray);
  background: var(--light);
}

.chat-input input {
  flex: 1;
  padding: 12px 15px;
  border-radius: 25px;
  border: 1px solid var(--light-gray);
  font-size: 16px;
  outline: none;
  transition: border 0.3s;
}

.chat-input input:focus {
  border-color: var(--primary);
}

.chat-input button {
  margin-left: 10px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 25px;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.3s;
  font-weight: 600;
}

.chat-input button:hover {
  background: #1c68d3;
}

.reset-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 25px;
  margin: 10px 0;
  cursor: pointer;
  transition: background 0.3s;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 5px;
}

.reset-btn:hover {
  background: #ff5252;
}

.emergency-buttons {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.emergency-btn {
  padding: 15px 20px;
  border: none;
  border-radius: 12px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: transform 0.2s;
}

.emergency-btn:hover {
  transform: translateY(-2px);
}

.emergency-btn.ambulance {
  background: #ff6b6b;
}

.emergency-btn.admit {
  background: #3bb7a4;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: transform 0.3s, box-shadow 0.3s;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

.card-header {
  padding: 15px;
  background: var(--light);
  border-bottom: 1px solid var(--light-gray);
}

.card-body {
  padding: 15px;
}

.card-footer {
  padding: 15px;
  background: var(--light);
  border-top: 1px solid var(--light-gray);
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.doctor-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.action-btn {
  padding: 8px 12px;
  border: none;
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.action-btn.video {
  background: #4CAF50;
  color: white;
}

.action-btn.voice {
  background: #2196F3;
  color: white;
}

.action-btn.chat {
  background: #FF9800;
  color: white;
}

.badge {
  display: inline-block;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.badge-success {
  background: #e8f5e9;
  color: #2e7d32;
}

.badge-warning {
  background: #fff3e0;
  color: #ef6c00;
}

.badge-info {
  background: #e3f2fd;
  color: var(--primary);
}

.rating {
  color: #ffc107;
  margin-bottom: 5px;
}

.location {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--gray);
  font-size: 0.9rem;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.refresh-btn {
  background: var(--light);
  border: 1px solid var(--light-gray);
  padding: 8px 15px;
  border-radius: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.3s;
}

.refresh-btn:hover {
  background: var(--light-gray);
}

.loading {
  text-align: center;
  padding: 20px;
  color: var(--gray);
}

@media (max-width: 768px) {
  .tabs {
    flex-direction: column;
  }
  
  .card-grid {
    grid-template-columns: 1fr;
  }
  
  .header-content {
    flex-direction: column;
    gap: 10px;
  }
  
  .header-right {
    flex-direction: column;
    gap: 10px;
  }
  
  .emergency-buttons {
    flex-direction: column;
  }
  
  .tab-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
""")

# Create JS file with proper encoding
with open('static/script.js', 'w', encoding='utf-8') as f:
    f.write("""
const messagesDiv = document.getElementById("messages");
const userInput = document.getElementById("user-input");
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
let currentLanguage = 'english';

// Show loading state immediately
document.addEventListener('DOMContentLoaded', function() {
    // Load translations
    loadTranslations();
    
    // Preload tab data
    loadDoctors();
    loadMedicines();
    loadHospitals();
    loadAmbulanceServices();
    
    // Load chat history
    loadChatHistory();
});

// Load translations from server
async function loadTranslations() {
    try {
        const res = await fetch("/get_translations");
        const translations = await res.json();
        updateUIWithTranslations(translations);
    } catch(err) {
        console.error("Error loading translations:", err);
    }
}

// Update UI with translations
function updateUIWithTranslations(translations) {
    // Update all elements with translation keys
    document.getElementById('app-name').textContent = translations.app_name;
    document.getElementById('tagline').textContent = translations.tagline;
    document.getElementById('health-assistant-tab').textContent = translations.health_assistant;
    document.getElementById('nearby-doctors-tab').textContent = translations.nearby_doctors;
    document.getElementById('pharmacy-medicines-tab').textContent = translations.pharmacy_medicines;
    document.getElementById('nearby-hospitals-tab').textContent = translations.nearby_hospitals;
    document.getElementById('emergency-services-tab').textContent = translations.emergency_services;
    document.getElementById('video-consultation-tab').textContent = translations.video_consultation;
    document.getElementById('user-input').placeholder = translations.describe_symptoms;
    document.getElementById('send-text').textContent = translations.send;
    document.getElementById('reset-conversation-text').textContent = translations.reset_conversation;
    document.getElementById('recommended-doctors-text').textContent = translations.recommended_doctors;
    document.getElementById('refresh-text').textContent = translations.refresh;
    document.getElementById('refresh-text2').textContent = translations.refresh;
    document.getElementById('refresh-text3').textContent = translations.refresh;
    document.getElementById('refresh-text4').textContent = translations.refresh;
    document.getElementById('medicines-available-text').textContent = translations.medicines_available;
    document.getElementById('nearby-hospitals-text').textContent = translations.nearby_hospitals_clinics;
    document.getElementById('emergency-help-text').textContent = translations.emergency_help;
    document.getElementById('video-consultation-text').textContent = translations.video_consultation;
    document.getElementById('call-ambulance-text').textContent = translations.call_ambulance;
    document.getElementById('call-ambulance-text2').textContent = translations.call_ambulance;
    document.getElementById('quick-admit-text').textContent = translations.quick_admit;
    document.getElementById('quick-admit-text2').textContent = translations.quick_admit;
    document.getElementById('detect-location-text').textContent = translations.detect_location;
}

// Change language
async function changeLanguage(lang) {
    try {
        await fetch(`/set_language/${lang}`);
        currentLanguage = lang;
        loadTranslations();
    } catch(err) {
        console.error("Error changing language:", err);
    }
}

// Get user's current location
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            showPosition, 
            showError,
            {enableHighAccuracy: true, timeout: 10000, maximumAge: 60000}
        );
    } else {
        document.getElementById("location-display").textContent = "Geolocation is not supported by this browser.";
    }
}

function showPosition(position) {
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;
    
    // Use a geocoding service to get address from coordinates
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
        .then(response => response.json())
        .then(data => {
            const address = data.display_name || `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
            document.getElementById("location-display").textContent = address;
            
            // Reload data with new location
            loadDoctors();
            loadMedicines();
            loadHospitals();
            loadAmbulanceServices();
        })
        .catch(error => {
            document.getElementById("location-display").textContent = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
        });
}

function showError(error) {
    switch(error.code) {
        case error.PERMISSION_DENIED:
            document.getElementById("location-display").textContent = "User denied the request for Geolocation.";
            break;
        case error.POSITION_UNAVAILABLE:
            document.getElementById("location-display").textContent = "Location information is unavailable.";
            break;
        case error.TIMEOUT:
            document.getElementById("location-display").textContent = "The request to get user location timed out.";
            break;
        case error.UNKNOWN_ERROR:
            document.getElementById("location-display").textContent = "An unknown error occurred.";
            break;
    }
}

// Tab switching functionality
tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const tabId = tab.getAttribute('data-tab');
    
    // Update active tab
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    
    // Show active tab content
    tabContents.forEach(content => content.classList.remove('active'));
    document.getElementById(`${tabId}-tab`).classList.add('active');
    
    // Load data for the tab if needed
    if (tabId === 'emergency') {
        loadAmbulanceServices();
    } else if (tabId === 'video') {
        loadVideoDoctors();
    }
  });
});

function appendMessage(role, content) {
    const div = document.createElement("div");
    div.className = "message " + role;
    div.innerHTML = role === "user" ? "<strong>You:</strong> " + content
                                     : "<strong>Assistant:</strong> " + content;
    messagesDiv.appendChild(div);
    setTimeout(()=>{ div.classList.add("show"); }, 50);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    appendMessage("user", text);
    userInput.value = "";

    try {
        const res = await fetch("/chat", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify({message:text})
        });
        const data = await res.json();
        let reply = data.reply.reply_text;
        if (data.reply.possible_diagnoses && data.reply.possible_diagnoses.length) {
            reply += "<br><em>Possible diagnoses:</em> " + data.reply.possible_diagnoses.join(", ");
        }
        if (data.reply.severity) {
            reply += "<br><em>Severity:</em> " + data.reply.severity;
        }
        if (data.reply.recommendations && data.reply.recommendations.length) {
            reply += "<br><em>Recommendations:</em> " + data.reply.recommendations.join(", ");
        }
        appendMessage("assistant", reply);
    } catch(err) {
        appendMessage("assistant", "Error connecting to server.");
    }
}

async function resetChat() {
    await fetch("/reset");
    messagesDiv.innerHTML = "";
}

async function loadChatHistory() {
    try {
        const res = await fetch("/history");
        const data = await res.json();
        data.history.forEach(msg => appendMessage(msg.role, msg.content));
    } catch(err) {
        console.error("Error loading chat history:", err);
    }
}

// Quick admit function
function quickAdmit() {
    alert("Quick admit feature would connect you with the nearest hospital for immediate admission. This would typically redirect to a hospital portal or call their emergency number.");
}

// Call ambulance function
function callAmbulance() {
    alert("Ambulance service would be notified of your location and emergency. They would typically call you back to confirm details.");
}

// Video call function
function videoCallDoctor(doctorId) {
    alert(`Video consultation would start with doctor ${doctorId}. This would typically open a video conferencing interface.`);
}

// Voice call function
function voiceCallDoctor(doctorId) {
    alert(`Voice call would be initiated to doctor ${doctorId}. This would typically use your phone's dialer.`);
}

// Chat with doctor function
function chatWithDoctor(doctorId) {
    alert(`Chat interface would open with doctor ${doctorId}. This would typically open a messaging interface.`);
}

async function loadDoctors() {
    const doctorsList = document.getElementById('doctors-list');
    doctorsList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading doctors...</div>';
    
    try {
        const res = await fetch("/doctors");
        const doctors = await res.json();
        doctorsList.innerHTML = '';
        
        doctors.forEach(doctor => {
            // Use text stars instead of Unicode stars
            const fullStars = Array(Math.floor(doctor.rating)).fill('★').join('');
            const emptyStars = Array(5 - Math.floor(doctor.rating)).fill('☆').join('');
            doctorsList.innerHTML += `
                <div class="card">
                    <div class="card-header">
                        <h3>${doctor.name}</h3>
                        <div class="rating">${fullStars}${emptyStars} ${doctor.rating}</div>
                    </div>
                    <div class="card-body">
                        <p><strong>Specialty:</strong> ${doctor.specialty}</p>
                        <p><strong>Availability:</strong> ${doctor.availability}</p>
                        <p><strong>Languages:</strong> ${doctor.languages.join(', ')}</p>
                        <p><strong>Consultation Fee:</strong> ${doctor.fees}</p>
                    </div>
                    <div class="card-footer">
                        <span class="location"><i class="fas fa-map-marker-alt"></i> ${doctor.distance}</span>
                        <div class="doctor-actions">
                            ${doctor.video_consult ? `<button class="action-btn video" onclick="videoCallDoctor('${doctor.name}')"><i class="fas fa-video"></i> Video</button>` : ''}
                            <button class="action-btn voice" onclick="voiceCallDoctor('${doctor.name}')"><i class="fas fa-phone"></i> Voice</button>
                            <button class="action-btn chat" onclick="chatWithDoctor('${doctor.name}')"><i class="fas fa-comment"></i> Chat</button>
                        </div>
                    </div>
                </div>
            `;
        });
    } catch(err) {
        doctorsList.innerHTML = '<p>Error loading doctors. Please try again.</p>';
    }
}

async function loadVideoDoctors() {
    const videoDoctorsList = document.getElementById('video-doctors-list');
    videoDoctorsList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading doctors with video consultation...</div>';
    
    try {
        const res = await fetch("/doctors");
        const doctors = await res.json();
        const videoDoctors = doctors.filter(doctor => doctor.video_consult);
        
        videoDoctorsList.innerHTML = '';
        
        videoDoctors.forEach(doctor => {
            // Use text stars instead of Unicode stars
            const fullStars = Array(Math.floor(doctor.rating)).fill('★').join('');
            const emptyStars = Array(5 - Math.floor(doctor.rating)).fill('☆').join('');
            videoDoctorsList.innerHTML += `
                <div class="card">
                    <div class="card-header">
                        <h3>${doctor.name}</h3>
                        <div class="rating">${fullStars}${emptyStars} ${doctor.rating}</div>
                    </div>
                    <div class="card-body">
                        <p><strong>Specialty:</strong> ${doctor.specialty}</p>
                        <p><strong>Availability:</strong> ${doctor.availability}</p>
                        <p><strong>Languages:</strong> ${doctor.languages.join(', ')}</p>
                        <p><strong>Consultation Fee:</strong> ${doctor.fees}</p>
                    </div>
                    <div class="card-footer">
                        <span class="location"><i class="fas fa-map-marker-alt"></i> ${doctor.distance}</span>
                        <button class="action-btn video" onclick="videoCallDoctor('${doctor.name}')"><i class="fas fa-video"></i> Start Video Call</button>
                    </div>
                </div>
            `;
        });
    } catch(err) {
        videoDoctorsList.innerHTML = '<p>Error loading doctors. Please try again.</p>';
    }
}

async function loadMedicines() {
    const medicinesList = document.getElementById('medicines-list');
    medicinesList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading medicines...</div>';
    
    try {
        const res = await fetch("/medicines");
        const medicines = await res.json();
        medicinesList.innerHTML = '';
        
        medicines.forEach(medicine => {
            const availabilityClass = medicine.availability === 'In Stock' ? 'badge-success' : 'badge-warning';
            medicinesList.innerHTML += `
                <div class="card">
                    <div class="card-header">
                        <h3>${medicine.name}</h3>
                    </div>
                    <div class="card-body">
                        <p><strong>Pharmacy:</strong> ${medicine.pharmacy}</p>
                        <p><strong>Price:</strong> ${medicine.price}</p>
                    </div>
                    <div class="card-footer">
                        <span class="location"><i class="fas fa-map-marker-alt"></i> ${medicine.distance}</span>
                        <span class="badge ${availabilityClass}">${medicine.availability}</span>
                    </div>
                </div>
            `;
        });
    } catch(err) {
        medicinesList.innerHTML = '<p>Error loading medicines. Please try again.</p>';
    }
}

async function loadHospitals() {
    const hospitalsList = document.getElementById('hospitals-list');
    hospitalsList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading hospitals...</div>';
    
    try {
        const res = await fetch("/hospitals");
        const hospitals = await res.json();
        hospitalsList.innerHTML = '';
        
        hospitals.forEach(hospital => {
            // Use text stars instead of Unicode stars
            const fullStars = Array(Math.floor(hospital.rating)).fill('★').join('');
            const emptyStars = Array(5 - Math.floor(hospital.rating)).fill('☆').join('');
            hospitalsList.innerHTML += `
                <div class="card">
                    <div class="card-header">
                        <h3>${hospital.name}</h3>
                        <div class="rating">${fullStars}${emptyStars} ${hospital.rating}</div>
                    </div>
                    <div class="card-body">
                        <p><strong>Emergency:</strong> ${hospital.emergency}</p>
                        <p><strong>Wait Time:</strong> ${hospital.wait_time}</p>
                        <p><strong>Beds Available:</strong> ${hospital.beds_available}</p>
                    </div>
                    <div class="card-footer">
                        <span class="location"><i class="fas fa-map-marker-alt"></i> ${hospital.distance}</span>
                        <button class="badge badge-info">Get Directions</button>
                    </div>
                </div>
            `;
        });
    } catch(err) {
        hospitalsList.innerHTML = '<p>Error loading hospitals. Please try again.</p>';
    }
}

async function loadAmbulanceServices() {
    const ambulanceList = document.getElementById('ambulance-list');
    ambulanceList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading ambulance services...</div>';
    
    try {
        const res = await fetch("/ambulance");
        const ambulances = await res.json();
        ambulanceList.innerHTML = '';
        
        ambulances.forEach(ambulance => {
            ambulanceList.innerHTML += `
                <div class="card">
                    <div class="card-header">
                        <h3>${ambulance.name}</h3>
                    </div>
                    <div class="card-body">
                        <p><strong>Distance:</strong> ${ambulance.distance}</p>
                        <p><strong>ETA:</strong> ${ambulance.eta}</p>
                    </div>
                    <div class="card-footer">
                        <span class="contact"><i class="fas fa-phone"></i> ${ambulance.contact}</span>
                        <button class="badge badge-info" onclick="callAmbulance()">Call Now</button>
                    </div>
                </div>
            `;
        });
    } catch(err) {
        ambulanceList.innerHTML = '<p>Error loading ambulance services. Please try again.</p>';
    }
}

document.getElementById("send-btn").addEventListener("click", sendMessage);
userInput.addEventListener("keypress", function(e){ if(e.key==="Enter") sendMessage(); });
""")

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
