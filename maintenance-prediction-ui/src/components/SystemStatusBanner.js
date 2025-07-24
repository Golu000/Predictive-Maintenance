import React, { useState } from 'react';
import { Alert } from 'react-bootstrap';
import { RiAiGenerate2 } from "react-icons/ri";

// Accepts 'loadedDataFile' as a prop
function SystemStatusBanner({ loadedDataFile }) {
  const [showBanner, setShowBanner] = useState(true);

  if (!showBanner || !loadedDataFile) { // Also hide if loadedDataFile is not provided
    return null;
  }

  // Extract the name without the .csv extension
  const fileNameWithoutExtension = loadedDataFile.replace(/\.csv$/i, '');

  // Construct the dynamic message
  const bannerMessage = `Predictive AI Model Loaded For ${fileNameWithoutExtension}`;

  // Removed bannerHeight as content will determine height and it's less relevant for a footer

  return (
    <Alert
      variant="dark"
      onClose={() => setShowBanner(false)}
      dismissible
      className="text-center mb-0 rounded-0 banner"
      style={{
        backgroundColor: '#ff8d6b',
        color: '#000000',
        padding: '0.5rem 1rem', // Adjusted padding for better footer appearance
        fontSize: '0.875rem',
        fontWeight: '500',
        width: '100%',
        position: 'fixed', 
        bottom: 0,         
        left: 0,
        zIndex: 2000,
      }}
    >
      <RiAiGenerate2 className="me-2" /> {/* Display the icon */}
      {bannerMessage} {/* Display the dynamic message */}
    </Alert>
  );
}

export default SystemStatusBanner;