import React, { useState } from 'react';
import Map from './components/Map';
import SearchBar from './components/SearchBar';
import { sendChatMessage, getLocationRecommendations, analyzeAreaOpportunities, getAreaGeometry } from './services/api';
import { Send, X, Tag, Layers, Sparkles, TrendingUp, MessageSquare, MapPin, Building2, Lightbulb } from 'lucide-react';

function App() {
  const [activeLayers, setActiveLayers] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [mapCenter, setMapCenter] = useState(null);
  const [filteredPOIs, setFilteredPOIs] = useState(null);
  const [activeFilter, setActiveFilter] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [areaAnalysis, setAreaAnalysis] = useState(null);
  const [sidePanel, setSidePanel] = useState(null);

  const toggleLayer = (layer) => {
    setActiveLayers(prev =>
      prev.includes(layer)
        ? prev.filter(l => l !== layer)
        : [...prev, layer]
    );
  };

  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
    setMapCenter({ lat: location.lat, lon: location.lon, zoom: 15 });
    setFilteredPOIs(null);
    setActiveFilter(null);
  };

  const handleCategorySelect = (filter) => {
    setActiveFilter(filter);
    if (!filter) {
      setFilteredPOIs(null);
    }
  };

  const handlePOIsLoad = (data) => {
    if (data && data.pois) {
      setFilteredPOIs(data.pois);
      if (!activeLayers.includes('competitors')) {
        setActiveLayers(prev => [...prev, 'competitors']);
      }
    }
  };

  const handleClearFilter = () => {
    setFilteredPOIs(null);
    setActiveFilter(null);
  };

  const closeSidePanel = () => {
    setSidePanel(null);
    setRecommendations(null);
    setAreaAnalysis(null);
  };

  const isBusinessLocationQuery = (query) => {
    const lowerQuery = query.toLowerCase();
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
    if (locationPatterns.some(p => lowerQuery.includes(p))) return true;
    const locationIntent = ['location', 'area', 'place', 'where', 'recommend', 'best', 'top', 'ideal', 'suitable'];
    return businessWords.some(b => lowerQuery.includes(b)) && locationIntent.some(l => lowerQuery.includes(l));
  };

  const isAreaAnalysisQuery = (query) => {
    const lowerQuery = query.toLowerCase();
    const areaPatterns = [
      'what.*open.*in', 'what.*start.*in', 'business.*in',
      'recommend.*in', 'suggest.*in', 'opportunity.*in',
      'what kind.*in', 'what type.*in', 'gaps.*in'
    ];
    const hasAreaPattern = areaPatterns.some(p => new RegExp(p).test(lowerQuery));
    const areaKeywords = ['hauz khas', 'connaught', 'saket', 'khan market', 'defence colony', 
      'lajpat', 'karol bagh', 'rajouri', 'dwarka', 'rohini', 'pitampura', 'janakpuri',
      'vasant', 'greater kailash', 'south ex', 'nehru place', 'malviya'];
    const hasAreaName = areaKeywords.some(a => lowerQuery.includes(a));
    return hasAreaPattern || (hasAreaName && (lowerQuery.includes('business') || lowerQuery.includes('open') || lowerQuery.includes('recommend')));
  };

  const extractAreaName = (query) => {
    const lowerQuery = query.toLowerCase();
    const areas = [
      'hauz khas', 'connaught place', 'saket', 'khan market', 'defence colony',
      'lajpat nagar', 'karol bagh', 'rajouri garden', 'dwarka', 'rohini',
      'pitampura', 'janakpuri', 'vasant kunj', 'vasant vihar', 'greater kailash',
      'south extension', 'nehru place', 'malviya nagar', 'green park', 'safdarjung',
      'moti bagh', 'punjabi bagh', 'model town', 'civil lines', 'chandni chowk',
      'paharganj', 'rajender nagar', 'patel nagar', 'tilak nagar',
      'uttam nagar', 'vikaspuri', 'paschim vihar', 'shalimar bagh', 'prashant vihar',
      'laxmi nagar', 'preet vihar', 'mayur vihar', 'vasundhara enclave', 'ip extension'
    ];
    for (const area of areas) {
      if (lowerQuery.includes(area)) return area;
    }
    const match = query.match(/in\s+([A-Za-z\s]+?)(?:\?|$|,|\.)/i);
    if (match) return match[1].trim();
    return null;
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = chatInput;
    setChatInput("");
    setIsLoading(true);

    if (isBusinessLocationQuery(userMsg)) {
      try {
        const result = await getLocationRecommendations(userMsg, 1.0);
        if (result.success) {
          setRecommendations(result);
          setSidePanel({ type: 'recommendation', content: result });
          if (result.recommendations?.length > 0) {
            const top = result.recommendations[0];
            setMapCenter({ lat: top.centroid.lat, lon: top.centroid.lon, zoom: 12 });
          }
        } else {
          setSidePanel({ type: 'error', content: result.error || 'Failed to get recommendations' });
        }
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Error getting recommendations';
        setSidePanel({ type: 'error', content: errorMsg });
      }
    } else if (isAreaAnalysisQuery(userMsg)) {
      const areaName = extractAreaName(userMsg);
      if (areaName) {
        try {
          const result = await analyzeAreaOpportunities(areaName);
          if (result.success) {
            setAreaAnalysis(result);
            setSidePanel({ type: 'analysis', content: result });
            if (result.centroid) {
              setMapCenter({ lat: result.centroid.lat, lon: result.centroid.lon, zoom: 14 });
            }
            // Set recommendations with area info for polygon highlighting (no medal markers)
            setRecommendations({ 
              recommendations: [{ 
                area: result.area, 
                centroid: result.centroid,
                // These prevent medal marker from showing undefined
                composite_score: null,
                competitors: null,
                complementary: null,
                _isAreaAnalysis: true  // Flag to skip medal markers
              }] 
            });
          } else {
            setSidePanel({ type: 'error', content: result.error || 'Failed to analyze area' });
          }
        } catch (error) {
          setSidePanel({ type: 'error', content: 'Could not find area "' + areaName + '"' });
        }
      } else {
        setSidePanel({ type: 'error', content: 'Please specify an area name (e.g., "What business to open in Hauz Khas?")' });
      }
    } else {
      setSidePanel({ 
        type: 'help', 
        content: {
          query: userMsg,
          message: "I can help you with business location decisions! Try asking:",
          examples: [
            "Where should I open a cafe?",
            "Best location for a gym in Delhi",
            "What business should I open in Hauz Khas?",
            "Recommend business opportunities in Saket"
          ]
        }
      });
    }
    setIsLoading(false);
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
            activeFilter.type === 'category' ? 'bg-purple-600 text-white' : 'bg-orange-600 text-white'
          }`}>
            {activeFilter.type === 'category' ? <Tag size={16} /> : <Layers size={16} />}
            <span className="font-medium">{activeFilter.name}</span>
            <span className="opacity-80">({activeFilter.count?.toLocaleString()} places)</span>
            <button onClick={handleClearFilter} className="ml-2 hover:bg-white/20 rounded-full p-1">
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Simple Layer Toggle */}
      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm p-3 rounded-xl shadow-lg border border-gray-200 z-[1000]">
        <button
          onClick={() => toggleLayer('competitors')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
            activeLayers.includes('competitors')
              ? 'bg-blue-50 text-blue-700 border border-blue-200'
              : 'hover:bg-gray-50 text-gray-600 border border-transparent'
          }`}
        >
          <MapPin size={16} />
          Show POIs
        </button>
      </div>

      <Map 
        activeLayers={activeLayers} 
        selectedLocation={selectedLocation}
        mapCenter={mapCenter}
        filteredPOIs={filteredPOIs}
        recommendations={recommendations}
      />

      {/* Side Panel for Results */}
      {sidePanel && (
        <div className="absolute top-20 right-4 bottom-24 w-96 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200 z-[1000] flex flex-col overflow-hidden">
          {/* Panel Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="flex items-center gap-2">
              {sidePanel.type === 'recommendation' && <Sparkles className="text-amber-500" size={20} />}
              {sidePanel.type === 'analysis' && <Lightbulb className="text-green-500" size={20} />}
              {sidePanel.type === 'help' && <MessageSquare className="text-blue-500" size={20} />}
              {sidePanel.type === 'error' && <X className="text-red-500" size={20} />}
              <h3 className="font-bold text-gray-800">
                {sidePanel.type === 'recommendation' && 'Location Recommendations'}
                {sidePanel.type === 'analysis' && 'Business Opportunities'}
                {sidePanel.type === 'help' && 'How to Use'}
                {sidePanel.type === 'error' && 'Oops!'}
              </h3>
            </div>
            <button onClick={closeSidePanel} className="hover:bg-gray-200 rounded-full p-1">
              <X size={18} className="text-gray-500" />
            </button>
          </div>

          {/* Panel Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {/* Error */}
            {sidePanel.type === 'error' && (
              <div className="text-red-600 bg-red-50 p-4 rounded-lg">
                {sidePanel.content}
              </div>
            )}

            {/* Help */}
            {sidePanel.type === 'help' && (
              <div className="space-y-4">
                <p className="text-gray-600">{sidePanel.content.message}</p>
                <div className="space-y-2">
                  {sidePanel.content.examples.map((ex, idx) => (
                    <div 
                      key={idx}
                      onClick={() => setChatInput(ex)}
                      className="p-3 bg-blue-50 rounded-lg text-blue-700 cursor-pointer hover:bg-blue-100 transition-colors"
                    >
                      "{ex}"
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Location Recommendations */}
            {sidePanel.type === 'recommendation' && sidePanel.content && (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Building2 size={14} />
                  <span>{sidePanel.content.business_type} • {sidePanel.content.super_category}</span>
                </div>

                <div className="space-y-3">
                  {sidePanel.content.recommendations?.slice(0, 3).map((rec, idx) => (
                    <div 
                      key={rec.area}
                      className={`p-4 rounded-xl cursor-pointer transition-all ${
                        idx === 0 ? 'bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300' :
                        idx === 1 ? 'bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200' :
                        'bg-gray-50 border border-gray-100'
                      }`}
                      onClick={() => setMapCenter({ lat: rec.centroid.lat, lon: rec.centroid.lon, zoom: 14 })}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xl">{['🥇', '🥈', '🥉'][idx]}</span>
                        <span className="font-bold text-gray-800">{rec.area}</span>
                        <span className="ml-auto text-lg font-bold text-blue-600">{rec.composite_score}</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="bg-white/50 rounded p-2 text-center">
                          <div className="text-gray-500">Base</div>
                          <div className="font-semibold">{rec.area_score}</div>
                        </div>
                        <div className="bg-white/50 rounded p-2 text-center">
                          <div className="text-gray-500">Opportunity</div>
                          <div className="font-semibold">{rec.opportunity_score}</div>
                        </div>
                        <div className="bg-white/50 rounded p-2 text-center">
                          <div className="text-gray-500">Ecosystem</div>
                          <div className="font-semibold">{rec.ecosystem_score}</div>
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-gray-500">
                        {rec.competitors} competitors • {rec.complementary} complementary
                      </div>
                    </div>
                  ))}
                </div>

                {sidePanel.content.complementary_categories && (
                  <div className="mt-4 p-3 bg-green-50 rounded-lg">
                    <div className="text-xs font-semibold text-green-700 mb-1">Complementary Categories</div>
                    <div className="flex flex-wrap gap-1">
                      {sidePanel.content.complementary_categories.map(cat => (
                        <span key={cat} className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">{cat}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Area Analysis */}
            {sidePanel.type === 'analysis' && sidePanel.content && (
              <div className="space-y-4">
                <div className="text-center p-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-800">{sidePanel.content.area}</div>
                  <div className="text-sm text-gray-500">{sidePanel.content.total_pois} total businesses</div>
                </div>

                {/* Dominant Categories */}
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-2">Current Business Landscape</div>
                  <div className="flex flex-wrap gap-2">
                    {sidePanel.content.dominant_categories?.map(cat => (
                      <div key={cat.category} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                        {cat.category}: {cat.count}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendations */}
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                    <Lightbulb size={16} className="text-amber-500" />
                    Recommended Business Categories
                  </div>
                  <div className="space-y-3">
                    {sidePanel.content.recommendations?.map((rec, idx) => (
                      <div key={rec.category} className={`p-4 rounded-xl border ${
                        rec.type === 'gap' ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200' : 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200'
                      }`}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-gray-800">{idx + 1}. {rec.category}</span>
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                              rec.type === 'gap' ? 'bg-blue-200 text-blue-700' : 'bg-green-200 text-green-700'
                            }`}>
                              {rec.type === 'gap' ? 'Market Gap' : 'Complementary'}
                            </span>
                          </div>
                          <span className={`text-lg font-bold ${
                            rec.type === 'gap' ? 'text-blue-600' : 'text-green-600'
                          }`}>{Math.round(rec.score)}</span>
                        </div>
                        
                        {/* Score breakdown */}
                        <div className="grid grid-cols-3 gap-2 text-xs mb-3">
                          <div className={`rounded p-2 text-center ${
                            rec.type === 'gap' ? 'bg-blue-100/50' : 'bg-green-100/50'
                          }`}>
                            <div className="text-gray-500">Demand</div>
                            <div className="font-semibold">{rec.type === 'gap' ? 'High' : 'Medium'}</div>
                          </div>
                          <div className={`rounded p-2 text-center ${
                            rec.type === 'gap' ? 'bg-blue-100/50' : 'bg-green-100/50'
                          }`}>
                            <div className="text-gray-500">Supply</div>
                            <div className="font-semibold">{rec.type === 'gap' ? 'Low' : 'Growing'}</div>
                          </div>
                          <div className={`rounded p-2 text-center ${
                            rec.type === 'gap' ? 'bg-blue-100/50' : 'bg-green-100/50'
                          }`}>
                            <div className="text-gray-500">Fit</div>
                            <div className="font-semibold">{Math.round(rec.score) > 70 ? 'Excellent' : Math.round(rec.score) > 40 ? 'Good' : 'Fair'}</div>
                          </div>
                        </div>
                        
                        <div className="text-xs text-gray-600 mb-2">{rec.reason}</div>
                        <div className="flex flex-wrap gap-1">
                          {rec.examples?.map(ex => (
                            <span key={ex} className="px-2 py-1 bg-white/70 rounded-full text-xs text-gray-700 border border-gray-200">{ex}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Chat Input */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-[1000]">
        <form onSubmit={handleChatSubmit} className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200 p-2 flex gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask: 'Where to open a cafe?' or 'What business in Hauz Khas?'"
            className="flex-1 bg-transparent border-none outline-none px-4 py-3 text-gray-800 placeholder-gray-400"
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
