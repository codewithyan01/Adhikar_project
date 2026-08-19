import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Mic, 
  Bot, 
  User, 
  Sparkles, 
  CheckCircle2, 
  HelpCircle,
  Volume2,
  VolumeX,
  Layers,
  FileText,
  Scale,
  AlertCircle,
  Square
} from 'lucide-react';
import { UserProfile, ChatMessage, ViewMode } from '../types';

interface Props {
  profile: UserProfile;
  onProfileUpdate: (newProfile: UserProfile) => void;
  onRequestMatchSchemes: () => void;
  activeLanguage?: string;
  voiceEnabled?: boolean;
  onSwitchView?: (view: ViewMode) => void;
}

const GREETINGS_BY_LANG: Record<string, string> = {
  en: "Namaste! I am Adhikar, your civic and legal empowerment assistant. Tell me about yourself (your state, occupation, age, or income) to find government welfare schemes you are eligible for, or describe any tenancy, consumer, or RTI dispute.",
  bn: "নমস্কার! আমি অধিকার, আপনার নাগরিক ও আইনি ক্ষমতায়ন সহকারী। আপনি কোন রাজ্যের বাসিন্দা, আপনার পেশা, বয়স বা পরিবারের আয় জানান—আমি আপনার উপযুক্ত সরকারি প্রকল্প ও স্কলারশিপ খুঁজে দেব, অথবা যেকোনো আইনি ও আরটিআই বিরোধের সমাধান দেব।",
  hi: "नमस्ते! मैं अधिकार हूँ, आपका नागरिक और कानूनी सशक्तिकरण सहायक। मुझे अपने बारे में बताएं (आपका राज्य, पेशा, आयु या आय) ताकि मैं आपके लिए उपयुक्त सरकारी योजनाएं खोज सकूँ, या किसी भी कानूनी या आरटीआई विवाद का समाधान प्राप्त करें।",
  mr: "नमस्कार! मी अधिकार आहे, आपला नागरी आणि कायदेशीर सक्षमीकरण सहाय्यक. मला आपल्याबद्दल सांगा (आपले राज्य, व्यवसाय, वय किंवा उत्पन्न) जेणेकरून मी आपल्यासाठी शासकीय योजना शोधू शकेन.",
  ta: "வணக்கம்! நான் அதிகார், உங்கள் குடிமை மற்றும் சட்ட அதிகாரமளித்தல் உதவியாளர். உங்களுக்கான அரசு நலத்திட்டங்களை அறிய உங்கள் விவரங்களைப் பகிரவும்.",
  te: "నమస్కారం! నేను అధికార్, మీ పౌర మరియు చట్టపరమైన సాధికారత సహాయకుడిని. ప్రభుత్వ సంక్షేమ పథకాలను కనుగొనడానికి మీ వివరాలను తెలియజేయండి.",
  kn: "ನಮಸ್ಕಾರ! ನಾನು ಅಧಿಕಾರ್, ನಿಮ್ಮ ನಾಗರಿಕ ಮತ್ತು ಕಾನೂನು ಸಬಲೀಕರಣ ಸಹಾಯಕ. ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಹುಡುಕಲು ನಿಮ್ಮ ವಿವರಗಳನ್ನು ಹಂಚಿಕೊಳ್ಳಿ.",
  gu: "નમસ્તે! હું અધિકાર છું, તમારો નાગરિક અને કાનૂની સશક્તિકરણ સહાયક. સરકારી કલ્યાણ યોજનાઓ શોધવા માટે તમારી વિગતો જણાવો.",
  pa: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਅਧਿਕਾਰ ਹਾਂ, ਤੁਹਾਡਾ ਨਾਗਰਿਕ ਅਤੇ ਕਾਨੂੰਨੀ ਸਹਾਇਕ। ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਲੱਭਣ ਲਈ ਆਪਣੇ ਵੇਰਵੇ ਸਾਂਝੇ ਕਰੋ।"
};

