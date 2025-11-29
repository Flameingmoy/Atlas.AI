import React, { useState } from 'react';
import Map from './components/Map';
import LayerControl from './components/LayerControl';
import SearchBar from './components/SearchBar';
import { sendChatMessage, getLocationRecommendations } from './services/api';
import { Send, Bot, User, Database, Table, X, Tag, Layers, MapPin, Sparkles, TrendingUp } from 'lucide-react';

function App() {
  const [activeLayers, setActiveLayers] = useState(['competitors']);
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [mapCenter, setMapCenter] = useState(null);
  const [filteredPOIs, setFilteredPOIs] = useState(null); // For category/super_category filtering
  const [activeFilter, setActiveFilter] = useState(null); // Track current filter
  const [recommendations, setRecommendations] = useState(null); // Business location recommendations

  const toggleLayer = (layer) => {
    setActiveLayers(prev =>
      prev.includes(layer)
        ? prev.filter(l => l !== layer)
        : [...prev, layer]
    );
  };

  // Handle location selection from search
  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
    setMapCenter({ lat: location.lat, lon: location.lon, zoom: 15 });
    // Clear any active filter when navigating to a specific location
    setFilteredPOIs(null);
    setActiveFilter(null);
  };

  // Handle category/super_category selection
  const handleCategorySelect = (filter) => {
    setActiveFilter(filter);
    if (!filter) {
      setFilteredPOIs(null);
    }
  };

  // Handle POIs loaded from category search
  const handlePOIsLoad = (data) => {
    if (data && data.pois) {
      setFilteredPOIs(data.pois);
      // Ensure competitors layer is active to show the filtered POIs
      if (!activeLayers.includes('competitors')) {
        setActiveLayers(prev => [...prev, 'competitors']);
      }
    }
  };

  // Clear filter
  const handleClearFilter = () => {
    setFilteredPOIs(null);
    setActiveFilter(null);
  };

  // Clear recommendations
  const handleClearRecommendations = () => {
    setRecommendations(null);
  };

  // Check if query looks like a business location question
  const isBusinessLocationQuery = (query) => {
    const lowerQuery = query.toLowerCase();
    
    // Direct business location patterns
    const locationPatterns = [
      'open a', 'start a', 'open my', 'start my',
      'where should i open', 'where should i start',
      'best location for', 'best place for', 'best area for',
      'recommend location', 'recommend area', 'recommend place',
      'suitable location', 'suitable area', 'ideal location',
      'want to open', 'want to start', 'planning to open',
      'looking to open', 'looking to start',
      'top areas for', 'top locations for'
    ];
    
    // Business types
    const businessWords = [
      'cafe', 'coffee', 'restaurant', 'food', 'bakery', 'tea',
      'shop', 'store', 'retail', 'boutique', 'mall',
      'gym', 'fitness', 'yoga', 'spa', 'salon', 'wellness',
      'hotel', 'hostel', 'lodge', 'resort',
      'clinic', 'pharmacy', 'hospital', 'medical', 'dental',
      'school', 'coaching', 'tuition', 'training',
      'bank', 'atm', 'insurance',
      'garage', 'mechanic', 'car wash', 'petrol',
      'business', 'venture', 'enterprise'
    ];
    
    // Check for direct patterns
    if (locationPatterns.some(p => lowerQuery.includes(p))) {
      return true;
    }
    
    // Check for business word + location intent
    const locationIntent = ['location', 'area', 'place', 'where', 'recommend', 'best', 'top', 'ideal', 'suitable'];
    const hasBusinessWord = businessWords.some(b => lowerQuery.includes(b));
    const hasLocationIntent = locationIntent.some(l => lowerQuery.includes(l));
    
    return hasBusinessWord && hasLocationIntent;
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = chatInput;
    setChatInput("");
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setIsLoading(true);

    // Check if this is a business location query
    if (isBusinessLocationQuery(userMsg)) {
      try {
        const result = await getLocationRecommendations(userMsg, 1.0);
        
        if (result.success) {
          setRecommendations(result);
          
          // Add AI response with recommendations
          const aiMessage = {
            role: 'ai',
            text: result.message,
            recommendations: result.recommendations
          };
          setChatHistory(prev => [...prev, aiMessage]);
          
          // If we have recommendations, fly to the first one
          if (result.recommendations && result.recommendations.length > 0) {
            const top = result.recommendations[0];
            setMapCenter({ lat: top.centroid.lat, lon: top.centroid.lon, zoom: 12 });
          }
        } else {
          setChatHistory(prev => [...prev, { 
            role: 'ai', 
            text: `Sorry, I couldn't get recommendations: ${result.error || 'Unknown error'}` 
          }]);
        }
      } catch (error) {
        console.error("Recommendation error:", error);
        setChatHistory(prev => [...prev, { 
          role: 'ai', 
          text: "Sorry, I encountered an error while getting recommendations." 
        }]);
      }
      setIsLoading(false);
      return;
    }

    // Regular chat message
    const response = await sendChatMessage(userMsg);

    setIsLoading(false);
    
    // Add AI response with potential database results
    const aiMessage = { 
      role: 'ai', 
      text: response.text,
      databaseResult: null
    };
    
    // Check if there's a database query result in actions
    if (response.actions) {
      const dbAction = response.actions.find(a => a.type === 'databaseQuery');
      if (dbAction && dbAction.result) {
        aiMessage.databaseResult = dbAction.result;
      }
    }
    
    setChatHistory(prev => [...prev, aiMessage]);

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
      {/* Header with Search */}
      <div className="absolute top-0 left-0 w-full p-4 pointer-events-none z-[1000] flex justify-center items-center gap-4">
        <div className="bg-black/80 backdrop-blur-md text-white px-6 py-2 rounded-full shadow-2xl border border-white/10 pointer-events-auto">
          <h1 className="font-bold text-lg tracking-wide">ATLAS <span className="text-blue-400 font-light">AI</span></h1>
        </div>
        <div className="pointer-events-auto">
          <SearchBar 
            onLocationSelect={handleLocationSelect}
            onCategorySelect={handleCategorySelect}
            onPOIsLoad={handlePOIsLoad}
          />
        </div>
      </div>

      {/* Active Filter Indicator */}
      {activeFilter && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-[1000] pointer-events-auto">
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-lg ${
            activeFilter.type === 'category' 
              ? 'bg-purple-600 text-white' 
              : 'bg-orange-600 text-white'
          }`}>
            {activeFilter.type === 'category' ? <Tag size={16} /> : <Layers size={16} />}
            <span className="font-medium">{activeFilter.name}</span>
            <span className="opacity-80">({activeFilter.count?.toLocaleString()} places)</span>
            <button 
              onClick={handleClearFilter}
              className="ml-2 hover:bg-white/20 rounded-full p-1"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      <LayerControl activeLayers={activeLayers} toggleLayer={toggleLayer} />

      <Map 
        activeLayers={activeLayers} 
        selectedLocation={selectedLocation}
        mapCenter={mapCenter}
        filteredPOIs={filteredPOIs}
        recommendations={recommendations}
      />

      {/* Recommendations Panel */}
      {recommendations && recommendations.recommendations && recommendations.recommendations.length > 0 && (
        <div className="absolute top-24 left-4 z-[1000] bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200 p-4 max-w-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="text-amber-500" size={20} />
              <h3 className="font-bold text-gray-800">Top Locations for {recommendations.business_type}</h3>
            </div>
            <button 
              onClick={handleClearRecommendations}
              className="hover:bg-gray-100 rounded-full p-1"
            >
              <X size={18} className="text-gray-500" />
            </button>
          </div>
          
          <div className="text-xs text-gray-500 mb-3 flex items-center gap-1">
            <TrendingUp size={12} />
            <span>{recommendations.super_category}</span>
          </div>
          
          <div className="space-y-3">
            {recommendations.recommendations.slice(0, 3).map((rec, idx) => (
              <div 
                key={rec.area}
                className={`p-3 rounded-xl cursor-pointer transition-all ${
                  idx === 0 ? 'bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300' :
                  idx === 1 ? 'bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200' :
                  'bg-gray-50 border border-gray-100'
                }`}
                onClick={() => {
                  setMapCenter({ lat: rec.centroid.lat, lon: rec.centroid.lon, zoom: 14 });
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    idx === 0 ? 'bg-amber-400 text-white' :
                    idx === 1 ? 'bg-gray-400 text-white' :
                    'bg-gray-300 text-white'
                  }`}>{idx + 1}</span>
                  <span className="font-semibold text-gray-800">{rec.area}</span>
                </div>
                
                <div className="ml-8 space-y-1">
                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-gray-600">
                      <span className="font-medium text-blue-600">{rec.composite_score}</span>/100 Score
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span>📊 {rec.area_score} base</span>
                    <span>🎯 {rec.opportunity_score} opportunity</span>
                    <span>🏪 {rec.ecosystem_score} ecosystem</span>
                  </div>
                  <div className="text-xs text-gray-400">
                    {rec.competitors} competitors • {rec.complementary} complementary
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-3 text-xs text-gray-400 text-center">
            Click an area to view on map
          </div>
        </div>
      )}

      {/* Chat Interface */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-[1000] flex flex-col gap-2">

        {/* Chat History (Only show last few messages) */}
        {chatHistory.length > 0 && (
          <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-gray-200 p-4 max-h-60 overflow-y-auto mb-2">
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={`flex flex-col gap-2 mb-3 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`p-3 rounded-lg text-sm max-w-[80%] ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                  {msg.text}
                </div>
                
                {/* Database Query Results */}
                {msg.databaseResult && msg.databaseResult.success && (
                  <div className="bg-white border border-gray-300 rounded-lg p-3 max-w-[90%] text-xs">
                    <div className="flex items-center gap-2 mb-2 text-gray-600">
                      <Database size={14} />
                      <span className="font-semibold">Query Results ({msg.databaseResult.row_count} rows)</span>
                    </div>
                    
                    {/* Show SQL Query */}
                    <div className="bg-gray-50 p-2 rounded mb-2 font-mono text-xs text-gray-700 overflow-x-auto">
                      {msg.databaseResult.sql}
                    </div>
                    
                    {/* Show Data Table (first 10 rows) */}
                    {msg.databaseResult.results && msg.databaseResult.results.length > 0 && (
                      <div className="overflow-x-auto max-h-48 overflow-y-auto">
                        <table className="min-w-full text-xs border-collapse">
                          <thead className="bg-gray-100 sticky top-0">
                            <tr>
                              {Object.keys(msg.databaseResult.results[0]).map((key) => (
                                <th key={key} className="border border-gray-300 px-2 py-1 text-left font-semibold">
                                  {key}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {msg.databaseResult.results.slice(0, 10).map((row, rowIdx) => (
                              <tr key={rowIdx} className="hover:bg-gray-50">
                                {Object.values(row).map((val, colIdx) => (
                                  <td key={colIdx} className="border border-gray-300 px-2 py-1">
                                    {val !== null && val !== undefined ? String(val) : 'null'}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {msg.databaseResult.results.length > 10 && (
                          <div className="text-center text-gray-500 mt-2 text-xs">
                            Showing 10 of {msg.databaseResult.results.length} rows
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
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
            placeholder="Ask Atlas: 'Show me all restaurants in Delhi' or 'What areas exist?'"
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
