import React, { useState } from 'react';
import Map from './components/Map';
import LayerControl from './components/LayerControl';
import { sendChatMessage } from './services/api';
import { Send, Bot, User } from 'lucide-react';

function App() {
  const [activeLayers, setActiveLayers] = useState(['competitors']);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const toggleLayer = (layer) => {
    setActiveLayers(prev =>
      prev.includes(layer)
        ? prev.filter(l => l !== layer)
        : [...prev, layer]
    );
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = chatInput;
    setChatInput("");
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setIsLoading(true);

    const response = await sendChatMessage(userMsg);

    setIsLoading(false);
    setChatHistory(prev => [...prev, { role: 'ai', text: response.text }]);

    // Execute Actions
    if (response.actions) {
      response.actions.forEach(action => {
        if (action.type === 'setLayer') {
          // If layer is not active, add it.
          // If the user wants to "switch" to it, maybe we should clear others?
          // For now, let's just ensure it's active.
          setActiveLayers(prev => {
            if (!prev.includes(action.layer)) {
              return [...prev, action.layer];
            }
            return prev;
          });
        }
      });
    }
  };

  return (
    <div className="h-screen w-screen relative overflow-hidden bg-gray-900">
      {/* Header / Overlay */}
      <div className="absolute top-0 left-0 w-full p-4 pointer-events-none z-[1000] flex justify-center">
        <div className="bg-black/80 backdrop-blur-md text-white px-6 py-2 rounded-full shadow-2xl border border-white/10 pointer-events-auto">
          <h1 className="font-bold text-lg tracking-wide">ATLAS <span className="text-blue-400 font-light">AI</span></h1>
        </div>
      </div>

      <LayerControl activeLayers={activeLayers} toggleLayer={toggleLayer} />

      <Map activeLayers={activeLayers} />

      {/* Chat Interface */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-[1000] flex flex-col gap-2">

        {/* Chat History (Only show last few messages) */}
        {chatHistory.length > 0 && (
          <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-gray-200 p-4 max-h-60 overflow-y-auto mb-2">
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={`flex gap-2 mb-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`p-2 rounded-lg text-sm max-w-[80%] ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                  {msg.text}
                </div>
              </div>
            ))}
            {isLoading && <div className="text-xs text-gray-500 italic">Atlas is thinking...</div>}
          </div>
        )}

        <form onSubmit={handleChatSubmit} className="bg-white/90 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200 p-2 flex gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask Atlas: 'Show me high foot traffic areas...'"
            className="flex-1 bg-transparent border-none outline-none px-4 py-3 text-gray-800 placeholder-gray-500"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-6 py-2 rounded-xl font-medium transition-colors flex items-center justify-center"
          >
            {isLoading ? <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" /> : <Send size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