const QUICK_STARTERS_BY_LANG: Record<string, string[]> = {
  bn: [
    "আমি একজন ২১ বছর বয়সী ছাত্র, পশ্চিমবঙ্গে থাকি, স্টুডেন্ট ক্রেডিট কার্ড ও স্কলারশিপ চাই",
    "আমি আসামের একজন ৪৮ বছর বয়সী কৃষক, পরিবারের বার্ষিক আয় ২.৫ লাখ টাকা",
    "আমি দিল্লির একজন ৩২ বছর বয়সী হকার বা ছোট ব্যবসায়ী, পারিবারিক আয় ৮০,০০০ টাকা",
    "ব্যাঙ্গালোরে আমার বাড়িওয়ালা সিকিউরিটি ডিপোজিট ফেরত দিতে অস্বীকার করছে"
  ],
  hi: [
    "मैं महाराष्ट्र में रहने वाला 48 वर्षीय किसान हूँ, वार्षिक आय 2.5 लाख है",
    "मैं असम की एक छात्रा हूँ, छात्रवृत्ति और योजनाओं की जानकारी चाहिए",
    "मैं दिल्ली में 32 वर्षीय स्ट्रीट वेंडर हूँ, पारिवारिक आय 80,000 है",
    "मेरे मकान मालिक ने मेरा सिक्योरिटी डिपॉजिट वापस करने से मना कर दिया है"
  ],
  mr: [
    "मी महाराष्ट्रातील ४८ वर्षीय शेतकरी आहे, वार्षिक उत्पन्न २.৫ लाख आहे",
    "मी आसाममधील विद्यार्थिनी आहे, शिष्यवृत्ती योजना हवी आहे",
    "मी दिल्लीतील ३२ वर्षीय विक्रेता आहे, कौटुंबिक उत्पन्न ८०,००० आहे",
    "माझ्या घरमालकाने माझी अनामत रक्कम परत करण्यास नकार दिला आहे"
  ],
  ta: [
    "நான் மகாராஷ்டிராவில் வசிக்கும் 48 வயது விவசாயி, ஆண்டு வருமானம் 2.5 லட்சம்",
    "நான் அசாமில் உள்ள ஒரு மாணவி, உதவித்தொகை திட்டங்கள் தேவை",
    "தில்லியில் உள்ள 32 வயது சாலையோர வியாபாரி, குடும்ப வருமானம் 80,000"
  ],
  te: [
    "నేను మహారాష్ట్రలో నివసిస్తున్న 48 ఏళ్ల రైతును, వార్షిక ఆదాయం 2.5 లక్షలు",
    "నేను అస్సాంలోని విద్యార్థిని, స్కాలర్‌షిప్ పథకాలు కావాలి"
  ],
  en: [
    "I am a 48-year-old farmer living in Maharashtra with annual income 2.5 lakh",
    "I am a female college student in Assam from SC category seeking scholarship",
    "I am a 32-year-old street vendor in Delhi with family income 80000",
    "My landlord in Bangalore is refusing to return my security deposit"
  ]
};

const SLOT_LABELS: Record<string, Record<string, string>> = {
  en: { state: 'State / UT', occupation: 'Occupation', age: 'Age', income: 'Annual Income', category: 'Category' },
  bn: { state: 'রাজ্য / ইউটি', occupation: 'পেশা', age: 'বয়স', income: 'বার্ষিক আয়', category: 'সামাজিক শ্রেণী' },
  hi: { state: 'राज्य / UT', occupation: 'व्यवसाय', age: 'आयु', income: 'वार्षिक आय', category: 'श्रेणी' },
  mr: { state: 'राज्य', occupation: 'व्यवसाय', age: 'वय', income: 'वार्षिक उत्पन्न', category: 'प्रवर्ग' },
  ta: { state: 'மாநிலம்', occupation: 'தொழில்', age: 'வயது', income: 'வருமானம்', category: 'பிரிவு' },
  te: { state: 'రాష్ట్రం', occupation: 'వృత్తి', age: 'వయస్సు', income: 'ఆదాయం', category: 'వర్గం' }
};

