import React, { useState } from 'react';
import Map from './components/Map';
import SearchBar from './components/SearchBar';
import { sendChatMessage, getLocationRecommendations, analyzeAreaOpportunities, getAreaGeometry } from './services/api';
import { Send, X, Tag, Layers, Sparkles, TrendingUp, MessageSquare, MapPin, Building2, Lightbulb, History, ChevronRight, Search, Globe, ExternalLink, Check } from 'lucide-react';

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
  const [activeTab, setActiveTab] = useState('analysis'); // 'analysis' or 'recommendation'
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]); // Array of { query, type, data, timestamp }
  const [showHistory, setShowHistory] = useState(false);
  const [deepResearchEnabled, setDeepResearchEnabled] = useState(false); // Toggle for Tavily research
  const [isResearching, setIsResearching] = useState(false); // Track deep research in progress
  const [researchComplete, setResearchComplete] = useState(false); // Track when research is done

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
    setIsPanelOpen(false);
  };

  const togglePanel = () => {
    setIsPanelOpen(prev => !prev);
  };

  const loadFromHistory = (historyItem) => {
    setSidePanel(historyItem.panel);
    setActiveTab(historyItem.activeTab);
    if (historyItem.panel.locationData) {
      setRecommendations(historyItem.panel.locationData);
    }
    if (historyItem.panel.analysisData) {
      setAreaAnalysis(historyItem.panel.analysisData);
      // Set recommendations for map highlighting
      setRecommendations({ 
        recommendations: [{ 
          area: historyItem.panel.analysisData.area, 
          centroid: historyItem.panel.analysisData.centroid,
          location_source: historyItem.panel.analysisData.location_source,
          radius_km: historyItem.panel.analysisData.radius_km,
          composite_score: null,
          competitors: null,
          complementary: null,
          _isAreaAnalysis: true
        }] 
      });
    }
    setIsPanelOpen(true);
    setShowHistory(false);
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
    setResearchComplete(false);
    
    // Set researching state if deep research is enabled
    if (deepResearchEnabled) {
      setIsResearching(true);
    }

    // Determine query type and extract info
    const isLocationQuery = isBusinessLocationQuery(userMsg);
    const isAreaQuery = isAreaAnalysisQuery(userMsg);
    const areaName = extractAreaName(userMsg);

    let locationResult = null;
    let analysisResult = null;

    if (isLocationQuery) {
      // User asked "Where to open X?" - get location recommendations
      try {
        locationResult = await getLocationRecommendations(userMsg, 1.0, deepResearchEnabled);
        if (locationResult.success) {
          setRecommendations(locationResult);
          setActiveTab('recommendation');
          if (locationResult.recommendations?.length > 0) {
            const top = locationResult.recommendations[0];
            setMapCenter({ lat: top.centroid.lat, lon: top.centroid.lon, zoom: 12 });
          }
        }
      } catch (error) {
        const errorMsg = error.response?.data?.detail || error.message || 'Error getting recommendations';
        setSidePanel({ type: 'error', content: errorMsg });
        setIsLoading(false);
        return;
      }
      
      // Also show side panel with results
      const newPanel = { 
        type: 'unified', 
        locationData: locationResult?.success ? locationResult : null,
        analysisData: null 
      };
      setSidePanel(newPanel);
      
      // Save to history
      if (locationResult?.success) {
        setChatHistory(prev => [{
          query: userMsg,
          type: 'recommendation',
          panel: newPanel,
          activeTab: 'recommendation',
          timestamp: new Date()
        }, ...prev].slice(0, 10)); // Keep last 10
      }
      
    } else if (isAreaQuery && areaName) {
      // User asked "What business in X?" - get area analysis
      try {
        analysisResult = await analyzeAreaOpportunities(areaName, deepResearchEnabled);
        if (analysisResult.success) {
          setAreaAnalysis(analysisResult);
          setActiveTab('analysis');
          if (analysisResult.centroid) {
            setMapCenter({ lat: analysisResult.centroid.lat, lon: analysisResult.centroid.lon, zoom: 14 });
          }
          // Set recommendations with area info for polygon/circle highlighting
          setRecommendations({ 
            recommendations: [{ 
              area: analysisResult.area, 
              centroid: analysisResult.centroid,
              location_source: analysisResult.location_source,
              radius_km: analysisResult.radius_km,
              composite_score: null,
              competitors: null,
              complementary: null,
              _isAreaAnalysis: true
            }] 
          });
        }
      } catch (error) {
        setSidePanel({ type: 'error', content: 'Could not find area "' + areaName + '"' });
        setIsLoading(false);
        return;
      }
      
      const newPanel = { 
        type: 'unified', 
        locationData: null,
        analysisData: analysisResult?.success ? analysisResult : null 
      };
      setSidePanel(newPanel);
      
      // Save to history
      if (analysisResult?.success) {
        setChatHistory(prev => [{
          query: userMsg,
          type: 'analysis',
          panel: newPanel,
          activeTab: 'analysis',
          timestamp: new Date()
        }, ...prev].slice(0, 10)); // Keep last 10
      }
      
    } else if (!isLocationQuery && !isAreaQuery) {
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
    } else {
      setSidePanel({ type: 'error', content: 'Please specify an area name (e.g., "What business to open in Hauz Khas?")' });
    }
    
    setIsPanelOpen(true);
    setIsLoading(false);
    setIsResearching(false);
    
    // Check if research was completed
    const hasResearch = locationResult?.research_enabled || analysisResult?.research_enabled;
    if (deepResearchEnabled && hasResearch) {
      setResearchComplete(true);
      // Auto-hide the "complete" badge after 5 seconds
      setTimeout(() => setResearchComplete(false), 5000);
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

      {/* Panel Toggle Button (always visible in top right) */}
      {!isPanelOpen && (
        <button
          onClick={togglePanel}
          className="absolute top-4 right-4 z-[1000] bg-white/95 backdrop-blur-md p-3 rounded-full shadow-lg border border-gray-200 hover:bg-gray-50 hover:scale-105 transition-all"
          title="Open Insights Panel"
        >
          <MessageSquare size={20} className="text-blue-600" />
          {chatHistory.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-medium">
              {chatHistory.length}
            </span>
          )}
        </button>
      )}

      {/* Side Panel for Results */}
      {isPanelOpen && (
        <div className="absolute top-4 right-4 bottom-24 w-96 bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200 z-[1000] flex flex-col overflow-hidden">
          {/* Panel Header - Always visible */}
          <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="flex items-center gap-2">
              <MessageSquare className="text-blue-600" size={18} />
              <h3 className="font-semibold text-gray-800">Insights Panel</h3>
            </div>
            <div className="flex items-center gap-1">
              {chatHistory.length > 0 && (
                <button 
                  onClick={() => setShowHistory(!showHistory)} 
                  className={`relative p-1.5 rounded-full transition-colors ${showHistory ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-200 text-gray-500'}`}
                  title="Chat History"
                >
                  <History size={16} />
                  {!showHistory && (
                    <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-medium">
                      {chatHistory.length}
                    </span>
                  )}
                </button>
              )}
              <button onClick={closeSidePanel} className="hover:bg-gray-200 rounded-full p-1.5">
                <X size={16} className="text-gray-500" />
              </button>
            </div>
          </div>

          {/* History View */}
          {showHistory ? (
            <div className="flex-1 overflow-y-auto p-4">
              {chatHistory.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <History size={32} className="mx-auto mb-3 opacity-50" />
                  <p className="text-sm">No history yet.</p>
                  <p className="text-xs mt-1">Your queries will appear here.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {chatHistory.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => loadFromHistory(item)}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 hover:border-gray-300 transition-all group"
                    >
                      <div className="flex items-start gap-2">
                        {item.type === 'recommendation' ? (
                          <Sparkles size={16} className="text-amber-500 mt-0.5 flex-shrink-0" />
                        ) : (
                          <Lightbulb size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-800 font-medium truncate">{item.query}</p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {item.type === 'recommendation' ? 'Location Search' : 'Area Analysis'}
                            {' • '}
                            {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                        <ChevronRight size={16} className="text-gray-400 group-hover:text-gray-600 flex-shrink-0" />
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : sidePanel && sidePanel.type === 'unified' ? (
            <>
              {/* Tabs for unified panel */}
              <div className="border-b border-gray-200 px-4 py-2 flex gap-1">
                <button
                  onClick={() => setActiveTab('analysis')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    activeTab === 'analysis' 
                      ? 'bg-green-100 text-green-700 shadow-sm' 
                      : 'text-gray-500 hover:bg-gray-100'
                  }`}
                >
                  <Lightbulb size={14} />
                  Opportunities
                </button>
                <button
                  onClick={() => setActiveTab('recommendation')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    activeTab === 'recommendation' 
                      ? 'bg-amber-100 text-amber-700 shadow-sm' 
                      : 'text-gray-500 hover:bg-gray-100'
                  }`}
                >
                  <Sparkles size={14} />
                  Locations
                </button>
              </div>
              
              {/* Deep Research Status Indicators */}
              {isResearching && (
                <div className="mx-4 mt-3 p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-200 animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Globe className="text-purple-500 animate-spin" size={20} />
                      <span className="absolute -top-1 -right-1 w-2 h-2 bg-purple-500 rounded-full animate-ping" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-purple-700">Deep Research in Progress...</div>
                      <div className="text-xs text-purple-500">Searching the web with Tavily AI for real-time insights</div>
                    </div>
                  </div>
                </div>
              )}
              
              {researchComplete && !isResearching && (
                <div className="mx-4 mt-3 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200">
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                      <Check className="text-white" size={14} />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-green-700">Research Complete!</div>
                      <div className="text-xs text-green-500">Real-time insights added to recommendations below</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Panel Content */}
              <div className="flex-1 overflow-y-auto p-4">
                {/* Unified Panel - Location Recommendations Tab */}
                {activeTab === 'recommendation' && (
                  <div className="space-y-4">
                    {sidePanel.locationData ? (
                      <>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <Building2 size={14} />
                          <span>{sidePanel.locationData.business_type} • {sidePanel.locationData.super_category}</span>
                        </div>

                        <div className="space-y-3">
                          {sidePanel.locationData.recommendations?.slice(0, 3).map((rec, idx) => (
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
                              
                              {/* Deep Research Results */}
                              {rec.research && (
                                <div className="mt-3 pt-3 border-t border-gray-200/50 space-y-2">
                                  <div className="flex items-center gap-1 text-xs text-purple-600 font-medium">
                                    <Search size={12} />
                                    <span>Deep Research Insights</span>
                                  </div>
                                  
                                  {rec.research.market_insights && (
                                    <div className="text-xs text-purple-700 bg-purple-50 rounded px-2 py-1.5 font-medium">
                                      💡 {rec.research.market_insights}
                                    </div>
                                  )}
                                  
                                  {rec.research.pros?.length > 0 && (
                                    <div className="space-y-1">
                                      <div className="text-xs font-medium text-green-700">✓ Pros</div>
                                      {rec.research.pros.slice(0, 2).map((pro, i) => (
                                        <div key={i} className="text-xs text-green-600 bg-green-50 rounded px-2 py-1">{pro}</div>
                                      ))}
                                    </div>
                                  )}
                                  
                                  {rec.research.cons?.length > 0 && (
                                    <div className="space-y-1">
                                      <div className="text-xs font-medium text-red-700">✗ Cons</div>
                                      {rec.research.cons.slice(0, 2).map((con, i) => (
                                        <div key={i} className="text-xs text-red-600 bg-red-50 rounded px-2 py-1">{con}</div>
                                      ))}
                                    </div>
                                  )}
                                  
                                  {rec.research.sources?.length > 0 && (
                                    <div className="text-xs text-gray-400 mt-1">
                                      {rec.research.sources.length} source{rec.research.sources.length > 1 ? 's' : ''} cited
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>

                        {sidePanel.locationData.complementary_categories && (
                          <div className="mt-4 p-3 bg-green-50 rounded-lg">
                            <div className="text-xs font-semibold text-green-700 mb-1">Complementary Categories</div>
                            <div className="flex flex-wrap gap-1">
                              {sidePanel.locationData.complementary_categories.map(cat => (
                                <span key={cat} className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">{cat}</span>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <Sparkles size={32} className="mx-auto mb-3 opacity-50" />
                        <p className="text-sm">No location data available.</p>
                        <p className="text-xs mt-1">Try asking "Where should I open a cafe?"</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Unified Panel - Business Opportunities Tab */}
                {activeTab === 'analysis' && (
                  <div className="space-y-4">
                    {sidePanel.analysisData ? (
                      <>
                        <div className="text-center p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-100">
                          <div className="text-2xl font-bold text-gray-800">{sidePanel.analysisData.area}</div>
                          <div className="text-sm text-gray-500 mt-1">{sidePanel.analysisData.total_pois?.toLocaleString()} total businesses</div>
                          
                          {/* Trend Indicator */}
                          {sidePanel.analysisData.trend_indicator && (
                            <div className="mt-3">
                              <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold ${
                                sidePanel.analysisData.trend_indicator.indicator === 'emerging' 
                                  ? 'bg-green-100 text-green-700 border border-green-200' 
                                  : sidePanel.analysisData.trend_indicator.indicator === 'growing'
                                    ? 'bg-amber-100 text-amber-700 border border-amber-200'
                                    : 'bg-red-100 text-red-700 border border-red-200'
                              }`}>
                                <span>{sidePanel.analysisData.trend_indicator.emoji}</span>
                                <span>{sidePanel.analysisData.trend_indicator.label}</span>
                              </span>
                              <p className="text-xs text-gray-500 mt-2 px-2">{sidePanel.analysisData.trend_indicator.reason}</p>
                            </div>
                          )}
                        </div>

                        {/* Dominant Categories */}
                        <div>
                          <div className="text-sm font-semibold text-gray-700 mb-2">Current Business Landscape</div>
                          <div className="flex flex-wrap gap-2">
                            {sidePanel.analysisData.dominant_categories?.map(cat => (
                              <div key={cat.category} className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                                {cat.category}: {cat.count}
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Recommendations */}
                        <div>
                          <div className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                            <Lightbulb size={16} className="text-amber-500" />
                            Recommended Business Categories
                          </div>
                          <div className="space-y-3">
                            {sidePanel.analysisData.recommendations?.map((rec, idx) => (
                              <div key={rec.category} className={`p-4 rounded-xl border ${
                                rec.type === 'gap' 
                                  ? 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200' 
                                  : 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200'
                              }`}>
                                {/* Header Row */}
                                <div className="flex items-start justify-between gap-3 mb-2">
                                  <span className="font-bold text-gray-800 text-base">{idx + 1}. {rec.category}</span>
                                  <span className={`text-xl font-bold tabular-nums ${
                                    rec.type === 'gap' ? 'text-blue-600' : 'text-green-600'
                                  }`}>{Math.round(rec.score)}</span>
                                </div>
                                
                                {/* Type Tag */}
                                <div className="mb-3">
                                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                                    rec.type === 'gap' ? 'bg-blue-200 text-blue-700' : 'bg-green-200 text-green-700'
                                  }`}>
                                    {rec.type === 'gap' ? 'Market Gap' : 'Complementary'}
                                  </span>
                                </div>
                                
                                {/* Score breakdown */}
                                <div className="grid grid-cols-3 gap-2 mb-3">
                                  <div className={`rounded-lg p-2 text-center ${
                                    rec.type === 'gap' ? 'bg-blue-100/60' : 'bg-green-100/60'
                                  }`}>
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wide">Base</div>
                                    <div className="text-sm font-bold text-gray-800 mt-0.5">{rec.base_score ?? '—'}</div>
                                  </div>
                                  <div className={`rounded-lg p-2 text-center ${
                                    rec.type === 'gap' ? 'bg-blue-100/60' : 'bg-green-100/60'
                                  }`}>
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wide">Opportunity</div>
                                    <div className="text-sm font-bold text-gray-800 mt-0.5">{rec.opportunity_score ?? '—'}</div>
                                  </div>
                                  <div className={`rounded-lg p-2 text-center ${
                                    rec.type === 'gap' ? 'bg-blue-100/60' : 'bg-green-100/60'
                                  }`}>
                                    <div className="text-[10px] text-gray-500 uppercase tracking-wide">Ecosystem</div>
                                    <div className="text-sm font-bold text-gray-800 mt-0.5">{rec.ecosystem_score ?? '—'}</div>
                                  </div>
                                </div>
                                
                                {/* Competition stats */}
                                <div className="text-xs text-gray-500 mb-3">
                                  {rec.competitors} competitors • {rec.complementary} complementary
                                </div>
                                
                                {/* Pros */}
                                <div className="mb-2">
                                  <div className="flex items-center gap-1.5 mb-1">
                                    <span className="text-green-600 text-sm">✓</span>
                                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Pros</span>
                                  </div>
                                  <p className="text-xs text-gray-600 leading-relaxed pl-5">{rec.reason}</p>
                                </div>
                                
                                {/* Cons */}
                                {rec.cons && rec.cons.length > 0 && (
                                  <div className="mb-3">
                                    <div className="flex items-center gap-1.5 mb-1">
                                      <span className="text-red-500 text-sm">✗</span>
                                      <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Cons</span>
                                    </div>
                                    <ul className="text-xs text-gray-600 leading-relaxed pl-5 space-y-0.5">
                                      {rec.cons.map((con, i) => (
                                        <li key={i}>• {con}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                
                                {/* Examples */}
                                <div className="flex flex-wrap gap-1.5">
                                  {rec.examples?.map(ex => (
                                    <span key={ex} className="px-2.5 py-1 bg-white/80 rounded-full text-xs text-gray-700 border border-gray-200 font-medium">{ex}</span>
                                  ))}
                                </div>
                                
                                {/* Deep Research Results */}
                                {rec.research && (
                                  <div className="mt-3 pt-3 border-t border-gray-200/50 space-y-2">
                                    <div className="flex items-center gap-1 text-xs text-purple-600 font-medium">
                                      <Search size={12} />
                                      <span>Deep Research Insights</span>
                                    </div>
                                    
                                    {rec.research.market_potential && (
                                      <div className="text-xs text-purple-700 bg-purple-50 rounded px-2 py-1.5 font-medium">
                                        📊 {rec.research.market_potential}
                                      </div>
                                    )}
                                    
                                    {rec.research.pros?.length > 0 && (
                                      <div className="space-y-1">
                                        <div className="text-xs font-medium text-green-700">✓ Real-time Pros</div>
                                        {rec.research.pros.slice(0, 2).map((pro, i) => (
                                          <div key={i} className="text-xs text-green-600 bg-green-50 rounded px-2 py-1">{pro}</div>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {rec.research.cons?.length > 0 && (
                                      <div className="space-y-1">
                                        <div className="text-xs font-medium text-red-700">✗ Real-time Cons</div>
                                        {rec.research.cons.slice(0, 2).map((con, i) => (
                                          <div key={i} className="text-xs text-red-600 bg-red-50 rounded px-2 py-1">{con}</div>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {rec.research.sources?.length > 0 && (
                                      <div className="text-xs text-gray-400 mt-1">
                                        {rec.research.sources.length} source{rec.research.sources.length > 1 ? 's' : ''} cited
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <Lightbulb size={32} className="mx-auto mb-3 opacity-50" />
                        <p className="text-sm">No area analysis available.</p>
                        <p className="text-xs mt-1">Try asking "What business in Hauz Khas?"</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : sidePanel && (sidePanel.type === 'help' || sidePanel.type === 'error') ? (
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
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500 p-4">
              <MessageSquare size={32} className="mb-3 opacity-50" />
              <p className="text-sm text-center">No results yet.</p>
              <p className="text-xs mt-1 text-center">Ask a question below to get started!</p>
            </div>
          )}
        </div>
      )}

      {/* Chat Input */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-[1000]">
        <form onSubmit={handleChatSubmit} className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-gray-200 p-2">
          <div className="flex gap-2">
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
          </div>
          {/* Deep Research Toggle */}
          <div className="flex items-center justify-between px-4 pt-2 border-t border-gray-100 mt-2">
            <button
              type="button"
              onClick={() => setDeepResearchEnabled(!deepResearchEnabled)}
              disabled={isResearching}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                deepResearchEnabled 
                  ? 'bg-purple-100 text-purple-700 border border-purple-200' 
                  : 'bg-gray-100 text-gray-500 border border-gray-200 hover:bg-gray-200'
              } ${isResearching ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <Globe size={14} className={isResearching ? 'animate-spin' : ''} />
              Deep Research
              {deepResearchEnabled && !isResearching && <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-pulse" />}
            </button>
            {isResearching ? (
              <span className="text-xs text-purple-600 font-medium animate-pulse">
                🔍 Researching with Tavily AI...
              </span>
            ) : deepResearchEnabled ? (
              <span className="text-xs text-gray-400">Powered by Tavily AI • May take longer</span>
            ) : null}
          </div>
        </form>
      </div>
    </div>
  );
}

export default App;
