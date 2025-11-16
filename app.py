import React, { useState, useEffect, useRef } from 'react';
import { Send, Menu, X, Plus, Zap, Crown, LogOut, Sparkles, MessageSquare } from 'lucide-react';

export default function NexusAI() {
  const [currentView, setCurrentView] = useState('landing');
  const [authMode, setAuthMode] = useState('login');
  const [selectedPlan, setSelectedPlan] = useState('');
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [dailyCount, setDailyCount] = useState(0);
  const chatEndRef = useRef(null);

  const MESSAGE_LIMITS = {
    guest: 5,
    free: 20,
    premium: Infinity
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handlePlanSelect = (plan) => {
    setSelectedPlan(plan);
    setCurrentView('auth');
  };

  const handleAuth = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const username = formData.get('username');
    const isPremium = selectedPlan === 'premium';
    
    setUser({
      username: username || 'Guest',
      type: selectedPlan || 'guest',
      isPremium: isPremium,
      isGuest: !username
    });
    setDailyCount(0);
    setCurrentView('chat');
    
    setTimeout(() => {
      addMessage('bot', `Ciao ${username || 'Guest'}! 👋 Sono NEXUS AI, il bot più intelligente al mondo! Come posso aiutarti oggi?`);
    }, 500);
  };

  const handleGuestMode = () => {
    setUser({
      username: 'Guest',
      type: 'guest',
      isPremium: false,
      isGuest: true
    });
    setSelectedPlan('guest');
    setDailyCount(0);
    setCurrentView('chat');
    
    setTimeout(() => {
      addMessage('bot', 'Benvenuto in modalità Ospite! 👋 Hai 5 messaggi disponibili. Registrati per ottenere 20 messaggi al giorno!');
    }, 500);
  };

  const addMessage = (role, content) => {
    setMessages(prev => [...prev, { role, content, timestamp: Date.now() }]);
  };

  const sendMessage = (e) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || isTyping) return;

    const userType = user?.type || 'guest';
    const limit = MESSAGE_LIMITS[userType];

    if (dailyCount >= limit) {
      addMessage('bot', `⚠️ Hai raggiunto il limite di ${limit} messaggi! ${userType === 'guest' ? 'Registrati per ottenere 20 messaggi!' : 'Passa a Premium per messaggi illimitati!'}`);
      return;
    }

    const userMessage = inputValue;
    setInputValue('');
    addMessage('user', userMessage);
    setIsTyping(true);
    setDailyCount(prev => prev + 1);

    setTimeout(() => {
      const response = generateSmartResponse(userMessage);
      addMessage('bot', response);
      setIsTyping(false);
    }, 1000 + Math.random() * 1000);
  };

  const generateSmartResponse = (input) => {
    const lower = input.toLowerCase();
    
    const isItalian = /[àèéìòù]|che|sono|come|cosa|dove|quando/.test(lower);
    
    if (lower.includes('ciao') || lower.includes('hello') || lower.includes('hola')) {
      if (isItalian) return '👋 Ciao! Come posso aiutarti oggi?';
      return '👋 Hello! How can I help you today?';
    }

    if (lower.includes('chi sei') || lower.includes('who are you')) {
      if (isItalian) return '🤖 Sono NEXUS AI, il bot più intelligente al mondo! Combino ChatGPT, Claude e Gemini. Posso aiutarti in qualsiasi lingua!';
      return '🤖 I am NEXUS AI, the smartest bot in the world! I combine ChatGPT, Claude and Gemini. I can help you in any language!';
    }

    if (lower.includes('grazie') || lower.includes('thank')) {
      if (isItalian) return '😊 Prego! Sono sempre qui per aiutarti!';
      return '😊 You are welcome! I am always here to help!';
    }

    if (lower.includes('cod') || lower.includes('programm')) {
      if (isItalian) return '💻 Certo! Posso aiutarti con Python, JavaScript, HTML, CSS, React e molto altro. Cosa vuoi creare?';
      return '💻 Sure! I can help with Python, JavaScript, HTML, CSS, React and more. What do you want to create?';
    }

    if (lower.includes('help') || lower.includes('aiut')) {
      if (isItalian) return '🎯 Posso aiutarti con:\n\n✨ Programmazione\n📚 Ricerca\n🎨 Creatività\n🧮 Matematica\n🌍 Traduzioni\n\nCosa ti serve?';
      return '🎯 I can help with:\n\n✨ Programming\n📚 Research\n🎨 Creativity\n🧮 Math\n🌍 Translations\n\nWhat do you need?';
    }

    if (isItalian) {
      return `🤔 Interessante! Riguardo a "${input.slice(0, 40)}..." posso dirti che è un argomento affascinante. Puoi darmi più dettagli?`;
    }
    return `🤔 Interesting! About "${input.slice(0, 40)}..." I can tell you it's a fascinating topic. Can you give me more details?`;
  };

  const newChat = () => {
    if (messages.length > 0 && confirm('Iniziare una nuova chat?')) {
      setMessages([]);
      setDailyCount(0);
    }
  };

  if (currentView === 'landing') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
        <div className="max-w-6xl w-full">
          <div className="text-center mb-16">
            <h1 className="text-7xl font-black text-white mb-4">
              NEXUS <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">AI</span>
            </h1>
            <p className="text-2xl text-blue-200 mb-4">Il Bot Più Intelligente Al Mondo</p>
            <p className="text-lg text-blue-300 max-w-2xl mx-auto">Combina ChatGPT, Claude e Gemini. Risponde in tutte le lingue.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 mb-12">
            <div 
              onClick={() => handlePlanSelect('free')}
              className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border-2 border-white/20 hover:border-blue-400 transition-all cursor-pointer hover:scale-105"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-cyan-500 rounded-xl flex items-center justify-center">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white">Free Plan</h3>
                  <p className="text-blue-300">Inizia Gratis</p>
                </div>
              </div>
              
              <div className="space-y-3 mb-8">
                <p className="text-blue-100">✓ 20 messaggi al giorno</p>
                <p className="text-blue-100">✓ Risposte intelligenti</p>
                <p className="text-blue-100">✓ Tutte le lingue</p>
                <p className="text-blue-100">✓ Storico conversazioni</p>
              </div>

              <button className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-bold py-4 rounded-xl">
                Inizia Gratis →
              </button>
            </div>

            <div 
              onClick={() => handlePlanSelect('premium')}
              className="bg-gradient-to-br from-yellow-500/20 to-orange-500/20 backdrop-blur-xl rounded-3xl p-8 border-2 border-yellow-400 transition-all cursor-pointer hover:scale-105 relative"
            >
              <div className="absolute top-4 right-4 bg-yellow-400 text-purple-900 px-3 py-1 rounded-full text-sm font-bold">
                BEST VALUE
              </div>
              
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl flex items-center justify-center">
                  <Crown className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white">Premium</h3>
                  <p className="text-yellow-300">Potenza Illimitata</p>
                </div>
              </div>
              
              <div className="space-y-3 mb-8">
                <p className="text-white font-semibold">✓ Messaggi illimitati</p>
                <p className="text-white font-semibold">✓ Risposte prioritarie</p>
                <p className="text-white font-semibold">✓ Modelli AI avanzati</p>
                <p className="text-white font-semibold">✓ Supporto prioritario</p>
                <p className="text-white font-semibold">✓ Funzioni esclusive</p>
              </div>

              <button className="w-full bg-gradient-to-r from-yellow-400 to-orange-500 text-purple-900 font-bold py-4 rounded-xl">
                Diventa Premium →
              </button>
            </div>
          </div>

          <div className="text-center">
            <button 
              onClick={handleGuestMode}
              className="text-blue-300 hover:text-white transition-colors text-lg font-medium underline"
            >
              Continua come Ospite (5 messaggi)
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (currentView === 'auth') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 max-w-md w-full border-2 border-white/20">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">
              {authMode === 'login' ? 'Bentornato!' : 'Crea Account'}
            </h2>
            <p className="text-blue-300">
              Piano: <span className="font-bold text-white">{selectedPlan === 'premium' ? 'Premium' : 'Free'}</span>
            </p>
          </div>

          <form onSubmit={handleAuth} className="space-y-6">
            <div>
              <label className="block text-blue-200 mb-2">Username</label>
              <input
                type="text"
                name="username"
                required
                className="w-full px-4 py-3 bg-white/10 border-2 border-white/20 rounded-xl text-white placeholder-blue-300 focus:outline-none focus:border-blue-400"
                placeholder="Scegli username"
              />
            </div>

            <div>
              <label className="block text-blue-200 mb-2">Password</label>
              <input
                type="password"
                name="password"
                required
                className="w-full px-4 py-3 bg-white/10 border-2 border-white/20 rounded-xl text-white placeholder-blue-300 focus:outline-none focus:border-blue-400"
                placeholder="Password"
              />
            </div>

            {authMode === 'register' && (
              <div>
                <label className="block text-blue-200 mb-2">Email</label>
                <input
                  type="email"
                  name="email"
                  required
                  className="w-full px-4 py-3 bg-white/10 border-2 border-white/20 rounded-xl text-white placeholder-blue-300 focus:outline-none focus:border-blue-400"
                  placeholder="Email"
                />
              </div>
            )}

            <button type="submit" className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-bold py-4 rounded-xl">
              {authMode === 'login' ? 'Accedi' : 'Registrati'}
            </button>
          </form>

          <div className="mt-6 text-center space-y-3">
            <button onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')} className="text-blue-300 hover:text-white">
              {authMode === 'login' ? 'Registrati' : 'Hai un account? Accedi'}
            </button>
            <div>
              <button onClick={handleGuestMode} className="text-blue-400 hover:text-white underline">
                Continua come Ospite
              </button>
            </div>
            <div>
              <button onClick={() => setCurrentView('landing')} className="text-blue-300 hover:text-white text-sm">
                ← Torna indietro
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-900 flex overflow-hidden">
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 fixed md:relative z-50 w-64 bg-gray-950 h-full flex flex-col transition-transform`}>
        <div className="p-4 border-b border-gray-800">
          <button onClick={newChat} className="w-full flex items-center gap-2 px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-xl text-white">
            <Plus className="w-5 h-5" />
            <span>Nuova Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <button className="w-full text-left px-4 py-3 text-gray-300 hover:bg-gray-800 rounded-xl flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            <span className="text-sm">Chat corrente</span>
          </button>
        </div>

        <div className="border-t border-gray-800 p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-bold">
              {user?.username?.[0]?.toUpperCase() || 'G'}
            </div>
            <div className="flex-1">
              <div className="text-white font-medium">{user?.username}</div>
              <div className="text-sm text-gray-400">
                {user?.isPremium ? (
                  <span className="flex items-center gap-1">
                    <Crown className="w-3 h-3 text-yellow-400" />
                    Premium
                  </span>
                ) : (
                  `${user?.type === 'guest' ? 'Ospite' : 'Free'} • ${dailyCount}/${MESSAGE_LIMITS[user?.type || 'guest']}`
                )}
              </div>
            </div>
          </div>

          {!user?.isPremium && (
            <button className="w-full px-4 py-2 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-lg text-sm mb-2 flex items-center justify-center gap-2">
              <Crown className="w-4 h-4" />
              Upgrade
            </button>
          )}

          {!user?.isGuest && (
            <button onClick={() => setCurrentView('landing')} className="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm flex items-center justify-center gap-2">
              <LogOut className="w-4 h-4" />
              Esci
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="md:hidden bg-gray-950 border-b border-gray-800 px-4 py-3 flex items-center justify-between">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="text-white">
            {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
          <span className="text-white font-bold">NEXUS AI</span>
          <button onClick={newChat} className="text-white">
            <Plus className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-3xl flex items-center justify-center mb-6">
                <Sparkles className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-3">Benvenuto in NEXUS AI</h2>
              <p className="text-gray-400 max-w-md">Il bot più intelligente al mondo. Chiedi qualsiasi cosa!</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'bot' && (
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
              )}
              <div className={`max-w-3xl px-4 py-3 rounded-2xl ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-100'}`}>
                <div className="whitespace-pre-wrap break-words">{msg.content}</div>
              </div>
              {msg.role === 'user' && (
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center flex-shrink-0 text-white font-bold">
                  {user?.username?.[0]?.toUpperCase() || 'U'}
                </div>
              )}
            </div>
          ))}

          {isTyping && (
            <div className="flex gap-4 justify-start">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="bg-gray-800 px-4 py-3 rounded-2xl">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="border-t border-gray-800 p-4">
          <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Scrivi un messaggio..."
              className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isTyping}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
