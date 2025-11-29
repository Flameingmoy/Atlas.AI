import React from 'react';
import { Layers, Map as MapIcon } from 'lucide-react';

const LayerControl = ({ activeLayers, toggleLayer }) => {
    return (
        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm p-4 rounded-xl shadow-lg border border-gray-200 z-[1000] w-64">
            <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <Layers size={16} />
                Map Layers
            </h3>

            <div className="space-y-2">
                <button
                    onClick={() => toggleLayer('competitors')}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${activeLayers.includes('competitors')
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'hover:bg-gray-50 text-gray-600 border border-transparent'
                        }`}
                >
                    <MapIcon size={16} />
                    Points of Interest
                </button>
            </div>
        </div>
    );
};

export default LayerControl;