export const ChatAssistant: React.FC<Props> = ({
  profile,
  onProfileUpdate,
  onRequestMatchSchemes,
  activeLanguage = 'en',
  voiceEnabled = true,
  onSwitchView
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'assistant',
      text: GREETINGS_BY_LANG[activeLanguage] || GREETINGS_BY_LANG.en,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isTranscribingAudio, setIsTranscribingAudio] = useState(false);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);
  const [micError, setMicError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // Dynamically update greeting if conversation has not yet started
  useEffect(() => {
    setMessages(prev => {
      if (prev.length === 1 && prev[0].sender === 'assistant') {
        return [{
          ...prev[0],
          text: GREETINGS_BY_LANG[activeLanguage] || GREETINGS_BY_LANG.en
        }];
      }
      return prev;
    });
  }, [activeLanguage]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Pre-load available browser voices
  useEffect(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
  }, []);

  const getLanguageTag = (lang: string) => {
    const map: Record<string, string> = {
      en: 'en-IN',
      hi: 'hi-IN',
      mr: 'mr-IN',
      ta: 'ta-IN',
      te: 'te-IN',
      bn: 'bn-IN',
      kn: 'kn-IN',
      gu: 'gu-IN',
      pa: 'pa-IN'
    };
    return map[lang] || 'en-IN';
  };

  const getLanguageName = (lang: string) => {
    const map: Record<string, string> = {
      en: 'English',
      hi: 'हिन्दी (Hindi)',
      mr: 'मराठी (Marathi)',
      ta: 'தமிழ் (Tamil)',
      te: 'తెలుగు (Telugu)',
      bn: 'বাংলা (Bengali)',
      kn: 'ಕನ್ನಡ (Kannada)',
      gu: 'ગુજરાતી (Gujarati)',
      pa: 'ਪੰਜਾਬੀ (Punjabi)'
    };
    return map[lang] || 'English';
  };

  // High-Fidelity Regional Speech Audio Playback
  const speakText = async (text: string, msgId?: string, force = false) => {
    if (!voiceEnabled && !force) return;

    stopSpeaking();
    if (msgId) setSpeakingMsgId(msgId);

    try {
      // Direct high-fidelity regional audio stream from backend
      const audioUrl = `/api/voice/tts?text=${encodeURIComponent(text)}&language=${activeLanguage}`;
      const audio = new Audio(audioUrl);
      audioPlayerRef.current = audio;

      audio.onended = () => {
        setSpeakingMsgId(null);
      };

      audio.onerror = () => {
        if ('speechSynthesis' in window) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = getLanguageTag(activeLanguage);
          utterance.onend = () => setSpeakingMsgId(null);
          utterance.onerror = () => setSpeakingMsgId(null);
          window.speechSynthesis.speak(utterance);
        } else {
          setSpeakingMsgId(null);
        }
      };

      await audio.play();
    } catch (err) {
      console.warn("Audio element playback note:", err);
      if ('speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = getLanguageTag(activeLanguage);
          utterance.onend = () => setSpeakingMsgId(null);
          utterance.onerror = () => setSpeakingMsgId(null);
          window.speechSynthesis.speak(utterance);
        } catch (e) {
          setSpeakingMsgId(null);
        }
      } else {
        setSpeakingMsgId(null);
      }
    }
  };

  const stopSpeaking = () => {
    if (audioPlayerRef.current) {
      try {
        audioPlayerRef.current.pause();
        audioPlayerRef.current.currentTime = 0;
      } catch (e) {}
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setSpeakingMsgId(null);
  };

  // Voice Input: Dual-Mode Speech-to-Text
  const startMediaRecorderFallback = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (audioBlob.size > 0) {
          setIsTranscribingAudio(true);
          try {
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = async () => {
              const base64Audio = (reader.result as string).split(',')[1];
              const res = await fetch('/api/voice/transcribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  audio_base64: base64Audio,
                  mime_type: 'audio/webm',
                  language: activeLanguage
                })
              });
              if (res.ok) {
                const data = await res.json();
                if (data.transcribed_text) {
                  setInputText(data.transcribed_text);
                }
              }
              setIsTranscribingAudio(false);
            };
          } catch (err) {
            console.error('Audio upload error:', err);
            setIsTranscribingAudio(false);
          }
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsListening(true);
    } catch (err: any) {
      console.error('Microphone error:', err);
      setIsListening(false);
      setMicError("Microphone access is blocked. Please allow microphone permissions in your browser address bar.");
    }
  };

  const toggleSpeechRecognition = () => {
    setMicError(null);

    if (isListening) {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        try { mediaRecorderRef.current.stop(); } catch (e) {}
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = getLanguageTag(activeLanguage);

        recognition.onstart = () => {
          setIsListening(true);
          setMicError(null);
        };

        recognition.onresult = (event: any) => {
          let interimTranscript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            } else {
              interimTranscript += event.results[i][0].transcript;
            }
          }

          const fullText = finalTranscript || interimTranscript;
          if (fullText) {
            setInputText(fullText);
          }
        };

        recognition.onerror = (event: any) => {
          console.warn("Speech recognition note:", event.error);
          setIsListening(false);
          if (event.error === 'not-allowed') {
            setMicError("Microphone access was denied. Please allow microphone permissions in your browser.");
          } else if (event.error !== 'no-speech') {
            startMediaRecorderFallback();
          }
        };

        recognition.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current = recognition;
        recognition.start();
      } catch (e) {
        console.warn('SpeechRecognition failed, falling back to MediaRecorder:', e);
        startMediaRecorderFallback();
      }
    } else {
      startMediaRecorderFallback();
    }
  };

  // Submit Turn to Backend API with Gemini Native Multilingual Processing (ADR-011)
  const handleSendMessage = async (textToSend?: string) => {
    const rawText = textToSend || inputText;
    if (!rawText.trim() || isLoading) return;

    stopSpeaking();

    // Add user message to UI
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: rawText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);
    setMicError(null);

    try {
      // Direct Native Gemini Turn (ADR-011)
      const response = await fetch('/api/profile/turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_utterance: rawText,
          current_profile: profile,
          required_slots: ['state', 'occupation', 'age', 'income', 'category'],
          language: activeLanguage
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        onProfileUpdate(data.profile);

        let replyText = data.next_question || "Thank you! I have updated your profile with the details provided.";
        if (data.is_complete && !data.next_question) {
          replyText += " All required eligibility criteria are collected. Matching schemes for you right now!";
        }

        if (data.is_complete) {
          onRequestMatchSchemes();
        }

        const newMsgId = (Date.now() + 1).toString();
        const botMsg: ChatMessage = {
          id: newMsgId,
          sender: 'assistant',
          text: replyText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          status: data.status
        };
        setMessages(prev => [...prev, botMsg]);

        // Trigger Audio Readout if enabled
        speakText(replyText, newMsgId);
      } else {
        throw new Error(`Server returned ${response.status}`);
      }
    } catch (err) {
      console.error('Turn processing error:', err);
      const errMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: activeLanguage === 'bn' 
          ? "সাময়িক সংযোগ সমস্যা দেখা দিয়েছে। দয়া করে আবার চেষ্টা করুন।" 
          : activeLanguage === 'hi'
          ? "अस्थायी कनेक्शन समस्या हुई। कृपया पुनः प्रयास करें।"
          : "I encountered a temporary connection issue. Please check your network and try again.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const slotLabels = SLOT_LABELS[activeLanguage] || SLOT_LABELS.en;
  const quickStarters = QUICK_STARTERS_BY_LANG[activeLanguage] || QUICK_STARTERS_BY_LANG.en;

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border-r border-slate-800/80">
      {/* Top Profile Summary Bar */}
      <div className="p-3.5 border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            {activeLanguage === 'bn' ? 'যাচাইকৃত প্রোফাইল স্লট' : activeLanguage === 'hi' ? 'सत्यापित प्रोफ़ाइल स्लॉट' : 'Verified Profile Slots (ADR-004)'}
          </span>
          <button
            onClick={() => onRequestMatchSchemes()}
            className="text-[11px] font-semibold text-sky-400 hover:text-sky-300 transition-colors flex items-center gap-1"
          >
            <span>{activeLanguage === 'bn' ? 'স্কিম রিফ্রেশ' : activeLanguage === 'hi' ? 'योजनाएं ताज़ा करें' : 'Refresh Matches'}</span>
          </button>
        </div>

        {/* Dynamic Slot Pills */}
        <div className="flex flex-wrap gap-1.5">
          {Object.keys(slotLabels).map((slotKey) => {
            const val = profile[slotKey as keyof UserProfile];
            const isFilled = val !== undefined && val !== null && val !== '';
            let displayVal = val;
            if (slotKey === 'income' && typeof val === 'number') {
              displayVal = `₹${val.toLocaleString('en-IN')}`;
            }

            return (
              <span
                key={slotKey}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                  isFilled
                    ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 shadow-sm'
                    : 'bg-slate-850/60 text-slate-400 border-slate-700/50'
                }`}
              >
                {isFilled ? (
                  <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                ) : (
                  <HelpCircle className="w-3 h-3 text-slate-500 shrink-0" />
                )}
                <span>{slotLabels[slotKey]}:</span>
                <span className={isFilled ? 'text-slate-100' : 'italic text-slate-500'}>
                  {isFilled ? String(displayVal) : (activeLanguage === 'bn' ? 'অনুপস্থিত' : activeLanguage === 'hi' ? 'अनुपलब्ध' : 'Missing')}
                </span>
              </span>
            );
          })}
        </div>
      </div>

      {/* Message History Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => {
          const isSpeaking = speakingMsgId === msg.id;

          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${
                msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 text-xs shadow-md ${
                  msg.sender === 'user'
                    ? 'bg-sky-600 text-white'
                    : 'bg-gradient-to-tr from-sky-500 to-indigo-600 text-white'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className="space-y-1 max-w-[82%]">
                <div
                  className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-sky-600 text-white rounded-tr-sm shadow-md'
                      : msg.status === 'AMBIGUOUS_STATE'
                      ? 'bg-amber-950/40 text-amber-200 border border-amber-800/60 rounded-tl-sm'
                      : 'bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-tl-sm shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                </div>
                <div className={`flex items-center gap-2 text-[10px] text-slate-500 px-1 ${
                  msg.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}>
                  <span>{msg.timestamp}</span>
                  {msg.sender === 'assistant' && (
                    <button
                      onClick={() => isSpeaking ? stopSpeaking() : speakText(msg.text, msg.id, true)}
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md transition-all ${
                        isSpeaking 
                          ? 'bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/50 shadow-sm' 
                          : 'hover:text-sky-300 hover:bg-slate-800 text-slate-400 border border-slate-700/50'
                      }`}
                      title={isSpeaking ? "Stop Speaking" : "Listen aloud in native voice"}
                    >
                      {isSpeaking ? (
                        <>
                          <VolumeX className="w-3 h-3 text-emerald-400 animate-pulse" />
                          <span className="text-[10px] text-emerald-300 font-medium">Playing...</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3 h-3 text-sky-400" />
                          <span className="text-[10px]">
                            {activeLanguage === 'bn' ? '🔊 শুনুন' : activeLanguage === 'hi' ? '🔊 सुनें' : '🔊 Listen'}
                          </span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400">
              <Bot className="w-4 h-4 animate-pulse" />
            </div>
            <div className="p-3 rounded-2xl bg-slate-800/80 border border-slate-700 text-xs text-slate-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-sky-400 animate-ping"></div>
              <span>
                {activeLanguage === 'bn' 
                  ? 'উত্তর তৈরি ও সরকারি তথ্যের যাচাই চলছে...' 
                  : activeLanguage === 'hi'
                  ? 'उत्तर तैयार और सरकारी जानकारी का सत्यापन हो रहा है...'
                  : 'Processing turn & verifying statutory grounding...'}
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Cross-Module In-Chat Shortcut Switcher */}
      {onSwitchView && (
        <div className="px-4 py-2 border-t border-slate-800/60 bg-slate-950/40 flex items-center gap-1.5 overflow-x-auto text-[11px]">
          <span className="text-slate-500 font-semibold text-[10px] uppercase shrink-0">
            {activeLanguage === 'bn' ? 'ভিউ পরিবর্তন:' : activeLanguage === 'hi' ? 'दृश्य बदलें:' : 'Switch View:'}
          </span>
          <button
            onClick={() => onSwitchView('schemes')}
            className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-sky-300 border border-slate-800 flex items-center gap-1 shrink-0"
          >
            <Layers className="w-3 h-3 text-sky-400" />
            {activeLanguage === 'bn' ? 'যোগ্য প্রকল্প' : activeLanguage === 'hi' ? 'योग्य योजनाएं' : 'Matched Schemes'}
          </button>
          <button
            onClick={() => onSwitchView('rights')}
            className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-indigo-300 border border-slate-800 flex items-center gap-1 shrink-0"
          >
            <Scale className="w-3 h-3 text-indigo-400" />
            {activeLanguage === 'bn' ? 'আপনার অধিকার' : activeLanguage === 'hi' ? 'आपके अधिकार' : 'Your Rights'}
          </button>
          <button
            onClick={() => onSwitchView('rti')}
            className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-emerald-300 border border-slate-800 flex items-center gap-1 shrink-0"
          >
            <FileText className="w-3 h-3 text-emerald-400" />
            {activeLanguage === 'bn' ? 'RTI ড্রাফট' : activeLanguage === 'hi' ? 'RTI ड्राफ्ट' : 'Draft RTI'}
          </button>
        </div>
      )}

      {/* Quick Prompts Carousel */}
      <div className="px-4 py-2 border-t border-slate-800/60 bg-slate-950/30 overflow-x-auto flex gap-2">
        {quickStarters.map((starter, index) => (
          <button
            key={index}
            onClick={() => handleSendMessage(starter)}
            className="shrink-0 text-[11px] px-2.5 py-1 rounded-full bg-slate-800/70 hover:bg-slate-750 text-slate-300 hover:text-sky-300 border border-slate-700/60 transition-colors"
          >
            {starter.substring(0, 52)}...
          </button>
        ))}
      </div>

      {/* Active Mic Listening / Audio Transcribing Banner */}
      {isListening && (
        <div className="px-4 py-2 bg-rose-950/70 border-t border-rose-800/80 flex items-center justify-between text-rose-200 text-xs animate-pulse">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
            <span className="font-bold">
              🎙️ Listening in {getLanguageName(activeLanguage)}... Speak into your microphone now!
            </span>
          </div>
          <button
            onClick={toggleSpeechRecognition}
            className="px-2 py-0.5 rounded bg-rose-900/80 hover:bg-rose-800 text-rose-100 text-[10px] font-bold flex items-center gap-1 border border-rose-700"
          >
            <Square className="w-3 h-3 fill-current" />
            {activeLanguage === 'bn' ? 'বলা শেষ' : activeLanguage === 'hi' ? 'समाप्त' : 'Done Speaking'}
          </button>
        </div>
      )}

      {isTranscribingAudio && (
        <div className="px-4 py-1.5 bg-indigo-950/60 border-t border-indigo-800/70 flex items-center gap-2 text-indigo-300 text-xs animate-pulse">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
          <span>Transcribing your speech in {getLanguageName(activeLanguage)}...</span>
        </div>
      )}

      {micError && (
        <div className="px-4 py-2 bg-amber-950/60 border-t border-amber-800/60 flex items-center gap-2 text-amber-200 text-xs">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span className="flex-1">{micError}</span>
          <button onClick={() => setMicError(null)} className="text-[10px] text-amber-400 hover:text-amber-200 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Input Box with Voice Mic Button */}
      <div className="p-3.5 border-t border-slate-800 bg-slate-950/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={
              isListening 
                ? `Listening in ${getLanguageName(activeLanguage)}... Speak now!` 
                : activeLanguage === 'bn'
                ? "বাংলায় আপনার প্রশ্ন বা বিবরণ লিখুন বা বলুন (যেমন: 'আমি পশ্চিমবঙ্গে থাকি, স্টুডেন্ট ক্রেডিট কার্ড চাই')..."
                : activeLanguage === 'hi' 
                ? "अपनी भाषा में बोलें या लिखें (जैसे: 'मैं असम में 45 वर्ष का किसान हूँ')..." 
                : "Type your details or civic grievance (e.g. 'I am 45yr farmer in Assam')..."
            }
            className={`flex-1 px-4 py-2.5 text-xs rounded-xl bg-slate-900 border text-slate-100 placeholder-slate-500 focus:outline-none transition-all shadow-inner ${
              isListening ? 'border-rose-500 ring-2 ring-rose-500/40 bg-slate-900/90' : 'border-slate-800 focus:border-sky-500'
            }`}
          />

          {/* Microphone Speech Recognition Button */}
          <button
            type="button"
            onClick={toggleSpeechRecognition}
            className={`p-2.5 rounded-xl border transition-all flex items-center justify-center shrink-0 cursor-pointer ${
              isListening
                ? 'bg-rose-600 text-white border-rose-500 shadow-lg shadow-rose-900/50 animate-bounce'
                : 'bg-slate-900 hover:bg-slate-850 text-sky-400 hover:text-sky-300 border-slate-700/80 shadow-sm'
            }`}
            title={isListening ? "Click to Stop Speaking" : "Click to Speak via Microphone"}
          >
            {isListening ? (
              <Square className="w-4 h-4 text-white fill-current" />
            ) : (
              <Mic className="w-4 h-4 text-sky-400" />
            )}
          </button>

          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="p-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white transition-all shadow-lg shadow-sky-900/30 flex items-center justify-center shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
